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

    def append_lifecycle(self,sid,event):
        from engine.dispositions import validate_event
        validate_event(sid,event)
        key='lifecycle:'+event['id']
        doc=self._doc(sid,key,'lifecycle_event',event)
        try:
            self.stories.create_item(doc)
        except Exception as exc:
            if _status(exc)!=409:raise
        return self._read(self.stories,key,sid)['data']

    def lifecycle_events(self,sid):
        rows=[d['data'] for d in self.stories.query_items(
            query='SELECT c.data FROM c WHERE c.type = "lifecycle_event"',partition_key=sid)]
        return sorted(rows,key=lambda e:(e['recorded_at'],e['id']))

    def save_workflow_outcome(self, sid, outcome):
        from engine.outcomes import validate_outcome
        item = 'run:' + outcome['run_id']
        previous = self._read(self.stories, item, sid)
        validate_outcome(sid, outcome, previous['data'] if previous else None)
        if previous and previous['data'] == outcome:
            return
        doc = self._doc(sid, item, 'workflow_outcome', outcome)
        doc['kind'] = 'workflow_outcome'
        operation = ('replace', (item, doc), {'if_match_etag': previous['_etag']}) if previous else ('create', (doc,))
        try:
            self._batch(sid, [operation])
        except RepositoryConflict:
            # Simultaneous identical writes are harmless; divergent writes must
            # not overwrite a completion or erase another process's attempts.
            current = self._read(self.stories, item, sid)
            if current and current['data'] == outcome:
                return
            raise RepositoryConflict('workflow_outcome_conflict')

    def workflow_outcomes(self, sid):
        outcomes = [d['data'] for d in self.stories.query_items(
            query='SELECT c.data FROM c WHERE c.type = "workflow_outcome"', partition_key=sid)]
        return sorted(outcomes, key=lambda o: (o['scheduled_at'], o['run_id']))

    def interrupt_workflow_outcomes(self):
        from engine.outcomes import ACTIVE_STATES, interrupted_outcome
        count = 0
        documents = self.stories.query_items(
            query='SELECT c.session_id, c.data FROM c WHERE c.type = "workflow_outcome"',
            enable_cross_partition_query=True)
        for doc in documents:
            outcome = doc['data']
            if outcome['state'] in ACTIVE_STATES:
                try:
                    self.save_workflow_outcome(doc['session_id'], interrupted_outcome(outcome))
                    count += 1
                except RepositoryConflict:
                    current = self._read(self.stories, 'run:' + outcome['run_id'], doc['session_id'])
                    if not current or current['data']['state'] in ACTIVE_STATES:
                        raise
        return count

    def list_sessions(self):
        return [d['data'] for d in self.sessions.query_items(
            query='SELECT c.data FROM c WHERE c.type = "session"', enable_cross_partition_query=True)]

    @staticmethod
    def _story_key(story_id):
        return 'story:' + digest(story_id)

    def _pointer(self, sid, story_id=None):
        if story_id is None:return self._read(self.stories, 'current', sid)
        pointer=self._read(self.stories,self._story_key(story_id)+':current',sid)
        if pointer:return pointer
        legacy=self._read(self.stories,'current',sid)
        if legacy and 'stories' not in legacy:
            package=self._read(self.stories,f"package:{legacy['revision']}",sid)
            if package and package['data']['id']==story_id:return legacy
        # A migrated manifest can still refer to an unmigrated legacy story.
        if legacy and story_id in legacy.get('stories',[]):
            package_id=legacy.get('legacy_package_id')
            package=self._read(self.stories,package_id,sid) if package_id else None
            if package and package['data']['id']==story_id:
                return {**legacy,'revision':package['data']['revision'],'package_hash':package['data']['package_hash'],'package_id':package_id}
        return None

    def latest_package(self, sid, story_id=None):
        pointer=self._pointer(sid,story_id)
        if not pointer:return None
        package_id=pointer.get('package_id',f"package:{pointer['revision']}")
        doc=self._read(self.stories,package_id,sid)
        return doc['data'] if doc else None

    def stored_package(self, sid, story_id, revision):
        item = self._story_key(story_id) + ':package:' + str(revision)
        doc = self._read(self.stories, item, sid)
        if doc:
            return doc['data']
        legacy = self._read(self.stories, f'package:{revision}', sid)
        return legacy['data'] if legacy and legacy['data']['id'] == story_id else None

    def list_packages(self,sid):
        current=self._pointer(sid)
        if not current:return []
        if 'stories' not in current:
            package=self.latest_package(sid)
            return [package] if package else []
        packages=[self.latest_package(sid,story_id) for story_id in current['stories']]
        return sorted((p for p in packages if p),key=lambda p:(p.get('eligible_from_ms',0),p['id']))

    def _decision_doc(self,sid,story_id):
        doc=self._read(self.stories,self._story_key(story_id)+':decision',sid)
        if doc:return doc
        legacy=self._read(self.stories,'decision',sid)
        if legacy:
            package=self._read(self.stories,f"package:{legacy['data']['revision']}",sid)
            if package and package['data']['id']==story_id:return legacy
        return None

    def decision(self, sid, story_id=None):
        package=self.latest_package(sid,story_id)
        if not package:return None
        doc=self._decision_doc(sid,package['id'])
        return doc['data'] if doc else None

    def _publication_ops(self,sid,package,advance_latest=True,expected_pointer=None):
        """Guard the session manifest and the independently versioned story pointer."""
        current=self._pointer(sid)
        story_id=package['id'];key=self._story_key(story_id)
        pointer=self._pointer(sid,story_id)
        if (pointer or {}).get('_etag') != (expected_pointer or {}).get('_etag'):
            raise RepositoryConflict('stale_revision')
        package_id=key+':package:'+str(package['revision'])
        story_current={'id':key+':current','session_id':sid,'story_id':story_id,
                       'revision':package['revision'],'package_hash':package['package_hash'],'package_id':package_id}
        manifest=dict(current) if current else {'id':'current','session_id':sid}
        stories=list(manifest.get('stories',[]))
        if current and 'stories' not in current:
            legacy_id=f"package:{current['revision']}"
            legacy=self._read(self.stories,legacy_id,sid)
            if legacy:
                stories.append(legacy['data']['id']);manifest['legacy_package_id']=legacy_id
        if story_id not in stories:stories.append(story_id)
        manifest['stories']=stories
        if advance_latest or not current:
            manifest.update({'story_id':story_id,'revision':package['revision'],'package_hash':package['package_hash'],'package_id':package_id})
        ops=[('replace',('current',manifest),{'if_match_etag':current['_etag']}) if current else ('create',(manifest,))]
        if pointer and pointer['id']==story_current['id']:
            ops.append(('replace',(story_current['id'],story_current),{'if_match_etag':pointer['_etag']}))
        else:ops.append(('create',(story_current,)))
        return ops

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

    def invalidate(self, sid, story_id=None):
        current=self._pointer(sid)
        if not current:return
        packages=self.list_packages(sid) if story_id is None else [self.latest_package(sid,story_id)]
        ops=[('replace',('current',current),{'if_match_etag':current['_etag']})]
        for package in packages:
            if not package:continue
            pointer=self._pointer(sid,package['id'])
            if pointer and pointer['id']!='current':
                ops.append(('replace',(pointer['id'],pointer),{'if_match_etag':pointer['_etag']}))
            decision=self._decision_doc(sid,package['id'])
            if decision and decision['data']['status']!='superseded':
                decision['data']['status']='superseded'
                ops.append(('replace',(decision['id'],decision),{'if_match_etag':decision['_etag']}))
        self._batch(sid,ops)

    def store_package(self, sid, package, at_ms, expected_revision=None, acceptance_events=()):
        from engine.dispositions import validate_acceptance_events
        if package.get('schema_version') in {'5.0.0','6.0.0','7.0.0'}:
            from engine.event_narrative import EventPackage
            EventPackage.model_validate(package)
        validate_acceptance_events(sid, package, acceptance_events)
        pointer=self._pointer(sid,package['id'])
        prior=pointer['revision'] if pointer else 0
        if (expected_revision is not None and prior!=expected_revision) or package['revision']!=prior+1:
            raise RepositoryConflict('stale_revision')
        ops=self._publication_ops(sid,package,expected_pointer=pointer)
        ops.append(('create',(self._doc(sid,self._story_key(package['id'])+':package:'+str(package['revision']),'package',package),)))
        decision=self._decision_doc(sid,package['id'])
        if decision:
            decision['data']['status']='superseded'
            ops.append(('replace',(decision['id'],decision),{'if_match_etag':decision['_etag']}))
        ops.append(('create',(self._audit(sid,'package_ready',at_ms,{'story_id':package['id'],'revision':package['revision'],'workflow_ms':package['workflow_ms']}),)))
        ops.extend(('create', (self._doc(sid, 'lifecycle:' + event['id'], 'lifecycle_event', event),))
                   for event in acceptance_events)
        self._batch(sid,ops)

    def commit_review(self, sid, key, request_hash, expected_revision, expected_hash, package, status, at_ms, result, edited=False):
        old=self.operation(sid,key)
        if old:
            if old['request_hash']!=request_hash:raise RepositoryConflict('idempotency_key_reused')
            return old['data']
        pointer=self._pointer(sid,package['id'])
        if not pointer or pointer['revision']!=expected_revision or pointer['package_hash']!=expected_hash:
            raise RepositoryConflict('stale_revision')
        if (edited and package['revision']!=expected_revision+1) or (not edited and (package['revision']!=expected_revision or package['package_hash']!=expected_hash)):
            raise RepositoryConflict('stale_revision')
        ops=self._publication_ops(sid,package,advance_latest=edited,expected_pointer=pointer)
        package_id=self._story_key(package['id'])+':package:'+str(package['revision'])
        # Migrating an unedited legacy package also creates its story-specific immutable copy.
        if edited or not self._read(self.stories,package_id,sid):
            ops.append(('create',(self._doc(sid,package_id,'package',package),)))
        decision={'session_id':sid,'story_id':package['id'],'revision':package['revision'],'status':status,'at_ms':at_ms,'package_hash':package['package_hash']}
        decision_id=self._story_key(package['id'])+':decision'
        prior_decision=self._read(self.stories,decision_id,sid)
        doc=self._doc(sid,decision_id,'decision',decision)
        ops.append(('replace',(decision_id,doc),{'if_match_etag':prior_decision['_etag']}) if prior_decision else ('create',(doc,)))
        action='edit' if edited else {'approved':'approve','suppressed':'suppress','retracted':'retract'}[status]
        ops.extend([('create',(self._doc(sid,'operation:'+digest(key),'operation',{'request_hash':request_hash,'data':result}),)),
                    ('create',(self._audit(sid,action,at_ms,{**result,'story_id':package['id']}),))])
        try:self._batch(sid,ops)
        except RepositoryConflict:
            old=self.operation(sid,key)
            if old:
                if old['request_hash']!=request_hash:raise RepositoryConflict('idempotency_key_reused')
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
