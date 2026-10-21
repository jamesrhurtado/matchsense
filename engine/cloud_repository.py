"""Managed-identity Cosmos persistence with atomic, session-partitioned publication.

Containers must already exist. Infrastructure and RBAC are provisioned separately.
"""
from __future__ import annotations
import json
import os
import uuid
from engine.core import digest


class RepositoryConflict(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _status(exc):
    return getattr(exc, 'status_code', None)


class CosmosRepository:
    def __init__(self, endpoint=None, database=None, credential=None, client=None):
        if client is None:
            from azure.cosmos import CosmosClient
            if credential is None:
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential(managed_identity_client_id=os.getenv('AZURE_CLIENT_ID'))
            client = CosmosClient(endpoint or os.environ['WHY_NOW_COSMOS_ENDPOINT'], credential=credential)
        self.client = client
        db = client.get_database_client(database or os.getenv('WHY_NOW_COSMOS_DATABASE', 'whynow'))
        self.sessions = db.get_container_client('session-state')
        self.stories = db.get_container_client('story-state')
        self.observations = db.get_container_client('observations')

    @staticmethod
    def _read(container, item, sid):
        try:
            return container.read_item(item=item, partition_key=sid)
        except Exception as exc:
            if _status(exc) == 404:
                return None
            raise

    def get_session(self, sid):
        doc = self._read(self.sessions, 'session', sid)
        return doc['data'] if doc else None

    def save_session(self, session):
        self.sessions.upsert_item({'id': 'session', 'session_id': session['id'], 'type': 'session', 'data': session})

    def list_sessions(self):
        return [d['data'] for d in self.sessions.query_items(
            query='SELECT c.data FROM c WHERE c.type = "session"', enable_cross_partition_query=True)]

    def _pointer(self, sid):
        return self._read(self.stories, 'current', sid)

    def latest_package(self, sid):
        pointer = self._pointer(sid)
        if not pointer:
            return None
        return self._read(self.stories, f"package:{pointer['revision']}", sid)['data']

    def decision(self, sid):
        doc = self._read(self.stories, 'decision', sid)
        return doc['data'] if doc else None

    def audit(self, sid):
        return [d['data'] for d in self.stories.query_items(
            query='SELECT c.data FROM c WHERE c.type = "audit" ORDER BY c.created_at', partition_key=sid)]

    def operation(self, sid, key):
        doc = self._read(self.stories, 'operation:' + digest(key), sid)
        return doc['data'] if doc else None

    @staticmethod
    def _doc(sid, item, kind, data):
        return {'id': item, 'session_id': sid, 'type': kind, 'data': data}

    def _audit(self, sid, action, at_ms, data):
        import time
        doc = self._doc(sid, 'audit:' + uuid.uuid4().hex, 'audit', {
            'action': action, 'at_ms': at_ms, 'data': json.dumps(data)})
        doc['created_at'] = time.time_ns()
        return doc

    def _batch(self, sid, operations):
        try:
            return self.stories.execute_item_batch(batch_operations=operations, partition_key=sid)
        except Exception as exc:
            if _status(exc) in (409, 412, 424):
                raise RepositoryConflict('stale_revision') from exc
            raise

    def invalidate(self, sid):
        decision = self._read(self.stories, 'decision', sid)
        pointer = self._pointer(sid)
        if decision and decision['data']['status'] != 'superseded':
            decision['data']['status'] = 'superseded'
            ops = [('replace', ('decision', decision), {'if_match_etag': decision['_etag']})]
            # Advance the publication ETag as well so an approval racing with
            # invalidation cannot commit using the old evidence snapshot.
            if pointer:
                ops.append(('replace', ('current', pointer), {'if_match_etag': pointer['_etag']}))
            self._batch(sid, ops)

    def store_package(self, sid, package, at_ms, expected_revision=None):
        pointer = self._pointer(sid)
        prior = pointer['revision'] if pointer else 0
        if (expected_revision is not None and prior != expected_revision) or package['revision'] != prior + 1:
            raise RepositoryConflict('stale_revision')
        current = {'id': 'current', 'session_id': sid, 'revision': package['revision'], 'package_hash': package['package_hash']}
        ops = [('create', (self._doc(sid, f"package:{package['revision']}", 'package', package),)),
               ('replace', ('current', current), {'if_match_etag': pointer['_etag']}) if pointer else ('create', (current,))]
        decision = self._read(self.stories, 'decision', sid)
        if decision:
            decision['data']['status'] = 'superseded'
            ops.append(('replace', ('decision', decision), {'if_match_etag': decision['_etag']}))
        ops.append(('create', (self._audit(sid, 'package_ready', at_ms, {'revision': package['revision'], 'workflow_ms': package['workflow_ms']}),)))
        self._batch(sid, ops)

    def commit_review(self, sid, key, request_hash, expected_revision, expected_hash, package, status, at_ms, result, edited=False):
        old = self.operation(sid, key)
        if old:
            if old['request_hash'] != request_hash:
                raise RepositoryConflict('idempotency_key_reused')
            return old['data']
        if not edited and (package['revision'] != expected_revision or package['package_hash'] != expected_hash):
            raise RepositoryConflict('stale_revision')
        pointer = self._pointer(sid)
        if not pointer or pointer['revision'] != expected_revision or pointer['package_hash'] != expected_hash:
            raise RepositoryConflict('stale_revision')
        current = {'id': 'current', 'session_id': sid, 'revision': package['revision'], 'package_hash': package['package_hash']}
        decision = {'session_id': sid, 'revision': package['revision'], 'status': status, 'at_ms': at_ms, 'package_hash': package['package_hash']}
        ops = [('replace', ('current', current), {'if_match_etag': pointer['_etag']}),
               ('upsert', (self._doc(sid, 'decision', 'decision', decision),)),
               ('create', (self._doc(sid, 'operation:' + digest(key), 'operation', {'request_hash': request_hash, 'data': result}),)),
               ('create', (self._audit(sid, 'edit' if edited else {'approved': 'approve', 'suppressed': 'suppress', 'retracted': 'retract'}[status], at_ms, result),))]
        if edited:
            if package['revision'] != expected_revision + 1:
                raise RepositoryConflict('stale_revision')
            ops.append(('create', (self._doc(sid, f"package:{package['revision']}", 'package', package),)))
        try:
            self._batch(sid, ops)
        except RepositoryConflict:
            old = self.operation(sid, key)
            if old:
                if old['request_hash'] != request_hash:
                    raise RepositoryConflict('idempotency_key_reused')
                return old['data']
            raise
        return result

    def append_observation(self, sid, message):
        return bool(self.append_observations(sid, [message]))

    def append_observations(self, sid, messages):
        from engine.contracts import OBSERVATION
        unique = {}
        for message in messages:
            OBSERVATION.validate_python(message)
            key = 'observation:' + message['message_id']
            if key in unique and digest(unique[key]) != digest(message):
                raise RepositoryConflict('observation_id_reused')
            unique[key] = message
        if not unique:
            return 0
        # Cosmos allows at most 100 operations and 2MB per transactional batch.
        # Event Hubs receive_batch is capped at 100; chunk defensively for callers.
        total = 0
        entries = list(unique.items())
        for start in range(0, len(entries), 100):
            group = dict(entries[start:start + 100])
            for attempt in range(4):
                existing = list(self.observations.query_items(
                    query='SELECT c.id, c.data FROM c WHERE c.type = "observation" AND ARRAY_CONTAINS(@ids, c.id)',
                    parameters=[{'name': '@ids', 'value': list(group)}], partition_key=sid))
                known = {row['id']: row['data'] for row in existing}
                for key, value in known.items():
                    if digest(value) != digest(group[key]):
                        raise RepositoryConflict('observation_id_reused')
                docs = []
                for key, message in group.items():
                    if key not in known:
                        doc = self._doc(sid, key, 'observation', message)
                        doc['sequence_no'] = message['sequence_no']
                        docs.append(doc)
                if not docs:
                    break
                try:
                    self.observations.execute_item_batch(
                        batch_operations=[('create', (doc,)) for doc in docs], partition_key=sid)
                    total += len(docs)
                    break
                except Exception as exc:
                    if _status(exc) not in (409, 412, 424) or attempt == 3:
                        raise
                    # Another consumer may have durably written the same IDs
                    # during rollout. Reread and verify hashes before retrying.
        return total

    def read_observations(self, sid):
        return [d['data'] for d in self.observations.query_items(
            query='SELECT c.data FROM c WHERE c.type = "observation" ORDER BY c.sequence_no', partition_key=sid)]

    def transport_cursor(self, sid):
        doc = self._read(self.sessions, 'transport', sid)
        return doc['sequence_no'] if doc else -1

    def save_transport_cursor(self, sid, sequence_no):
        self.sessions.upsert_item({'id': 'transport', 'session_id': sid, 'sequence_no': sequence_no})
