import json

class ReportService:
    def generate(self, db, incident_id):
        with db.connection() as conn:
            incident = conn.execute("SELECT * FROM fire_incidents WHERE id=?", (incident_id,)).fetchone()
            tasks = [dict(r) for r in conn.execute("SELECT * FROM agent_tasks WHERE incident_id=? ORDER BY id", (incident_id,))]
            logs = [dict(r) for r in conn.execute("SELECT * FROM agent_execution_logs WHERE incident_id=? ORDER BY id", (incident_id,))]
            notifications = [dict(r) for r in conn.execute("SELECT * FROM notification_logs WHERE incident_id=? ORDER BY id", (incident_id,))]
        report = {
            "incident": dict(incident) if incident else None,
            "task_summary": {"total": len(tasks), "completed": sum(t["status"] == "completed" for t in tasks), "failed": sum(t["status"] == "failed" for t in tasks)},
            "notification_summary": {"generated": len(notifications), "success": sum(n["status"] == "success" for n in notifications), "failed": sum(n["status"] == "failed" for n in notifications)},
            "agent_execution_count": len(logs), "tasks": tasks, "logs": logs, "notifications": notifications,
            "prototype_notice": "QuickFire AI is a prototype and is not a certified emergency response or life-safety system."
        }
        with db.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO emergency_reports(incident_id, report_json, status) VALUES (?,?,?)", (incident_id, json.dumps(report), "generated"))
        return report
