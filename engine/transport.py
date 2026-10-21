"""Replay-clock publisher and durable Event Hubs consumer.

Delivery is at least once: persist immutable observations before checkpointing.
A crash after persistence replays safely; a crash after send retries safely.
Future observations remain inaccessible through the timeline cutoff on every read.
"""
from __future__ import annotations
import json
import logging
import os
import threading
import time
from collections import deque, OrderedDict
from engine.core import available, digest, load_match
from engine.contracts import OBSERVATION
from engine.cloud_repository import RepositoryConflict

LOG = logging.getLogger(__name__)


def replay_clock(session):
    elapsed = max(0, time.time() - session['updated_at']) * session['speed'] * 1000 if session['running'] else 0
    return min(60000, int(session['clock_ms'] + elapsed))


class EventHubTransport:
    def __init__(self, repository, credential=None, producer=None, consumer=None):
        self.repo = repository
        self.stop = threading.Event()
        self.lock = threading.RLock()
        self.cache = {}
        self.cache_refreshed_at = {}
        self.cache_refresh_seconds = 2
        self.session_metadata = OrderedDict()
        self.session_cache_limit = 1024
        self.publisher_error = None
        self.receive_error = None
        self.partition_errors = {}
        self.received = 0
        self.sent = 0
        self.threads = []
        self._checkpoint_counts = {}
        self._pending_events = {}
        if producer is None or consumer is None:
            from azure.identity import DefaultAzureCredential
            from azure.eventhub import EventHubProducerClient, EventHubConsumerClient, TransportType
            from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore
            credential = credential or DefaultAzureCredential(managed_identity_client_id=os.getenv('AZURE_CLIENT_ID'))
            host = os.environ['WHY_NOW_EVENTHUB_NAMESPACE']
            hub = os.getenv('WHY_NOW_EVENTHUB_NAME', 'match-observations')
            # WebSockets uses outbound 443 and works in restrictive hosting networks.
            options = {'fully_qualified_namespace': host, 'eventhub_name': hub,
                       'credential': credential, 'transport_type': TransportType.AmqpOverWebsocket}
            producer = producer or EventHubProducerClient(**options)
            checkpoint = BlobCheckpointStore(blob_account_url=os.environ['WHY_NOW_CHECKPOINT_ACCOUNT_URL'],
                container_name=os.getenv('WHY_NOW_CHECKPOINT_CONTAINER', 'eventhub-checkpoints'), credential=credential)
            consumer = consumer or EventHubConsumerClient(consumer_group=os.getenv('WHY_NOW_EVENTHUB_CONSUMER_GROUP', 'whynow-state'), checkpoint_store=checkpoint, load_balancing_interval=5, partition_ownership_expiration_interval=20, **options)
        self.producer = producer
        self.consumer = consumer

    def messages(self, session, cutoff):
        sid = session['id']
        with self.lock:
            refreshed = self.cache_refreshed_at.get(sid)
            if refreshed is None or time.monotonic() - refreshed >= self.cache_refresh_seconds:
                # During a rolling deployment another consumer can persist and
                # checkpoint messages after this process first populates its cache.
                # Reconcile durable rows periodically so those arrivals are visible
                # even when Event Hubs never redelivers them to this process.
                durable = self.repo.read_observations(sid)
                current = self.cache.setdefault(sid, {})
                for message in durable:
                    old = current.get(message['message_id'])
                    if old and digest(old) != digest(message):
                        raise RepositoryConflict('observation_id_reused')
                    current[message['message_id']] = message
                self.cache_refreshed_at[sid] = time.monotonic()
            # The durable cache may include arrivals beyond the current replay clock.
            # Enforce both availability and occurrence at every boundary, also after pause/restart.
            return available(list(self.cache[sid].values()), cutoff)

    def _session(self, sid):
        with self.lock:
            if sid in self.session_metadata:
                self.session_metadata.move_to_end(sid)
                return self.session_metadata[sid]
        session = self.repo.get_session(sid)
        if not session:
            raise ValueError('unknown_transport_session')
        # Session identity, generation and match are immutable. Reset creates a
        # fresh ID, so clock/control changes do not invalidate this metadata.
        metadata = {key: session[key] for key in ('id', 'generation', 'match_id')}
        with self.lock:
            self.session_metadata[sid] = metadata
            self.session_metadata.move_to_end(sid)
            while len(self.session_metadata) > self.session_cache_limit:
                self.session_metadata.popitem(last=False)
        return metadata

    def accept(self, envelope):
        return bool(self.accept_batch([envelope]))

    def accept_batch(self, envelopes):
        groups = {}
        for envelope in envelopes:
            sid = envelope['session_id']
            session = self._session(sid)
            if envelope['generation'] != session['generation'] or envelope['match_id'] != session['match_id']:
                raise ValueError('transport_generation_mismatch')
            message = OBSERVATION.validate_python(envelope['observation']).model_dump()
            if message['match_id'] != session['match_id']:
                raise ValueError('transport_match_mismatch')
            groups.setdefault(sid, []).append(message)
        count = 0
        for sid, messages in groups.items():
            # Durability precedes every cache update and every hub checkpoint.
            created = self.repo.append_observations(sid, messages)
            with self.lock:
                if sid in self.cache:
                    for message in messages:
                        old = self.cache[sid].get(message['message_id'])
                        if old and digest(old) != digest(message):
                            raise RepositoryConflict('observation_id_reused')
                        self.cache[sid][message['message_id']] = message
                self.received += created
            count += created
        return count

    def on_event_batch(self, context, events):
        pending = self._pending_events.setdefault(context.partition_id, deque())
        pending.extend(events or [])
        if pending:
            # A failed batch remains queued and is retried before newer arrivals.
            # Already committed session groups are verified/deduplicated on retry.
            self.accept_batch([json.loads(event.body_as_str(encoding='UTF-8')) for event in pending])
            context.update_checkpoint(pending[-1])
            pending.clear()
        self._consumer_success(context)

    def on_event(self, context, event):
        state = self._checkpoint_counts.setdefault(context.partition_id, {'count': 0, 'at': time.monotonic(), 'event': None})
        pending = self._pending_events.setdefault(context.partition_id, deque())
        if event is not None:
            pending.append(event)
        # Retry failed persistence before processing later arrivals. No checkpoint
        # may cross a failed event, even if the SDK continues callback delivery.
        while pending:
            current = pending[0]
            self.accept(json.loads(current.body_as_str(encoding='UTF-8')))
            state['event'] = current
            state['count'] += 1
            pending.popleft()
        if state['event'] and (state['count'] >= 50 or time.monotonic() - state['at'] >= 1):
            context.update_checkpoint(state['event'])
            state.update(count=0, at=time.monotonic(), event=None)
        self._consumer_success(context)

    def publish_session(self, session):
        from azure.eventhub import EventData
        _, observations = load_match(session['match_id'])
        ordered = sorted(observations, key=lambda m: (m['available_at_ms'], m['timeline_ms'], m['sequence_no']))
        cursor = self.repo.transport_cursor(session['id'])
        cutoff = replay_clock(session)
        pending = [(i, message) for i, message in enumerate(ordered)
                   if i > cursor and message['available_at_ms'] <= cutoff and message['timeline_ms'] <= cutoff]
        if not pending:
            return
        batch = self.producer.create_batch(partition_key=session['id'])
        batch_last = None
        count = 0
        for position, message in pending:
            envelope = {'session_id': session['id'], 'generation': session['generation'],
                        'match_id': session['match_id'], 'observation': message}
            event = EventData(json.dumps(envelope, separators=(',', ':')))
            try:
                batch.add(event)
            except ValueError:
                if batch_last is None:
                    raise ValueError('observation_exceeds_eventhub_batch')
                self.producer.send_batch(batch)
                self.repo.save_transport_cursor(session['id'], batch_last)
                self.sent += count
                batch = self.producer.create_batch(partition_key=session['id'])
                batch.add(event)
                count = 0
            batch_last = position
            count += 1
        self.producer.send_batch(batch)
        self.repo.save_transport_cursor(session['id'], batch_last)
        self.sent += count

    def _publish(self):
        while not self.stop.is_set():
            try:
                for session in self.repo.list_sessions():
                    if self.stop.is_set():
                        break
                    self.publish_session(session)
                self.publisher_error = None
            except Exception as exc:
                self.publisher_error = type(exc).__name__ + ': ' + str(exc)
                LOG.exception('Replay publication failed; durable cursor will retry')
            self.stop.wait(1)

    def _receive(self):
        while not self.stop.is_set():
            try:
                self.consumer.receive_batch(on_event_batch=self.on_event_batch, starting_position='-1',
                                            max_batch_size=100, max_wait_time=1, on_error=self._on_error)
            except Exception as exc:
                with self.lock:
                    self.receive_error = type(exc).__name__ + ': ' + str(exc)
                if not self.stop.is_set():
                    LOG.exception('Event Hubs consumer failed; restarting from durable checkpoint')
                    self.stop.wait(3)

    def _consumer_success(self, context):
        with self.lock:
            self.partition_errors.pop(str(context.partition_id), None)
            self.receive_error = None

    def _on_error(self, context, error):
        message = type(error).__name__ + ': ' + str(error)
        with self.lock:
            if context is None:
                self.receive_error = message
            else:
                self.partition_errors[str(context.partition_id)] = message
        LOG.error('Event Hubs partition failure: %s', message)

    def start(self):
        if self.threads:
            return
        self.threads = [threading.Thread(target=self._publish, daemon=True, name='replay-publisher'),
                        threading.Thread(target=self._receive, daemon=True, name='observation-consumer')]
        for thread in self.threads:
            thread.start()

    def close(self):
        self.stop.set()
        self.consumer.close()
        self.producer.close()
        for thread in self.threads:
            thread.join(timeout=5)

    @property
    def consumer_error(self):
        with self.lock:
            errors = [self.receive_error] if self.receive_error else []
            errors.extend(f'partition {key}: {value}' for key, value in sorted(self.partition_errors.items()))
        return '; '.join(errors) or None

    @consumer_error.setter
    def consumer_error(self, error):
        # Compatibility for callers assigning a receive-loop failure. Partition
        # failures remain separately tracked and cannot be cleared by assignment.
        with self.lock:
            self.receive_error = error

    @property
    def last_error(self):
        errors = []
        if self.publisher_error:
            errors.append('publisher: ' + self.publisher_error)
        consumer_error = self.consumer_error
        if consumer_error:
            errors.append('consumer: ' + consumer_error)
        return '; '.join(errors) or None

    def diagnostics(self):
        return {'mode': 'azure-event-hubs', 'sent_this_process': self.sent,
                'persisted_this_process': self.received, 'last_error': self.last_error,
                'publisher_error': self.publisher_error, 'consumer_error': self.consumer_error,
                'consumer_partition_errors': dict(self.partition_errors),
                'publisher_alive': bool(self.threads and self.threads[0].is_alive()),
                'consumer_alive': bool(len(self.threads) > 1 and self.threads[1].is_alive())}
