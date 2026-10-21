"""Active replay scheduling and consumer progress during durable cache refresh."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import sys
import threading
from types import SimpleNamespace

import pytest
import engine.transport as module
from engine.core import load_match
from engine.repository import Repository
from engine.transport import EventHubTransport


def session(sid, clock=1000, running=False):
    return {'id': sid, 'generation': 1, 'match_id': 'match-001', 'clock_ms': clock,
            'running': running, 'speed': 1, 'updated_at': 0, 'duration_ms': 60000}


class Batch:
    def __init__(self):
        self.events = []
    def add(self, event):
        self.events.append(event)


class Producer:
    def __init__(self):
        self.batches = []
        self.fail = False
    def create_batch(self, **kwargs):
        return Batch()
    def send_batch(self, batch):
        if self.fail:
            self.fail = False
            raise OSError('send_failed')
        self.batches.append(batch)


@pytest.fixture
def transport(tmp_path, monkeypatch):
    class EventData:
        def __init__(self, body):
            self.body = body
    monkeypatch.setitem(sys.modules, 'azure.eventhub', SimpleNamespace(EventData=EventData))
    repo = Repository(tmp_path / 'transport.db')
    return EventHubTransport(repo, producer=Producer(), consumer=object())


def test_active_session_publishes_before_idle_history_and_idle_skips_cursor_reads(transport, monkeypatch):
    t = transport
    t.repo.save_session(session('paused'))
    t.repo.save_session(session('finished', clock=60000, running=True))
    t.repo.save_session(session('active', running=True))
    monkeypatch.setattr(module.time, 'time', lambda: 0)
    calls = []
    original = t.publish_session
    def publish(s, cutoff=None):
        calls.append(s['id'])
        return original(s, cutoff)
    monkeypatch.setattr(t, 'publish_session', publish)
    t.publish_cycle()
    assert calls == ['active', 'paused', 'finished']
    calls.clear()
    t.publish_cycle()
    assert calls == ['active']


def test_paused_forward_seek_flushes_and_failed_send_retries(transport, monkeypatch):
    t = transport
    first, second = deepcopy(load_match('match-001')[1][:2])
    first['available_at_ms'] = first['timeline_ms'] = 1000
    second['available_at_ms'] = second['timeline_ms'] = 2000
    monkeypatch.setattr(module, 'load_match', lambda _: ({}, [first, second]))
    s = session('paused')
    t.repo.save_session(s)
    t.producer.fail = True
    with pytest.raises(OSError):
        t.publish_cycle()
    assert 'paused' not in t.publication_signatures
    assert t.repo.transport_cursor('paused') == -1
    t.publish_cycle()
    assert t.repo.transport_cursor('paused') == 0
    t.publish_cycle()
    assert len(t.producer.batches) == 1
    s['clock_ms'] = 2000
    t.repo.save_session(s)
    t.publish_cycle()
    assert t.repo.transport_cursor('paused') == 1
    assert len(t.producer.batches) == 2


def test_one_failed_session_does_not_starve_later_active_session(transport, monkeypatch):
    t = transport
    t.repo.save_session(session('active-a', running=True))
    t.repo.save_session(session('active-b', running=True))
    monkeypatch.setattr(module.time, 'time', lambda: 0)
    calls = []
    def publish(s, cutoff=None):
        calls.append(s['id'])
        if s['id'] == 'active-a':
            raise OSError('retry')
    monkeypatch.setattr(t, 'publish_session', publish)
    with pytest.raises(OSError):
        t.publish_cycle()
    assert calls == ['active-a', 'active-b']


def test_scheduling_caches_are_bounded(transport, monkeypatch):
    t = transport
    t.session_cache_limit = 2
    t.match_cache_limit = 2
    monkeypatch.setattr(module, 'load_match', lambda _: ({}, []))
    for number in range(5):
        s = session(str(number))
        s['match_id'] = 'match-' + str(number)
        t.repo.save_session(s)
    t.publish_cycle()
    assert len(t.publication_signatures) == 2
    assert len(t.ordered_matches) == 2


def test_durable_refresh_does_not_block_consumer_or_discard_concurrent_arrival(transport, monkeypatch):
    t = transport
    s = session('live')
    t.repo.save_session(s)
    first, second = load_match('match-001')[1][:2]
    t.repo.append_observation('live', first)
    read_started, release_read = threading.Event(), threading.Event()
    original = t.repo.read_observations
    def blocked_read(sid):
        snapshot = original(sid)
        read_started.set()
        assert release_read.wait(3)
        return snapshot
    monkeypatch.setattr(t.repo, 'read_observations', blocked_read)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reading = pool.submit(t.messages, s, 60000)
        assert read_started.wait(3)
        envelope = {'session_id': 'live', 'generation': 1, 'match_id': 'match-001',
                    'observation': second}
        accepted = pool.submit(t.accept, envelope)
        try:
            assert accepted.result(timeout=1) is True
        finally:
            release_read.set()
        messages = reading.result(timeout=3)
    assert {m['message_id'] for m in messages} == {first['message_id'], second['message_id']}
    early = t.messages(s, 0)
    assert all(m['timeline_ms'] <= 0 and m['available_at_ms'] <= 0 for m in early)
    assert len(early) < len(messages)  # Retain cutoff on the merged cache.


def test_refresh_failure_is_retried_and_does_not_mark_cache_fresh(transport, monkeypatch):
    t = transport
    original = t.repo.read_observations
    calls = []
    def flaky(sid):
        calls.append(sid)
        if len(calls) == 1:
            raise OSError('storage_unavailable')
        return original(sid)
    monkeypatch.setattr(t.repo, 'read_observations', flaky)
    with pytest.raises(OSError):
        t.messages(session('s'), 1000)
    assert 's' not in t.cache_refreshing
    assert 's' not in t.cache_refreshed_at
    assert t.messages(session('s'), 1000) == []
    assert calls == ['s', 's']
