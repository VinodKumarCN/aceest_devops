from flask import Flask, jsonify, request, abort
import sqlite3
import os

app = Flask(__name__)
DB_NAME = os.environ.get("DB_PATH", "aceest_fitness.db")

PROGRAMS = {
    "Fat Loss (FL)": {
        "factor": 22,
        "workout": "Mon: Back Squat 5x5\nTue: EMOM Assault Bike\nWed: Bench Press\nThu: Deadlift\nFri: Zone 2 Cardio",
        "diet": "Breakfast: Egg Whites + Oats\nLunch: Grilled Chicken + Rice\nDinner: Fish Curry\nTarget: ~2000 kcal"
    },
    "Muscle Gain (MG)": {
        "factor": 35,
        "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\nThu: Front Squat\nFri: Incline Press\nSat: Barbell Rows",
        "diet": "Breakfast: Eggs + Oats\nLunch: Chicken Biryani\nDinner: Mutton Curry\nTarget: ~3200 kcal"
    },
    "Beginner (BG)": {
        "factor": 26,
        "workout": "Full Body Circuit:\n- Air Squats\n- Ring Rows\n- Push-ups\nFocus: Technique",
        "diet": "Balanced Meals\nIdli / Dosa / Rice + Dal\nProtein: 120g/day"
    }
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
            membership_status TEXT DEFAULT 'Active'
        )
    """)
    conn.commit()
    conn.close()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "aceest-fitness"})

@app.route("/programs", methods=["GET"])
def list_programs():
    result = {}
    for name, data in PROGRAMS.items():
        result[name] = {
            "calorie_factor": data["factor"],
            "workout_plan": data["workout"],
            "diet_plan": data["diet"]
        }
    return jsonify(result)

@app.route("/programs/<program_name>", methods=["GET"])
def get_program(program_name):
    if program_name not in PROGRAMS:
        abort(404, description=f"Program '{program_name}' not found")
    data = PROGRAMS[program_name]
    return jsonify({"name": program_name, "calorie_factor": data["factor"],
                    "workout_plan": data["workout"], "diet_plan": data["diet"]})

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
    weight = data.get("weight")
    calories = None
    if weight and program in PROGRAMS:
        calories = int(float(weight) * PROGRAMS[program]["factor"])
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO clients (name, age, height, weight, program, calories) VALUES (?, ?, ?, ?, ?, ?)",
            (name, data.get("age"), data.get("height"), weight, program, calories)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError:
        abort(409, description=f"Client '{name}' already exists")
    finally:
        conn.close()

@app.route("/clients/<n>", methods=["GET"])
def get_client(n):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (n,)).fetchone()
    conn.close()
    if row is None:
        abort(404, description=f"Client '{n}' not found")
    return jsonify(dict(row))

@app.route("/clients/<n>", methods=["DELETE"])
def delete_client(n):
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE name=?", (n,)).fetchone()
    if existing is None:
        conn.close()
        abort(404, description=f"Client '{n}' not found")
    conn.execute("DELETE FROM clients WHERE name=?", (n,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Client '{n}' deleted"})

@app.route("/clients/<n>/calories", methods=["GET"])
def calculate_calories(n):
    conn = get_db()
    row = conn.execute("SELECT weight, program FROM clients WHERE name=?", (n,)).fetchone()
    conn.close()
    if row is None:
        abort(404, description=f"Client '{n}' not found")
    if not row["weight"] or row["program"] not in PROGRAMS:
        abort(400, description="Valid weight and program required")
    calories = int(float(row["weight"]) * PROGRAMS[row["program"]]["factor"])
    return jsonify({"client": n, "program": row["program"], "estimated_calories": calories})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)