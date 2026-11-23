import json
from services.geolocation import haversine_meters

class LocationIntelligenceAgent:
    name = "Location Intelligence Agent"

    def execute(self, db, incident_id):
        with db.connection() as conn:
            incident = dict(conn.execute("SELECT * FROM fire_incidents WHERE id=?", (incident_id,)).fetchone())
            people = [dict(r) for r in conn.execute("SELECT * FROM registered_users")]

        eligible, excluded = [], []
        for person in people:
            lat, lon = person["latitude"], person["longitude"]
            if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                excluded.append({**person, "reason": "missing_or_invalid_location", "distance_meters": None})
                continue
            distance = haversine_meters(incident["latitude"], incident["longitude"], lat, lon)
            item = {**person, "distance_meters": round(distance, 1)}
            if distance <= incident["radius_meters"] and person["consent_sms"]:
                eligible.append(item)
            else:
                item["reason"] = "outside_radius" if distance > incident["radius_meters"] else "consent_not_given"
                excluded.append(item)

        result = {"eligible": eligible, "excluded": excluded, "radius_meters": incident["radius_meters"],
                  "eligible_count": len(eligible), "map": {"latitude": incident["latitude"], "longitude": incident["longitude"]}}
        with db.connection() as conn:
            conn.execute("INSERT INTO agent_execution_logs(incident_id,agent_name,action,input_data,output_data,decision,tool_name,tool_status) VALUES(?,?,?,?,?,?,?,?)",
                         (incident_id, self.name, "Calculate radius recipients", json.dumps({"radius_meters": incident["radius_meters"]}), json.dumps(result), f"Selected {len(eligible)} eligible recipients", "Haversine distance calculation", "success"))
        return result
