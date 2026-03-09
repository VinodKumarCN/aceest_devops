from flask import Flask, jsonify, request, abort
import sqlite3
import os

app = Flask(__name__)
DB_NAME = os.environ.get("DB_PATH", "aceest_fitness.db")

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
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO clients (name, age, height, weight, program) VALUES (?, ?, ?, ?, ?)",
            (name, data.get("age"), data.get("height"), data.get("weight"), data.get("program"))
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

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)