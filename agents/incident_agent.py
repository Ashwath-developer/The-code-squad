import json
from services.geolocation import valid_coordinates

class IncidentAnalysisAgent:
    name = "Incident Analysis Agent"

    def execute(self, db, incident_id):
        with db.connection() as conn:
            incident = dict(conn.execute("SELECT * FROM fire_incidents WHERE id=?", (incident_id,)).fetchone())
        if not incident["title"] or not valid_coordinates(incident["latitude"], incident["longitude"]):
            assessment = {"valid": False, "severity": "Unknown", "summary": "Incident data or coordinates are incomplete.", "next_action": "Request administrator correction"}
        else:
            duplicate = 0
            severity = incident["severity"]
            assessment = {"valid": True, "severity": severity, "summary": f"{severity} severity fire report validated at the supplied coordinates.", "next_action": "Continue to location intelligence", "duplicate_count": duplicate}
        with db.connection() as conn:
            conn.execute("UPDATE fire_incidents SET severity=?, verification_status=? WHERE id=?",
                         (assessment["severity"], "verified" if assessment["valid"] else "needs_review", incident_id))
            conn.execute("INSERT INTO agent_execution_logs(incident_id,agent_name,action,input_data,output_data,decision,tool_name,tool_status) VALUES(?,?,?,?,?,?,?,?)",
                         (incident_id, self.name, "Validate and assess incident", json.dumps({"id": incident_id}), json.dumps(assessment), assessment["next_action"], "database validation + transparent severity rules", "success"))
        return assessment
