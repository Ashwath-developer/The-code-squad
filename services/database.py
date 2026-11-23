import sqlite3
import os
from contextlib import contextmanager

SCHEMA = "database/schema.sql"

class Database:
    def __init__(self, path):
        self.path = path

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def initialize(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_path = os.path.join(root, SCHEMA)
        with self.connect() as conn:
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(registered_users)")}
            migrations = {
                "address": "ALTER TABLE registered_users ADD COLUMN address TEXT",
                "consent_recorded_at": "ALTER TABLE registered_users ADD COLUMN consent_recorded_at TEXT",
                "active": "ALTER TABLE registered_users ADD COLUMN active INTEGER NOT NULL DEFAULT 1",
                "phone_normalized": "ALTER TABLE registered_users ADD COLUMN phone_normalized TEXT",
            }
            for column, statement in migrations.items():
                if column not in columns:
                    conn.execute(statement)
            conn.execute("UPDATE registered_users SET phone_normalized=phone WHERE phone_normalized IS NULL")
            conn.execute("UPDATE registered_users SET invalid_location=1 WHERE latitude IS NULL OR longitude IS NULL OR (latitude=0 AND longitude=0)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_registered_users_phone ON registered_users(phone_normalized)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_registered_users_location ON registered_users(latitude, longitude)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_registered_users_active ON registered_users(active)")
            existing_people = conn.execute("SELECT id, phone, phone_normalized FROM registered_users").fetchall()
            for person in existing_people:
                phone = str(person["phone"] or "").strip().replace(" ", "").replace("-", "")
                if phone.startswith("00"):
                    normalized = "+" + phone[2:]
                elif phone.startswith("+"):
                    normalized = phone
                elif len(phone) == 10:
                    normalized = "+91" + phone
                else:
                    normalized = phone
                conn.execute("UPDATE registered_users SET phone_normalized=?,phone=? WHERE id=?", (normalized, normalized, person["id"]))
            conn.execute("UPDATE registered_users SET invalid_location=1 WHERE latitude IS NULL OR longitude IS NULL OR (latitude=0 AND longitude=0)")

    @contextmanager
    def connection(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def dict_rows(rows):
    return [dict(row) for row in rows]
