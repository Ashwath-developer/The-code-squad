import json
from agents.incident_agent import IncidentAnalysisAgent
from agents.location_agent import LocationIntelligenceAgent
from agents.communication_agent import EmergencyCommunicationAgent
from agents.monitoring_agent import MonitoringRecoveryAgent
from services.research_service import ResearchService

class AICoordinator:
    name = "AI Coordinator"

    def execute(self, db, incident_id, sms_mode="simulation", approval=False):
        def task(agent_name, task_name, status="running"):
            with db.connection() as conn:
                conn.execute("INSERT INTO agent_tasks(incident_id,agent_name,task_name,status,attempts) VALUES(?,?,?,?,1)",
                             (incident_id, agent_name, task_name, status))
                return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        def finish(task_id, status, result=None, error=None):
            with db.connection() as conn:
                conn.execute("UPDATE agent_tasks SET status=?,result=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                             (status, json.dumps(result) if result is not None else None, error, task_id))

        plan_task = task(self.name, "Create execution plan")
        finish(plan_task, "completed", {"plan": ["validate incident", "calculate recipients", "prepare notifications", "dispatch/approval gate", "monitor/retry", "report"]})

        t1 = task(IncidentAnalysisAgent.name, "Validate incident")
        assessment = IncidentAnalysisAgent().execute(db, incident_id)
        finish(t1, "completed" if assessment["valid"] else "failed", assessment)
        if not assessment["valid"]:
            with db.connection() as conn:
                conn.execute("UPDATE fire_incidents SET status='needs_correction' WHERE id=?", (incident_id,))
            return {"status": "needs_correction", "assessment": assessment}

        t2 = task(LocationIntelligenceAgent.name, "Calculate affected recipients")
        location = LocationIntelligenceAgent().execute(db, incident_id)
        finish(t2, "completed", location)

        research_task = task("Research Integration", "Retrieve emergency guidance")
        research = ResearchService().current_guidance()
        finish(research_task, "completed" if research["status"] != "degraded" else "failed", research)

        t3 = task(EmergencyCommunicationAgent.name, "Generate notifications")
        communication = EmergencyCommunicationAgent().execute(db, incident_id, location, sms_mode=sms_mode, approval=approval)
        finish(t3, "completed", communication)

        t4 = task(MonitoringRecoveryAgent.name, "Monitor and retry")
        monitoring = MonitoringRecoveryAgent().execute(db, incident_id, sms_mode=sms_mode)
        finish(t4, "completed", monitoring)

        with db.connection() as conn:
            conn.execute("UPDATE fire_incidents SET status=? WHERE id=?", ("awaiting_approval" if sms_mode == "real" and not approval else "monitored", incident_id))
            conn.execute("INSERT INTO agent_execution_logs(incident_id,agent_name,action,input_data,output_data,decision,tool_name,tool_status) VALUES(?,?,?,?,?,?,?,?)",
                         (incident_id, self.name, "Coordinate complete workflow", json.dumps({"sms_mode": sms_mode, "approval": approval}), json.dumps({"research": research["status"], "monitoring": monitoring}), "Workflow completed or recorded for human review", "Coordinator state machine", "success"))
        return {"status": "completed", "assessment": assessment, "location": location, "research": research,
                "communication": communication, "monitoring": monitoring}
