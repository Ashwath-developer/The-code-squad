import os
import json
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
from config import Config
from services.database import Database
from workers.job_queue import JobQueue
from agents.coordinator import AICoordinator

app = Flask(__name__)
app.config.from_object(Config)
db = Database(app.config["DATABASE"])
db.initialize()
queue = JobQueue(db)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def seed_database():
    root = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.join(root, "database", "sample_data.sql")
    with db.connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
        if count == 0:
            admin_email = os.getenv("ADMIN_EMAIL") or "admin@quickfire.local"
            admin_password = os.getenv("ADMIN_PASSWORD") or "Admin@123"
            conn.execute("INSERT INTO admin_users(name,email,password_hash) VALUES(?,?,?)",
                         ("System Administrator", admin_email, generate_password_hash(admin_password)))
        user_count = conn.execute("SELECT COUNT(*) FROM registered_users").fetchone()[0]
        if user_count == 0:
            with open(sample_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())

seed_database()

@app.context_processor
def common():
    return {"current_admin": session.get("admin_name", "")}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with db.connection() as conn:
            admin = conn.execute("SELECT * FROM admin_users WHERE email=?", (email,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid administrator credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    with db.connection() as conn:
        stats = {
            "people": conn.execute("SELECT COUNT(*) FROM registered_users").fetchone()[0],
            "incidents": conn.execute("SELECT COUNT(*) FROM fire_incidents").fetchone()[0],
            "active": conn.execute("SELECT COUNT(*) FROM fire_incidents WHERE status!='resolved' AND status!='monitored'").fetchone()[0],
            "notifications": conn.execute("SELECT COUNT(*) FROM notification_logs").fetchone()[0],
            "success": conn.execute("SELECT COUNT(*) FROM notification_logs WHERE status='success'").fetchone()[0],
            "failed": conn.execute("SELECT COUNT(*) FROM notification_logs WHERE status='failed'").fetchone()[0],
            "tasks_running": conn.execute("SELECT COUNT(*) FROM agent_tasks WHERE status IN ('pending','running','retrying')").fetchone()[0],
        }
        incidents = [dict(r) for r in conn.execute("SELECT * FROM fire_incidents ORDER BY id DESC LIMIT 10")]
    return render_template("dashboard.html", stats=stats, incidents=incidents)

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        digits = phone.replace(" ", "").replace("-", "")
        if digits.startswith("00"):
            normalized = "+" + digits[2:]
        elif digits.startswith("+"):
            normalized = digits
        elif len(digits) == 10:
            normalized = "+91" + digits
        else:
            normalized = "+" + digits
        try:
            latitude = float(request.form.get("latitude") or 0)
            longitude = float(request.form.get("longitude") or 0)
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError
        except ValueError:
            latitude = longitude = None
        consent = 1 if request.form.get("consent") == "on" else 0
        if not name or not phone:
            flash("Name and phone are required.", "danger")
        elif not normalized.startswith("+") or len(normalized) < 9:
            flash("Enter a valid international phone number, such as +919876543210.", "danger")
        elif not consent:
            flash("SMS consent is required before registering the recipient.", "danger")
        else:
            with db.connection() as conn:
                duplicate = conn.execute("SELECT id FROM registered_users WHERE phone_normalized=?", (normalized,)).fetchone()
                if duplicate:
                    flash("This phone number is already registered.", "danger")
                else:
                    conn.execute("INSERT INTO registered_users(name,phone,phone_normalized,email,latitude,longitude,address,consent_sms,consent_recorded_at,active,invalid_location) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                 (name, normalized, normalized, email, latitude, longitude, address, consent, datetime.now(timezone.utc).isoformat(), 1, int(latitude is None or longitude is None)))
                    conn.execute("INSERT INTO audit_logs(actor,action,entity_type,details) VALUES(?,?,?,?)", (session["admin_name"], "register_recipient", "registered_user", json.dumps({"name": name, "phone": normalized, "consent": True})))
                    flash("Registered person and SMS consent recorded.", "success")
        return redirect(url_for("users"))
    with db.connection() as conn:
        people = [dict(r) for r in conn.execute("SELECT * FROM registered_users ORDER BY id DESC")]
    return render_template("users.html", people=people)

@app.route("/incident", methods=["GET", "POST"])
@login_required
def incident():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        severity = request.form.get("severity", "Medium")
        try:
            latitude = float(request.form["latitude"])
            longitude = float(request.form["longitude"])
            radius_value = request.form["radius"]
            radius = int(request.form.get("custom_radius", radius_value)) if radius_value == "custom" else int(radius_value)
            if radius < 100 or radius > 10000:
                raise ValueError("Radius must be between 100 and 10000 metres")
        except (KeyError, ValueError):
            flash("Please enter valid coordinates and radius.", "danger")
            return redirect(url_for("incident"))
        with db.connection() as conn:
            conn.execute("INSERT INTO fire_incidents(title,description,latitude,longitude,radius_meters,severity,reported_by,status) VALUES(?,?,?,?,?,?,?,?)",
                         (title, description, latitude, longitude, radius, severity, session["admin_id"], "reported"))
            incident_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        sms_mode = request.form.get("sms_mode", "simulation")
        approval = request.form.get("real_sms_approved") == "on"
        with db.connection() as conn:
            conn.execute("INSERT INTO audit_logs(actor,action,entity_type,entity_id,details) VALUES(?,?,?,?,?)", (session["admin_name"], "request_emergency_dispatch", "fire_incident", incident_id, json.dumps({"sms_mode": sms_mode, "approval": approval})))
        queue.enqueue(incident_id, sms_mode=sms_mode, approval=approval)
        # Run synchronously for a desktop demo; a separate worker can also consume the queue.
        queue.run_next(lambda iid, payload: AICoordinator().execute(db, iid, payload.get("sms_mode", "simulation"), payload.get("approval", False)))
        flash("Fire incident submitted and autonomous workflow started.", "success")
        return redirect(url_for("agents_view", incident_id=incident_id))
    return render_template("fire_alert.html")

@app.route("/map")
@login_required
def map_view():
    with db.connection() as conn:
        incidents = [dict(r) for r in conn.execute("SELECT * FROM fire_incidents ORDER BY id DESC")]
        people = [dict(r) for r in conn.execute("SELECT * FROM registered_users")]
    return render_template("map.html", incidents=incidents, people=people)

@app.route("/agents")
@login_required
def agents_view():
    incident_id = request.args.get("incident_id", type=int)
    with db.connection() as conn:
        incidents = [dict(r) for r in conn.execute("SELECT * FROM fire_incidents ORDER BY id DESC")]
        if incident_id:
            tasks = [dict(r) for r in conn.execute("SELECT * FROM agent_tasks WHERE incident_id=? ORDER BY id", (incident_id,))]
            logs = [dict(r) for r in conn.execute("SELECT * FROM agent_execution_logs WHERE incident_id=? ORDER BY id", (incident_id,))]
            notifications = [dict(r) for r in conn.execute("SELECT * FROM notification_logs WHERE incident_id=? ORDER BY id", (incident_id,))]
        else:
            tasks, logs, notifications = [], [], []
    return render_template("agents.html", incidents=incidents, incident_id=incident_id, tasks=tasks, logs=logs, notifications=notifications)

@app.route("/notifications")
@login_required
def notifications():
    with db.connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT n.*, r.name FROM notification_logs n JOIN registered_users r ON r.id=n.recipient_id ORDER BY n.id DESC")]
    return render_template("notifications.html", notifications=rows)

@app.route("/reports")
@login_required
def reports():
    with db.connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT r.*, i.title FROM emergency_reports r JOIN fire_incidents i ON i.id=r.incident_id ORDER BY r.id DESC")]
    return render_template("reports.html", reports=rows)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        try:
            max_retries = int(request.form.get("max_retries", 2))
            if max_retries < 0 or max_retries > 5:
                raise ValueError
        except ValueError:
            flash("Maximum retries must be from 0 to 5.", "danger")
            return redirect(url_for("settings"))
        with db.connection() as conn:
            conn.execute("INSERT INTO system_settings(key,value) VALUES('max_retries',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=CURRENT_TIMESTAMP", (str(max_retries),))
            conn.execute("INSERT INTO audit_logs(actor,action,entity_type,details) VALUES(?,?,?,?)", (session["admin_name"], "update_sms_retry_limit", "system_settings", json.dumps({"max_retries": max_retries})))
        flash("SMS retry limit updated.", "success")
        return redirect(url_for("settings"))

    with db.connection() as conn:
        setting = conn.execute("SELECT value FROM system_settings WHERE key='max_retries'").fetchone()
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    sender = os.getenv("TWILIO_FROM_NUMBER", "")
    return render_template("settings.html", max_retries=int(setting["value"] if setting else app.config["MAX_SMS_RETRIES"]), twilio_sid=bool(sid), twilio_token=bool(token), twilio_sender=sender, twilio_ready=bool(sid and token and sender))

@app.route("/api/sms/status", methods=["POST"])
def sms_status_callback():
    sid = request.form.get("MessageSid")
    delivery_status = request.form.get("MessageStatus")
    error_code = request.form.get("ErrorCode")
    if not sid:
        return jsonify({"status": "error", "message": "MessageSid is required"}), 400
    with db.connection() as conn:
        notification = conn.execute("SELECT id FROM notification_logs WHERE provider_response LIKE ?", (f'%{sid}%',)).fetchone()
        if not notification:
            return jsonify({"status": "not_found"}), 404
        status = "success" if delivery_status in ("delivered",) else ("failed" if delivery_status in ("failed", "undelivered") else "pending")
        conn.execute("UPDATE notification_logs SET status=?,provider_response=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, json.dumps({"sid": sid, "delivery_status": delivery_status, "error_code": error_code}), notification["id"]))
    return jsonify({"status": "updated", "delivery_status": delivery_status})

@app.route("/api/incidents/<int:incident_id>")
@login_required
def incident_api(incident_id):
    with db.connection() as conn:
        incident = conn.execute("SELECT * FROM fire_incidents WHERE id=?", (incident_id,)).fetchone()
        tasks = [dict(r) for r in conn.execute("SELECT * FROM agent_tasks WHERE incident_id=? ORDER BY id", (incident_id,))]
        logs = [dict(r) for r in conn.execute("SELECT * FROM agent_execution_logs WHERE incident_id=? ORDER BY id", (incident_id,))]
    return jsonify({"incident": dict(incident) if incident else None, "tasks": tasks, "logs": logs})

@app.route("/api/geocode")
@login_required
def geocode_api():
    import requests
    address = request.args.get("address", "")
    if not address:
        return jsonify({"status": "error", "message": "Address required"}), 400
    try:
        response = requests.get("https://nominatim.openstreetmap.org/search", params={"q": address, "format": "json", "limit": 1}, headers={"User-Agent": "QuickFireAI/1.0"}, timeout=10)
        response.raise_for_status()
        items = response.json()
        if not items:
            return jsonify({"status": "unavailable", "message": "No geocoding result"})
        item = items[0]
        return jsonify({"status": "success", "latitude": item["lat"], "longitude": item["lon"], "display_name": item["display_name"]})
    except requests.RequestException as exc:
        return jsonify({"status": "degraded", "message": str(exc)[:300]})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
