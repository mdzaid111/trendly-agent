import json, sqlite3, uuid
from datetime import datetime, timezone

class StateStore:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS sessions(
                session_id TEXT PRIMARY KEY, customer_id TEXT, created_at TEXT, updated_at TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT,
                content TEXT, tool_name TEXT, tool_call_id TEXT, created_at TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS actions(
                action_id TEXT PRIMARY KEY, session_id TEXT, customer_id TEXT, action_type TEXT,
                order_id TEXT, sku TEXT, status TEXT, payload TEXT, created_at TEXT)""")

    def create_session(self, customer_id=None):
        sid=str(uuid.uuid4()); now=datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO sessions VALUES(?,?,?,?)",(sid,customer_id,now,now))
        return sid

    def get_session(self,sid):
        with sqlite3.connect(self.path) as c:
            r=c.execute("SELECT session_id,customer_id,created_at,updated_at FROM sessions WHERE session_id=?",(sid,)).fetchone()
        return dict(zip(("session_id","customer_id","created_at","updated_at"),r)) if r else None

    def update_customer(self,sid,cid):
        now=datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE sessions SET customer_id=?,updated_at=? WHERE session_id=?",(cid,now,sid))

    def add_message(self,sid,role,content=None,tool_name=None,tool_call_id=None):
        now=datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO messages(session_id,role,content,tool_name,tool_call_id,created_at) VALUES(?,?,?,?,?,?)",
                      (sid,role,content,tool_name,tool_call_id,now))
            c.execute("UPDATE sessions SET updated_at=? WHERE session_id=?",(now,sid))

    def history(self,sid):
        with sqlite3.connect(self.path) as c:
            rows=c.execute("SELECT role,content,tool_name,tool_call_id FROM messages WHERE session_id=? ORDER BY id",(sid,)).fetchall()
        return [{"role":r,"content":content, **({"tool_name":tn} if tn else {}), **({"tool_call_id":tc} if tc else {})}
                for r,content,tn,tc in rows]

    def record_action(self,sid,cid,action_type,order_id,sku,status,payload):
        aid="ACT-"+uuid.uuid4().hex[:10].upper(); now=datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?)",
                      (aid,sid,cid,action_type,order_id,sku,status,json.dumps(payload),now))
        return aid
