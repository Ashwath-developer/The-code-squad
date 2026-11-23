import os
import time
import sys

sys.path.insert(0, os.path.dirname(os.dirname(os.path.abspath(__file__))))

from config import Config
from services.database import Database
from agents.coordinator import AICoordinator

def main():
    db = Database(Config.DATABASE)
    db.initialize()
    queue = __import__('workers.job_queue', fromlist=['JobQueue']).JobQueue(db)

    def runner(incident_id, payload):
        return AICoordinator().execute(db, incident_id,
                                       sms_mode=payload.get("sms_mode", "simulation"),
                                       approval=payload.get("approval", False))

    print("QuickFire AI worker started. Checking persistent SQLite queue...")
    while True:
        queue.run_next(runner)
        time.sleep(2)

if __name__ == "__main__":
    main()
