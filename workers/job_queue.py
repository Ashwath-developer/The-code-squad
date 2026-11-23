import json
from threading import Lock

class JobQueue:
    """Lightweight persistent SQLite-backed queue. Jobs survive web server restarts."""
    def __init__(self, db):
        self.db = db
        self.lock = Lock()

    def enqueue(self, incident_id, sms_mode="simulation", approval=False):
        with self.db.connection() as conn:
            conn.execute("INSERT INTO agent_tasks(incident_id,agent_name,task_name,status,payload,attempts) VALUES(?,?,?,?,?,0)",
                         (incident_id, "Persistent Worker", "Execute coordinated workflow", "pending", json.dumps({"sms_mode": sms_mode, "approval": approval})))
            task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return task_id

    def run_next(self, runner):
        with self.lock:
            with self.db.connection() as conn:
                row = conn.execute("SELECT * FROM agent_tasks WHERE agent_name='Persistent Worker' AND task_name='Execute coordinated workflow' AND status='pending' ORDER BY id LIMIT 1").fetchone()
                if not row:
                    return None
                conn.execute("UPDATE agent_tasks SET status='running',attempts=attempts+1,updated_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
            try:
                payload = json.loads(row["payload"] or "{}")
                result = runner(row["incident_id"], payload)
                with self.db.connection() as conn:
                    conn.execute("UPDATE agent_tasks SET status='completed',result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps(result), row["id"]))
                return result
            except Exception as exc:
                with self.db.connection() as conn:
                    conn.execute("UPDATE agent_tasks SET status='failed',error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (str(exc)[:500], row["id"]))
                raise
