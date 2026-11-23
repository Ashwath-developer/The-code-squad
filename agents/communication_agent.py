import json
from services.sms_service import SmsService

class EmergencyCommunicationAgent:
    name = "Emergency Communication Agent"

    def execute(self, db, incident_id, location_result, sms_mode="simulation", approval=False):
        with db.connection() as conn:
            incident = dict(conn.execute("SELECT * FROM fire_incidents WHERE id=?", (incident_id,)).fetchone())
        sms = SmsService(sms_mode, db)
        generated = 0
        for person in location_result["eligible"]:
            message = f"QUICKFIRE EMERGENCY: {incident['title']}. Severity: {incident['severity']}. Location: {incident['latitude']}, {incident['longitude']}. Leave the area and follow authorities. Prototype alert."
            with db.connection() as conn:
                existing = conn.execute("SELECT id FROM notification_logs WHERE incident_id=? AND recipient_id=?", (incident_id, person["id"])).fetchone()
                if existing:
                    continue
                conn.execute("INSERT INTO notification_logs(incident_id,recipient_id,recipient_phone,message,mode,status,provider_response) VALUES(?,?,?,?,?,?,?)",
                             (incident_id, person["id"], person["phone"], message, sms_mode, "pending", "queued for dispatch"))
                notification_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            generated += 1

            if sms_mode == "real" and not approval:
                outcome = {"status": "blocked", "provider": "human approval", "response": "Real SMS requires administrator approval"}
            else:
                outcome = sms.send(person["phone"], message, incident_id, person["id"])
                if sms_mode == "simulation": outcome["mode"] = "simulation"

            status = outcome["status"]
            stored_status = "failed" if status == "failed" else ("pending" if status == "blocked" else "accepted")
            with db.connection() as conn:
                conn.execute("UPDATE notification_logs SET status=?, provider_response=?, sent_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                             (stored_status, json.dumps(outcome), notification_id))

        with db.connection() as conn:
            conn.execute("INSERT INTO agent_execution_logs(incident_id,agent_name,action,input_data,output_data,decision,tool_name,tool_status) VALUES(?,?,?,?,?,?,?,?)",
                         (incident_id, self.name, "Generate and dispatch notifications", json.dumps({"sms_mode": sms_mode, "approval": approval}), json.dumps({"generated": generated}), "Duplicate-safe notification plan executed", "SMS service", "success"))
        return {"generated": generated}
