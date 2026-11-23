from services.database import Database
import tempfile, os

def test_location_excludes_outside_radius():
    fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
    db=Database(path); db.initialize()
    with db.connection() as conn:
        conn.execute("INSERT INTO registered_users(name,phone,latitude,longitude,consent_sms) VALUES(?,?,?,?,1)",("Nearby","+919876543210",12.972,77.595))
        conn.execute("INSERT INTO registered_users(name,phone,latitude,longitude,consent_sms) VALUES(?,?,?,?,1)",("Far","+919876543211",13.0,77.7))
        conn.execute("INSERT INTO fire_incidents(title,latitude,longitude,radius_meters,severity) VALUES(?,?,?,?,?)",("Fire",12.9716,77.5946,1000,"High"))
        incident_id=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    from agents.location_agent import LocationIntelligenceAgent
    result=LocationIntelligenceAgent().execute(db,incident_id)
    assert len(result['eligible']) == 1
    assert len(result['excluded']) == 1
