from flask import Flask, jsonify, request, abort
import sqlite3
import os
from datetime import datetime
# Final version - all endpoints tested and documented
app = Flask(__name__)

DB_NAME = os.environ.get("DB_PATH", "aceest_fitness.db")

PROGRAMS = {
    "Fat Loss (FL)": {
        "factor": 22,
        "workout": (
            "Mon: Back Squat 5x5 + Core\n"
            "Tue: EMOM 20min Assault Bike\n"
            "Wed: Bench Press + 21-15-9\n"
            "Thu: Deadlift + Box Jumps\n"
            "Fri: Zone 2 Cardio 30min"
        ),
        "diet": (
            "Breakfast: Egg Whites + Oats\n"
            "Lunch: Grilled Chicken + Brown Rice\n"
            "Dinner: Fish Curry + Millet Roti\n"
            "Target: ~2000 kcal"
        ),
    },
    "Muscle Gain (MG)": {
        "factor": 35,
        "workout": (
            "Mon: Squat 5x5\n"
            "Tue: Bench 5x5\n"
            "Wed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\n"
            "Fri: Incline Press 4x10\n"
            "Sat: Barbell Rows 4x10"
        ),
        "diet": (
            "Breakfast: Eggs + Peanut Butter Oats\n"
            "Lunch: Chicken Biryani\n"
            "Dinner: Mutton Curry + Rice\n"
            "Target: ~3200 kcal"
        ),
    },
    "Beginner (BG)": {
        "factor": 26,
        "workout": (
            "Full Body Circuit:\n"
            "- Air Squats\n"
            "- Ring Rows\n"
            "- Push-ups\n"
            "Focus: Technique & Consistency"
        ),
        "diet": (
            "Balanced Tamil Meals\n"
            "Idli / Dosa / Rice + Dal\n"
            "Protein Target: 120g/day"
        ),
    },
}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            target_adherence INTEGER,
            membership_status TEXT DEFAULT 'Active'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week TEXT,
            adherence INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------- HEALTH ----------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "aceest-fitness"})


# ---------- PROGRAMS ----------

@app.route("/programs", methods=["GET"])
def list_programs():
    result = {}
    for name, data in PROGRAMS.items():
        result[name] = {
            "calorie_factor": data["factor"],
            "workout_plan": data["workout"],
            "diet_plan": data["diet"],
        }
    return jsonify(result)


@app.route("/programs/<program_name>", methods=["GET"])
def get_program(program_name):
    if program_name not in PROGRAMS:
        abort(404, description=f"Program '{program_name}' not found")
    data = PROGRAMS[program_name]
    return jsonify({
        "name": program_name,
        "calorie_factor": data["factor"],
        "workout_plan": data["workout"],
        "diet_plan": data["diet"],
    })


# ---------- CLIENTS ----------

@app.route("/clients", methods=["GET"])
def list_clients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        abort(400, description="Client name is required")

    program = data.get("program", "")
    age = data.get("age")
    height = data.get("height")
    weight = data.get("weight")
    target_weight = data.get("target_weight")
    target_adherence = data.get("target_adherence")

    calories = None
    if weight and program in PROGRAMS:
        calories = int(float(weight) * PROGRAMS[program]["factor"])

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO clients
                (name, age, height, weight, program, calories, target_weight, target_adherence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, age, height, weight, program, calories, target_weight, target_adherence),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        abort(409, description=f"Client '{name}' already exists")
    finally:
        conn.close()


@app.route("/clients/<name>", methods=["GET"])
def get_client(name):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if row is None:
        abort(404, description=f"Client '{name}' not found")
    return jsonify(dict(row))


