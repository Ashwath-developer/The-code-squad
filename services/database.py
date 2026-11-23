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
