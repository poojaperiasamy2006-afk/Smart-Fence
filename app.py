from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)

# Change this to any random secret string
app.secret_key = "smartfence_secret_2026"

DATABASE = "database.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================
# LOGIN REQUIRED
# =========================

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# =========================
# DATABASE CREATION
# =========================

def create_database():

    connection = get_db_connection()

    # Users table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # Sensor table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battery INTEGER,
            voltage REAL,
            animal_detected INTEGER,
            timestamp TEXT
        )
    """)

    # Alerts table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            alert_type TEXT,
            timestamp TEXT
        )
    """)

    # Fence status table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS fence_status (
            id INTEGER PRIMARY KEY,
            status TEXT,
            updated_at TEXT
        )
    """)

    existing = connection.execute("""
        SELECT *
        FROM fence_status
        WHERE id = 1
    """).fetchone()

    if existing is None:

        connection.execute("""
            INSERT INTO fence_status
            (id, status, updated_at)
            VALUES (1, 'ON', ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))

    connection.commit()
    connection.close()


# =========================
# AI SENSOR ANALYSIS
# =========================

def analyze_sensor(voltage, battery, animal_detected):

    if animal_detected:

        return {
            "status": "WILDLIFE ALERT",
            "level": "warning",
            "icon": "🐾",
            "message": "Animal movement detected near the fence."
        }

    if voltage < 6.0:

        return {
            "status": "CRITICAL",
            "level": "critical",
            "icon": "🚨",
            "message": "Critical voltage drop detected."
        }

    if voltage < 7.0:

        return {
            "status": "WARNING",
            "level": "warning",
            "icon": "⚠️",
            "message": "Unusual voltage drop detected."
        }

    if battery < 70:

        return {
            "status": "LOW BATTERY",
            "level": "warning",
            "icon": "🔋",
            "message": "Sensor battery level is getting low."
        }

    return {
        "status": "NORMAL",
        "level": "safe",
        "icon": "🛡️",
        "message": "Fence condition is normal. No abnormal pattern detected."
    }


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        connection = get_db_connection()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        if password != confirm_password:

            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        connection = get_db_connection()

        existing_user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if existing_user:

            connection.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )

        hashed_password = generate_password_hash(password)

        connection.execute("""
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================

@app.route("/")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        user_email=session.get("user_email")
    )


# =========================
# ALERTS PAGE
# =========================

@app.route("/alerts")
@login_required
def alerts():

    return render_template("alerts.html")


# =========================
# HISTORY PAGE
# =========================

@app.route("/history")
@login_required
def history_page():

    return render_template("history.html")


# =========================
# SENSOR API
# =========================

@app.route("/api/sensor")
@login_required
def sensor_data():

    battery = random.randint(75, 96)

    voltage = round(
        random.uniform(6.2, 8.5),
        1
    )

    animal_detected = random.random() < 0.15

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    analysis = analyze_sensor(
        voltage,
        battery,
        animal_detected
    )

    connection = get_db_connection()

    connection.execute("""
        INSERT INTO sensor_data
        (
            battery,
            voltage,
            animal_detected,
            timestamp
        )
        VALUES (?, ?, ?, ?)
    """, (
        battery,
        voltage,
        int(animal_detected),
        timestamp
    ))

    if animal_detected:

        connection.execute("""
            INSERT INTO alerts
            (
                message,
                alert_type,
                timestamp
            )
            VALUES (?, ?, ?)
        """, (
            "Animal movement detected near the fence!",
            "warning",
            timestamp
        ))

    elif voltage < 6.0:

        connection.execute("""
            INSERT INTO alerts
            (
                message,
                alert_type,
                timestamp
            )
            VALUES (?, ?, ?)
        """, (
            "Critical fence voltage detected!",
            "critical",
            timestamp
        ))

    elif voltage < 7.0:

        connection.execute("""
            INSERT INTO alerts
            (
                message,
                alert_type,
                timestamp
            )
            VALUES (?, ?, ?)
        """, (
            "Low fence voltage detected!",
            "warning",
            timestamp
        ))

    connection.commit()
    connection.close()

    return jsonify({
        "battery": battery,
        "voltage": voltage,
        "animal_detected": animal_detected,
        "timestamp": timestamp,
        "ai_analysis": analysis
    })


# =========================
# FOREST ZONES
# =========================

@app.route("/api/zones")
@login_required
def get_zones():

    zones = []

    zone_names = [
        "North Forest",
        "Central Forest",
        "South Forest"
    ]

    for i, name in enumerate(zone_names, start=1):

        voltage = round(
            random.uniform(6.2, 8.5),
            1
        )

        battery = random.randint(75, 96)

        animal = random.random() < 0.18

        if voltage < 6.0:

            status = "Critical"

        elif voltage < 7.0:

            status = "Warning"

        elif animal:

            status = "Animal Detected"

        else:

            status = "Safe"

        zones.append({
            "id": i,
            "name": name,
            "voltage": voltage,
            "battery": battery,
            "animal_detected": animal,
            "status": status
        })

    return jsonify(zones)


# =========================
# FENCE STATUS
# =========================

@app.route("/api/fence", methods=["GET"])
@login_required
def get_fence_status():

    connection = get_db_connection()

    fence = connection.execute("""
        SELECT *
        FROM fence_status
        WHERE id = 1
    """).fetchone()

    connection.close()

    return jsonify({
        "status": fence["status"],
        "updated_at": fence["updated_at"]
    })


# =========================
# CHANGE FENCE STATUS
# =========================

@app.route("/api/fence", methods=["POST"])
@login_required
def change_fence_status():

    data = request.get_json()

    new_status = data.get("status")

    if new_status not in ["ON", "OFF"]:

        return jsonify({
            "success": False,
            "message": "Invalid fence status"
        }), 400

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_db_connection()

    connection.execute("""
        UPDATE fence_status
        SET status = ?,
            updated_at = ?
        WHERE id = 1
    """, (
        new_status,
        timestamp
    ))

    if new_status == "ON":

        message = "Fence system turned ON."
        alert_type = "info"

    else:

        message = "Fence system turned OFF."
        alert_type = "warning"

    connection.execute("""
        INSERT INTO alerts
        (
            message,
            alert_type,
            timestamp
        )
        VALUES (?, ?, ?)
    """, (
        message,
        alert_type,
        timestamp
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "status": new_status,
        "message": message,
        "timestamp": timestamp
    })


# =========================
# EMERGENCY SHUTDOWN
# =========================

@app.route("/api/emergency", methods=["POST"])
@login_required
def emergency_shutdown():

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_db_connection()

    connection.execute("""
        UPDATE fence_status
        SET status = 'OFF',
            updated_at = ?
        WHERE id = 1
    """, (
        timestamp,
    ))

    connection.execute("""
        INSERT INTO alerts
        (
            message,
            alert_type,
            timestamp
        )
        VALUES (?, ?, ?)
    """, (
        "Emergency shutdown activated!",
        "critical",
        timestamp
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "status": "OFF",
        "message": "Emergency shutdown activated!",
        "timestamp": timestamp
    })


# =========================
# ALERT API
# =========================

@app.route("/api/alerts")
@login_required
def get_alerts():

    connection = get_db_connection()

    alerts = connection.execute("""
        SELECT *
        FROM alerts
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    connection.close()

    return jsonify([
        dict(alert)
        for alert in alerts
    ])


# =========================
# SENSOR HISTORY API
# =========================

@app.route("/api/history")
@login_required
def history():

    connection = get_db_connection()

    history_data = connection.execute("""
        SELECT *
        FROM sensor_data
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()

    connection.close()

    return jsonify([
        dict(row)
        for row in history_data
    ])


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    create_database()

    print("")
    print("======================================")
    print("🌲 SMARTFENCE")
    print("🌿 Forest Monitoring System")
    print("🔐 Authentication Enabled")
    print("🤖 AI Anomaly Detection Enabled")
    print("======================================")
    print("")

    app.run(debug=True)