@app.route("/clients/<name>", methods=["PUT"])
def update_client(name):
    conn = get_db()
    existing = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if existing is None:
        conn.close()
        abort(404, description=f"Client '{name}' not found")

    data = request.get_json(force=True)
    age = data.get("age", existing["age"])
    height = data.get("height", existing["height"])
    weight = data.get("weight", existing["weight"])
    program = data.get("program", existing["program"])
    target_weight = data.get("target_weight", existing["target_weight"])
    target_adherence = data.get("target_adherence", existing["target_adherence"])
    membership_status = data.get("membership_status", existing["membership_status"])

    calories = existing["calories"]
    if weight and program in PROGRAMS:
        calories = int(float(weight) * PROGRAMS[program]["factor"])

    conn.execute(
        """
        UPDATE clients
        SET age=?, height=?, weight=?, program=?, calories=?,
            target_weight=?, target_adherence=?, membership_status=?
        WHERE name=?
        """,
        (age, height, weight, program, calories,
         target_weight, target_adherence, membership_status, name),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    return jsonify(dict(row))


@app.route("/clients/<name>", methods=["DELETE"])
def delete_client(name):
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE name=?", (name,)).fetchone()
    if existing is None:
        conn.close()
        abort(404, description=f"Client '{name}' not found")
    conn.execute("DELETE FROM clients WHERE name=?", (name,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Client '{name}' deleted successfully"})


# ---------- CALORIES ----------

@app.route("/clients/<name>/calories", methods=["GET"])
def calculate_calories(name):
    conn = get_db()
    row = conn.execute(
        "SELECT weight, program FROM clients WHERE name=?", (name,)
    ).fetchone()
    conn.close()
    if row is None:
        abort(404, description=f"Client '{name}' not found")
    weight = row["weight"]
    program = row["program"]
    if not weight or program not in PROGRAMS:
        abort(400, description="Weight and a valid program are required to calculate calories")
    calories = int(float(weight) * PROGRAMS[program]["factor"])
    return jsonify({"client": name, "program": program, "estimated_calories": calories})


# ---------- PROGRESS ----------

@app.route("/clients/<name>/progress", methods=["GET"])
def get_progress(name):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/clients/<name>/progress", methods=["POST"])
def log_progress(name):
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE name=?", (name,)).fetchone()
    if existing is None:
        conn.close()
        abort(404, description=f"Client '{name}' not found")

    data = request.get_json(force=True)
    adherence = data.get("adherence")
    if adherence is None:
        conn.close()
        abort(400, description="'adherence' field is required")

    week = data.get("week") or datetime.now().strftime("Week %U - %Y")
    conn.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
        (name, week, int(adherence)),
    )
    conn.commit()
    conn.close()
    return jsonify({"client": name, "week": week, "adherence": int(adherence)}), 201


# ---------- WORKOUTS ----------

@app.route("/clients/<name>/workouts", methods=["GET"])
def get_workouts(name):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (name,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/clients/<name>/workouts", methods=["POST"])
def log_workout(name):
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE name=?", (name,)).fetchone()
    if existing is None:
        conn.close()
        abort(404, description=f"Client '{name}' not found")

    data = request.get_json(force=True)
    workout_type = (data.get("workout_type") or "").strip()
    if not workout_type:
        conn.close()
        abort(400, description="'workout_type' is required")

    w_date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    duration = data.get("duration_min", 60)
    notes = data.get("notes", "")

    conn.execute(
        """
        INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, w_date, workout_type, duration, notes),
    )
    conn.commit()
    conn.close()
    return jsonify({
        "client": name,
        "date": w_date,
        "workout_type": workout_type,
        "duration_min": duration,
    }), 201


# ---------- BMI ----------

@app.route("/clients/<name>/bmi", methods=["GET"])
def get_bmi(name):
    conn = get_db()
    row = conn.execute(
        "SELECT height, weight FROM clients WHERE name=?", (name,)
    ).fetchone()
    conn.close()
    if row is None:
        abort(404, description=f"Client '{name}' not found")

    height = row["height"]
    weight = row["weight"]
    if not height or not weight or float(height) <= 0:
        abort(400, description="Valid height and weight are required to compute BMI")

    h_m = float(height) / 100.0
    bmi = round(float(weight) / (h_m * h_m), 1)

    if bmi < 18.5:
        category, risk = "Underweight", "Potential nutrient deficiency"
    elif bmi < 25:
        category, risk = "Normal", "Low risk if active and consistent"
    elif bmi < 30:
        category, risk = "Overweight", "Moderate risk; focus on adherence"
    else:
        category, risk = "Obese", "Higher risk; prioritise fat loss and supervision"

    return jsonify({"client": name, "bmi": bmi, "category": category, "risk_note": risk})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
