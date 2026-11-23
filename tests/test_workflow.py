import os
import tempfile
from services.database import Database
from agents.coordinator import AICoordinator

def make_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    db.initialize()
    with db.connection() as conn:
        conn.execute("INSERT INTO registered_users(name,phone,latitude,longitude,consent_sms) VALUES(?,?,?,?,1)", ("Test Person", "+919876543210", 12.972, 77.595))
    return db

def test_complete_simulation_workflow():
    db = make_db()
    with db.connection() as conn:
        conn.execute("INSERT INTO fire_incidents(title,latitude,longitude,radius_meters,severity,status) VALUES(?,?,?,?,?,?)", ("Campus Fire", 12.9716, 77.5946, 1000, "High", "reported"))
        incident_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    result = AICoordinator().execute(db, incident_id, sms_mode="simulation", approval=True)
    assert result["status"] == "completed"
    assert result["location"]["eligible_count"] >= 1
