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
        CREATE TABLE IF NOT EXISTS editorial(session_id TEXT PRIMARY KEY, revision INTEGER, status TEXT, at_ms INTEGER, package_hash TEXT);
        CREATE TABLE IF NOT EXISTS operations(session_id TEXT, operation_id TEXT, request_hash TEXT, data TEXT, PRIMARY KEY(session_id,operation_id));
        CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, action TEXT, at_ms INTEGER, data TEXT);
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
    def latest_package(self,sid):
        with self.connect() as c:
            row=c.execute('SELECT data FROM packages WHERE session_id=? ORDER BY revision DESC LIMIT 1',(sid,)).fetchone()
            return json.loads(row['data']) if row else None
    def decision(self,sid):
        with self.connect() as c:
            row=c.execute('SELECT * FROM editorial WHERE session_id=?',(sid,)).fetchone()
            return dict(row) if row else None
    def audit(self,sid):
        with self.connect() as c:return [dict(row) for row in c.execute('SELECT action,at_ms,data FROM audit_log WHERE session_id=? ORDER BY id',(sid,))]

    def list_sessions(self):
        with self.connect() as c:
            return [json.loads(row['data']) for row in c.execute('SELECT data FROM replay_sessions')]

    def invalidate(self,sid):
        with self.connect() as c:
            c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',sid))

    def operation(self,sid,key):
        with self.connect() as c:
            row=c.execute('SELECT request_hash,data FROM operations WHERE session_id=? AND operation_id=?',(sid,key)).fetchone()
            return {'request_hash':row['request_hash'],'data':json.loads(row['data'])} if row else None

    def store_package(self,sid,package,at_ms,expected_revision=None):
        from engine.cloud_repository import RepositoryConflict
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT MAX(revision) AS revision FROM packages WHERE session_id=?',(sid,)).fetchone()['revision'] or 0
            if (expected_revision is not None and old!=expected_revision) or package['revision']!=old+1:
                raise RepositoryConflict('stale_revision')
            c.execute('INSERT INTO packages VALUES (?,?,?)',(sid,package['revision'],json.dumps(package)))
            c.execute('UPDATE editorial SET status=? WHERE session_id=?',('superseded',sid))
            c.execute('INSERT INTO audit_log(session_id,action,at_ms,data) VALUES (?,?,?,?)',(sid,'package_ready',at_ms,json.dumps({'revision':package['revision'],'workflow_ms':package['workflow_ms']})))

    def commit_review(self,sid,key,request_hash,expected_revision,expected_hash,package,status,at_ms,result,edited=False):
        from engine.cloud_repository import RepositoryConflict
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT * FROM operations WHERE session_id=? AND operation_id=?',(sid,key)).fetchone()
            if old:
                if old['request_hash']!=request_hash:raise RepositoryConflict('idempotency_key_reused')
                return json.loads(old['data'])
            latest=c.execute('SELECT revision,data FROM packages WHERE session_id=? ORDER BY revision DESC LIMIT 1',(sid,)).fetchone()
            if not latest or latest['revision']!=expected_revision or json.loads(latest['data'])['package_hash']!=expected_hash:
                raise RepositoryConflict('stale_revision')
            if not edited and (package['revision']!=expected_revision or package['package_hash']!=expected_hash):
                raise RepositoryConflict('stale_revision')
            if edited:
                if package['revision']!=expected_revision+1:raise RepositoryConflict('stale_revision')
                c.execute('INSERT INTO packages VALUES (?,?,?)',(sid,package['revision'],json.dumps(package)))
            c.execute('INSERT OR REPLACE INTO editorial VALUES (?,?,?,?,?)',(sid,package['revision'],status,at_ms,package['package_hash']))
            action='edit' if edited else {'approved':'approve','suppressed':'suppress','retracted':'retract'}[status]
            c.execute('INSERT INTO audit_log(session_id,action,at_ms,data) VALUES (?,?,?,?)',(sid,action,at_ms,json.dumps(result)))
            c.execute('INSERT INTO operations VALUES (?,?,?,?)',(sid,key,request_hash,json.dumps(result)))
        return result

    def append_observation(self,sid,message):
        from engine.contracts import OBSERVATION
        from engine.core import digest
        from engine.cloud_repository import RepositoryConflict
        OBSERVATION.validate_python(message)
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS observations(session_id TEXT,message_id TEXT,sequence_no INTEGER,data TEXT,PRIMARY KEY(session_id,message_id))')
            old=c.execute('SELECT data FROM observations WHERE session_id=? AND message_id=?',(sid,message['message_id'])).fetchone()
            if old:
                if digest(json.loads(old['data']))!=digest(message):raise RepositoryConflict('observation_id_reused')
                return False
            c.execute('INSERT INTO observations VALUES (?,?,?,?)',(sid,message['message_id'],message['sequence_no'],json.dumps(message)))
        return True

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
