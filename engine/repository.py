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
