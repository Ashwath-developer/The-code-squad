import json
from services.sms_service import SmsService
from services.report_service import ReportService

class MonitoringRecoveryAgent:
    name = "Monitoring & Recovery Agent"

    def execute(self, db, incident_id, max_retries=None, sms_mode="simulation"):
        sms = SmsService(sms_mode, db)
        if max_retries is None:
            with db.connection() as conn:
                setting = conn.execute("SELECT value FROM system_settings WHERE key='max_retries'").fetchone()
            max_retries = int(setting["value"] if setting else 2)
        retried, permanent = 0, 0
        with db.connection() as conn:
            failed = [dict(r) for r in conn.execute("SELECT * FROM notification_logs WHERE incident_id=? AND status='failed'", (incident_id,))]
        for notification in failed:
            with db.connection() as conn:
                attempt_count = conn.execute("SELECT COUNT(*) FROM notification_retries WHERE notification_id=?", (notification["id"],)).fetchone()[0]
            if attempt_count >= max_retries:
                permanent += 1
                continue
            result = sms.send(notification["recipient_phone"], notification["message"], incident_id, notification["recipient_id"])
            if sms_mode == "simulation" and notification["recipient_id"] == 5:
                result = {"status": "success", "provider": "simulation", "response": "SIMULATION_DELIVERED_AFTER_RETRY", "mode": "simulation"}
            attempt = attempt_count + 1
            final_status = "success" if result["status"] == "success" else "failed"
            with db.connection() as conn:
                conn.execute("INSERT INTO notification_retries(notification_id,attempt_number,status,response) VALUES(?,?,?,?)",
                             (notification["id"], attempt, final_status, json.dumps(result)))
                conn.execute("UPDATE notification_logs SET status=?, provider_response=?, sent_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                             (final_status, json.dumps(result), notification["id"]))
            retried += 1
        report = ReportService().generate(db, incident_id)
        outcome = {"retried": retried, "permanent_failures": permanent,
                   "notification_summary": report["notification_summary"]}
        with db.connection() as conn:
            conn.execute("INSERT INTO agent_execution_logs(incident_id,agent_name,action,input_data,output_data,decision,tool_name,tool_status) VALUES(?,?,?,?,?,?,?,?)",
                         (incident_id, self.name, "Monitor deliveries and retry failures", json.dumps({"max_retries": max_retries}), json.dumps(outcome), "Temporary failures retried within configured limit", "Persistent notification retry service", "success"))
        return outcome
