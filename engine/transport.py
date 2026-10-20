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
from collections import deque
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
        self.last_error = None
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
            consumer = consumer or EventHubConsumerClient(consumer_group=os.getenv('WHY_NOW_EVENTHUB_CONSUMER_GROUP', 'whynow-state'), checkpoint_store=checkpoint, **options)
        self.producer = producer
        self.consumer = consumer

    def messages(self, session, cutoff):
        sid = session['id']
        with self.lock:
            if sid not in self.cache:
                self.cache[sid] = {m['message_id']: m for m in self.repo.read_observations(sid)}
            # The durable cache may include arrivals beyond the current replay clock.
            # Enforce both availability and occurrence at every boundary, also after pause/restart.
            return available(list(self.cache[sid].values()), cutoff)

    def accept(self, envelope):
        sid = envelope['session_id']
        session = self.repo.get_session(sid)
        if not session:
            raise ValueError('unknown_transport_session')
        if envelope['generation'] != session['generation'] or envelope['match_id'] != session['match_id']:
            raise ValueError('transport_generation_mismatch')
        message = OBSERVATION.validate_python(envelope['observation']).model_dump()
        if message['match_id'] != session['match_id']:
            raise ValueError('transport_match_mismatch')
        # Cosmos create is the durability boundary. Exact retries are no-ops; changed
        # content using an existing ID is rejected, including across restarts.
        created = self.repo.append_observation(sid, message)
        with self.lock:
            if sid in self.cache:
                old = self.cache[sid].get(message['message_id'])
                if old and digest(old) != digest(message):
                    raise RepositoryConflict('observation_id_reused')
                self.cache[sid][message['message_id']] = message
            self.received += int(created)
        return created

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
        self.last_error = None

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
            except Exception as exc:
                self.last_error = type(exc).__name__ + ': ' + str(exc)
                LOG.exception('Replay publication failed; durable cursor will retry')
            self.stop.wait(1)

    def _receive(self):
        while not self.stop.is_set():
            try:
                self.consumer.receive(on_event=self.on_event, starting_position='-1', max_wait_time=1,
                                      on_error=self._on_error)
            except Exception as exc:
                self.last_error = type(exc).__name__ + ': ' + str(exc)
                if not self.stop.is_set():
                    LOG.exception('Event Hubs consumer failed; restarting from durable checkpoint')
                    self.stop.wait(3)

    def _on_error(self, context, error):
        self.last_error = type(error).__name__ + ': ' + str(error)
        LOG.error('Event Hubs partition failure: %s', self.last_error)

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

    def diagnostics(self):
        return {'mode': 'azure-event-hubs', 'sent_this_process': self.sent,
                'persisted_this_process': self.received, 'last_error': self.last_error,
                'publisher_alive': bool(self.threads and self.threads[0].is_alive()),
                'consumer_alive': bool(len(self.threads) > 1 and self.threads[1].is_alive())}
