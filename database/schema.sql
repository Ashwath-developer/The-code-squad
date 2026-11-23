CREATE TABLE IF NOT EXISTS admin_users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS registered_users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT,
 latitude REAL, longitude REAL, consent_sms INTEGER NOT NULL DEFAULT 1,
 invalid_location INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS fire_incidents (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT,
 latitude REAL NOT NULL, longitude REAL NOT NULL, radius_meters INTEGER NOT NULL,
 severity TEXT NOT NULL DEFAULT 'Medium', status TEXT NOT NULL DEFAULT 'reported',
 verification_status TEXT NOT NULL DEFAULT 'pending', reported_by INTEGER,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(reported_by) REFERENCES admin_users(id)
);
CREATE TABLE IF NOT EXISTS agent_tasks (
 id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id INTEGER, agent_name TEXT NOT NULL,
 task_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', payload TEXT,
 result TEXT, error TEXT, attempts INTEGER NOT NULL DEFAULT 0,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(incident_id) REFERENCES fire_incidents(id)
);
CREATE TABLE IF NOT EXISTS agent_execution_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id INTEGER, agent_name TEXT NOT NULL,
 action TEXT NOT NULL, input_data TEXT, output_data TEXT, decision TEXT,
 tool_name TEXT, tool_status TEXT, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(incident_id) REFERENCES fire_incidents(id)
);
CREATE TABLE IF NOT EXISTS notification_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id INTEGER NOT NULL, recipient_id INTEGER NOT NULL,
 recipient_phone TEXT NOT NULL, message TEXT NOT NULL, mode TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', provider_response TEXT,
 sent_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(incident_id, recipient_id), FOREIGN KEY(incident_id) REFERENCES fire_incidents(id),
 FOREIGN KEY(recipient_id) REFERENCES registered_users(id)
);
CREATE TABLE IF NOT EXISTS notification_retries (
 id INTEGER PRIMARY KEY AUTOINCREMENT, notification_id INTEGER NOT NULL, attempt_number INTEGER NOT NULL,
 status TEXT NOT NULL, response TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(notification_id) REFERENCES notification_logs(id)
);
CREATE TABLE IF NOT EXISTS emergency_reports (
 id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id INTEGER NOT NULL UNIQUE, report_json TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'generated', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(incident_id) REFERENCES fire_incidents(id)
);
CREATE TABLE IF NOT EXISTS system_settings (
 key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT NOT NULL, action TEXT NOT NULL,
 entity_type TEXT, entity_id INTEGER, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON fire_incidents(status);
CREATE INDEX IF NOT EXISTS idx_tasks_incident ON agent_tasks(incident_id);
CREATE INDEX IF NOT EXISTS idx_notifications_incident ON notification_logs(incident_id);
