"""SQLite persistence for replay sessions, immutable packages, decisions and audit."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

class Repository:
    def __init__(self,path): self.path=Path(path)
    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        c=sqlite3.connect(self.path,timeout=15);c.row_factory=sqlite3.Row
        c.executescript('''
        CREATE TABLE IF NOT EXISTS replay_sessions(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS packages(session_id TEXT, revision INTEGER, data TEXT NOT NULL, PRIMARY KEY(session_id,revision));
        CREATE TABLE IF NOT EXISTS story_packages(sequence INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, story_id TEXT, revision INTEGER, data TEXT NOT NULL, UNIQUE(session_id,story_id,revision));
        CREATE TABLE IF NOT EXISTS story_editorial(session_id TEXT, story_id TEXT, revision INTEGER, status TEXT, at_ms INTEGER, package_hash TEXT, PRIMARY KEY(session_id,story_id));
        CREATE TABLE IF NOT EXISTS editorial(session_id TEXT PRIMARY KEY, revision INTEGER, status TEXT, at_ms INTEGER, package_hash TEXT);
        CREATE TABLE IF NOT EXISTS operations(session_id TEXT, operation_id TEXT, request_hash TEXT, data TEXT, PRIMARY KEY(session_id,operation_id));
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, action TEXT, at_ms INTEGER, data TEXT);
        CREATE TABLE IF NOT EXISTS lifecycle_events(session_id TEXT, event_id TEXT, data TEXT NOT NULL, PRIMARY KEY(session_id,event_id));
        CREATE TABLE IF NOT EXISTS workflow_outcomes(session_id TEXT, run_id TEXT, data TEXT NOT NULL, PRIMARY KEY(session_id,run_id));
        ''')
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback(); raise
        finally:c.close()
    def get_session(self,sid):
        with self.connect() as c:
            row=c.execute('SELECT data FROM replay_sessions WHERE id=?',(sid,)).fetchone()
            return json.loads(row['data']) if row else None
    def save_session(self,s):
        with self.connect() as c:c.execute('INSERT OR REPLACE INTO replay_sessions VALUES (?,?)',(s['id'],json.dumps(s)))

    def append_lifecycle(self,sid,event):
        from engine.dispositions import validate_event
        validate_event(sid,event)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT OR IGNORE INTO lifecycle_events VALUES (?,?,?)',(sid,event['id'],json.dumps(event)))
            return json.loads(c.execute('SELECT data FROM lifecycle_events WHERE session_id=? AND event_id=?',
                                       (sid,event['id'])).fetchone()['data'])

    def lifecycle_events(self,sid):
        with self.connect() as c:
            rows=[json.loads(row['data']) for row in c.execute('SELECT data FROM lifecycle_events WHERE session_id=?',(sid,))]
            return sorted(rows,key=lambda e:(e['recorded_at'],e['id']))

    def save_workflow_outcome(self,sid,outcome):
        from engine.outcomes import validate_outcome
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT data FROM workflow_outcomes WHERE session_id=? AND run_id=?',
                          (sid,outcome['run_id'])).fetchone()
            previous=json.loads(row['data']) if row else None
            validate_outcome(sid,outcome,previous)
            c.execute('INSERT OR REPLACE INTO workflow_outcomes VALUES (?,?,?)',
                      (sid,outcome['run_id'],json.dumps(outcome)))

    def workflow_outcomes(self,sid):
        with self.connect() as c:
            outcomes=[json.loads(row['data']) for row in c.execute(
                'SELECT data FROM workflow_outcomes WHERE session_id=?',(sid,))]
            return sorted(outcomes,key=lambda o:(o['scheduled_at'],o['run_id']))

    def interrupt_workflow_outcomes(self):
        from engine.outcomes import ACTIVE_STATES, interrupted_outcome
        count=0
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            for row in c.execute('SELECT session_id,run_id,data FROM workflow_outcomes').fetchall():
                outcome=json.loads(row['data'])
                if outcome['state'] in ACTIVE_STATES:
                    c.execute('UPDATE workflow_outcomes SET data=? WHERE session_id=? AND run_id=?',
                              (json.dumps(interrupted_outcome(outcome)),row['session_id'],row['run_id']))
                    count+=1
        return count
    @staticmethod
    def _latest(c,sid,story_id=None):
        if story_id is None:
            row=c.execute('SELECT data FROM story_packages WHERE session_id=? ORDER BY sequence DESC LIMIT 1',(sid,)).fetchone()
        else:
            row=c.execute('SELECT data FROM story_packages WHERE session_id=? AND story_id=? ORDER BY revision DESC LIMIT 1',(sid,story_id)).fetchone()
        if row:return json.loads(row['data'])
        for row in c.execute('SELECT data FROM packages WHERE session_id=? ORDER BY revision DESC',(sid,)):
            package=json.loads(row['data'])
            if story_id is None or package['id']==story_id:return package
        return None

    def latest_package(self,sid,story_id=None):
        with self.connect() as c:return self._latest(c,sid,story_id)

    def stored_package(self, sid, story_id, revision):
        """Read an immutable revision without advancing publication pointers."""
        with self.connect() as c:
            row = c.execute('SELECT data FROM story_packages WHERE session_id=? AND story_id=? AND revision=?',
                            (sid, story_id, revision)).fetchone()
            if row:
                return json.loads(row['data'])
            row = c.execute('SELECT data FROM packages WHERE session_id=? AND revision=?',
                            (sid, revision)).fetchone()
            package = json.loads(row['data']) if row else None
            return package if package and package['id'] == story_id else None

    def list_packages(self,sid):
        with self.connect() as c:
            packages={}
            for row in c.execute('SELECT data FROM packages WHERE session_id=? ORDER BY revision',(sid,)):
                package=json.loads(row['data']);packages[package['id']]=package
            for row in c.execute('SELECT data FROM story_packages WHERE session_id=? ORDER BY sequence',(sid,)):
                package=json.loads(row['data']);packages[package['id']]=package
            return sorted(packages.values(),key=lambda p:(p.get('eligible_from_ms',0),p['id']))

    def decision(self,sid,story_id=None):
        with self.connect() as c:
            package=self._latest(c,sid,story_id)
            if not package:return None
            story_id=package['id']
            row=c.execute('SELECT * FROM story_editorial WHERE session_id=? AND story_id=?',(sid,story_id)).fetchone()
            if row:return dict(row)
            legacy=c.execute('SELECT data FROM packages WHERE session_id=? ORDER BY revision DESC LIMIT 1',(sid,)).fetchone()
            if legacy and json.loads(legacy['data'])['id']==story_id:
                row=c.execute('SELECT * FROM editorial WHERE session_id=?',(sid,)).fetchone()
                return dict(row) if row else None
            return None
    def audit(self,sid):
        with self.connect() as c:return [dict(row) for row in c.execute('SELECT action,at_ms,data FROM audit_log WHERE session_id=? ORDER BY id',(sid,))]

    def list_sessions(self):
        with self.connect() as c:
            return [json.loads(row['data']) for row in c.execute('SELECT data FROM replay_sessions')]

    def invalidate(self,sid,story_id=None):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if story_id is None:
                c.execute('UPDATE story_editorial SET status=? WHERE session_id=?',('superseded',sid))
                c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',sid))
            else:
                c.execute('UPDATE story_editorial SET status=? WHERE session_id=? AND story_id=?',('superseded',sid,story_id))
                legacy=c.execute('SELECT data FROM packages WHERE session_id=? ORDER BY revision DESC LIMIT 1',(sid,)).fetchone()
                if legacy and json.loads(legacy['data'])['id']==story_id:
                    c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',sid))

    def operation(self,sid,key):
        with self.connect() as c:
            row=c.execute('SELECT request_hash,data FROM operations WHERE session_id=? AND operation_id=?',(sid,key)).fetchone()
            return {'request_hash':row['request_hash'],'data':json.loads(row['data'])} if row else None

    def store_package(self,sid,package,at_ms,expected_revision=None,acceptance_events=()):
        from engine.cloud_repository import RepositoryConflict
        from engine.dispositions import validate_acceptance_events
        if package.get('schema_version') in {'5.0.0','6.0.0','7.0.0'}:
            from engine.event_narrative import EventPackage
            EventPackage.model_validate(package)
        validate_acceptance_events(sid,package,acceptance_events)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            previous=self._latest(c,sid,package['id'])
            old=previous['revision'] if previous else 0
            if (expected_revision is not None and old!=expected_revision) or package['revision']!=old+1:
                raise RepositoryConflict('stale_revision')
            c.execute('INSERT INTO story_packages(session_id,story_id,revision,data) VALUES (?,?,?,?)',(sid,package['id'],package['revision'],json.dumps(package)))
            for event in acceptance_events:
                c.execute('INSERT INTO lifecycle_events VALUES (?,?,?)',
                          (sid,event['id'],json.dumps(event)))
            c.execute('UPDATE story_editorial SET status=? WHERE session_id=? AND story_id=?',('superseded',sid,package['id']))
            # Supersede legacy approval when this story is migrated.
            legacy=c.execute('SELECT data FROM packages WHERE session_id=? ORDER BY revision DESC LIMIT 1',(sid,)).fetchone()
            if legacy and json.loads(legacy['data'])['id']==package['id']:
                c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',sid))
            c.execute('INSERT INTO audit_log(session_id,action,at_ms,data) VALUES (?,?,?,?)',(sid,'package_ready',at_ms,json.dumps({'story_id':package['id'],'revision':package['revision'],'workflow_ms':package['workflow_ms']})))

    def commit_review(self,sid,key,request_hash,expected_revision,expected_hash,package,status,at_ms,result,edited=False):
        from engine.cloud_repository import RepositoryConflict
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT * FROM operations WHERE session_id=? AND operation_id=?',(sid,key)).fetchone()
            if old:
                if old['request_hash']!=request_hash:raise RepositoryConflict('idempotency_key_reused')
                return json.loads(old['data'])
            latest=self._latest(c,sid,package['id'])
            if not latest or latest['revision']!=expected_revision or latest['package_hash']!=expected_hash:
                raise RepositoryConflict('stale_revision')
            if not edited and (package['revision']!=expected_revision or package['package_hash']!=expected_hash):
                raise RepositoryConflict('stale_revision')
            if edited:
                if package['revision']!=expected_revision+1:raise RepositoryConflict('stale_revision')
                c.execute('INSERT INTO story_packages(session_id,story_id,revision,data) VALUES (?,?,?,?)',(sid,package['id'],package['revision'],json.dumps(package)))
            c.execute('INSERT OR REPLACE INTO story_editorial VALUES (?,?,?,?,?,?)',(sid,package['id'],package['revision'],status,at_ms,package['package_hash']))
            action='edit' if edited else {'approved':'approve','suppressed':'suppress','retracted':'retract'}[status]
            c.execute('INSERT INTO audit_log(session_id,action,at_ms,data) VALUES (?,?,?,?)',(sid,action,at_ms,json.dumps({**result,'story_id':package['id']})))
            c.execute('INSERT INTO operations VALUES (?,?,?,?)',(sid,key,request_hash,json.dumps(result)))
        return result

    def append_observation(self,sid,message):
        return bool(self.append_observations(sid,[message]))

    def append_observations(self,sid,messages):
        from engine.contracts import OBSERVATION
        from engine.core import digest
        from engine.cloud_repository import RepositoryConflict
        for message in messages:OBSERVATION.validate_python(message)
        count=0
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS observations(session_id TEXT,message_id TEXT,sequence_no INTEGER,data TEXT,PRIMARY KEY(session_id,message_id))')
            c.execute('BEGIN IMMEDIATE')
            for message in messages:
                old=c.execute('SELECT data FROM observations WHERE session_id=? AND message_id=?',(sid,message['message_id'])).fetchone()
                if old:
                    if digest(json.loads(old['data']))!=digest(message):raise RepositoryConflict('observation_id_reused')
                    continue
                c.execute('INSERT INTO observations VALUES (?,?,?,?)',(sid,message['message_id'],message['sequence_no'],json.dumps(message)))
                count+=1
        return count

    def read_observations(self,sid):
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS observations(session_id TEXT,message_id TEXT,sequence_no INTEGER,data TEXT,PRIMARY KEY(session_id,message_id))')
            return [json.loads(row['data']) for row in c.execute('SELECT data FROM observations WHERE session_id=? ORDER BY sequence_no',(sid,))]

    def transport_cursor(self,sid):
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS transport_cursors(session_id TEXT PRIMARY KEY,sequence_no INTEGER)')
            row=c.execute('SELECT sequence_no FROM transport_cursors WHERE session_id=?',(sid,)).fetchone()
            return row['sequence_no'] if row else -1

    def save_transport_cursor(self,sid,sequence_no):
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS transport_cursors(session_id TEXT PRIMARY KEY,sequence_no INTEGER)')
            c.execute('INSERT OR REPLACE INTO transport_cursors VALUES (?,?)',(sid,sequence_no))
