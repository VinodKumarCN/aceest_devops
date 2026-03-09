"""
Unit tests for ACEest Fitness & Gym Flask API.
Run with:  pytest tests/test_app.py -v
"""
import os
import pytest
import tempfile
# Tests for calorie, BMI, progress and workout endpoints
# Use an isolated temp database for tests so they never touch the real DB.
os.environ["DB_PATH"] = tempfile.mktemp(suffix=".db")

from app import app, init_db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Wipe and re-initialise the database before every test so each test is isolated."""
    import sqlite3
    conn = sqlite3.connect(os.environ.get("DB_PATH", "aceest_fitness.db"))
    cur = conn.cursor()
    # Drop all tables so every test starts with a clean slate
    cur.execute("DROP TABLE IF EXISTS clients")
    cur.execute("DROP TABLE IF EXISTS progress")
    cur.execute("DROP TABLE IF EXISTS workouts")
    conn.commit()
    conn.close()
    init_db()
    yield


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------- /health ----------

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert body["service"] == "aceest-fitness"


# ---------- /programs ----------

def test_list_programs_returns_three_programs(client):
    r = client.get("/programs")
    assert r.status_code == 200
    programs = r.get_json()
    assert len(programs) == 3
    assert "Fat Loss (FL)" in programs
    assert "Muscle Gain (MG)" in programs
    assert "Beginner (BG)" in programs


def test_get_program_returns_details(client):
    r = client.get("/programs/Fat Loss (FL)")
    assert r.status_code == 200
    data = r.get_json()
    assert data["calorie_factor"] == 22
    assert "Squat" in data["workout_plan"] or "Squat" in data["workout_plan"]


def test_get_program_not_found(client):
    r = client.get("/programs/Unknown Program")
    assert r.status_code == 404


def test_program_calorie_factors_are_correct(client):
    expected = {
        "Fat Loss (FL)": 22,
        "Muscle Gain (MG)": 35,
        "Beginner (BG)": 26,
    }
    programs = client.get("/programs").get_json()
    for name, factor in expected.items():
        assert programs[name]["calorie_factor"] == factor


# ---------- /clients – CREATE ----------

def test_create_client_success(client):
    payload = {
        "name": "Arjun Kumar",
        "age": 28,
        "height": 175.0,
        "weight": 80.0,
        "program": "Fat Loss (FL)",
    }
    r = client.post("/clients", json=payload)
    assert r.status_code == 201
    body = r.get_json()
    assert body["name"] == "Arjun Kumar"
    assert body["calories"] == 80 * 22


def test_create_client_missing_name_returns_400(client):
    r = client.post("/clients", json={"age": 25})
    assert r.status_code == 400


def test_create_duplicate_client_returns_409(client):
    payload = {"name": "Priya Sharma", "weight": 60.0, "program": "Beginner (BG)"}
    client.post("/clients", json=payload)
    r = client.post("/clients", json=payload)
    assert r.status_code == 409


# ---------- /clients – LIST ----------

def test_list_clients_empty_at_start(client):
    r = client.get("/clients")
    assert r.status_code == 200
    assert r.get_json() == []


def test_list_clients_after_insert(client):
    client.post("/clients", json={"name": "Ravi"})
    r = client.get("/clients")
    assert r.status_code == 200
    assert len(r.get_json()) == 1


# ---------- /clients/<name> – GET / UPDATE / DELETE ----------

def test_get_client_not_found(client):
    r = client.get("/clients/Nobody")
    assert r.status_code == 404


def test_update_client_changes_weight(client):
    client.post("/clients", json={"name": "Meena", "weight": 65.0, "program": "Muscle Gain (MG)"})
    r = client.put("/clients/Meena", json={"weight": 62.0})
    assert r.status_code == 200
    assert r.get_json()["weight"] == 62.0


def test_delete_client(client):
    client.post("/clients", json={"name": "Vikram"})
    r = client.delete("/clients/Vikram")
    assert r.status_code == 200
    assert client.get("/clients/Vikram").status_code == 404


def test_delete_nonexistent_client_returns_404(client):
    r = client.delete("/clients/Ghost")
    assert r.status_code == 404


# ---------- /clients/<name>/calories ----------

def test_calculate_calories(client):
    client.post("/clients", json={
        "name": "Deepa",
        "weight": 70.0,
        "program": "Muscle Gain (MG)",
    })
    r = client.get("/clients/Deepa/calories")
    assert r.status_code == 200
    body = r.get_json()
    assert body["estimated_calories"] == 70 * 35


def test_calories_no_client_returns_404(client):
    r = client.get("/clients/NoClient/calories")
    assert r.status_code == 404


# ---------- /clients/<name>/progress ----------

def test_log_progress_and_retrieve(client):
    client.post("/clients", json={"name": "Kartik"})
    r = client.post("/clients/Kartik/progress", json={"adherence": 85, "week": "Week 01 - 2025"})
    assert r.status_code == 201

    r2 = client.get("/clients/Kartik/progress")
    assert r2.status_code == 200
    entries = r2.get_json()
    assert len(entries) == 1
    assert entries[0]["adherence"] == 85


def test_log_progress_missing_adherence_returns_400(client):
    client.post("/clients", json={"name": "Siva"})
    r = client.post("/clients/Siva/progress", json={"week": "Week 01 - 2025"})
    assert r.status_code == 400


def test_log_progress_nonexistent_client_returns_404(client):
    r = client.post("/clients/Nobody/progress", json={"adherence": 50})
    assert r.status_code == 404


# ---------- /clients/<name>/workouts ----------

def test_log_workout_and_retrieve(client):
    client.post("/clients", json={"name": "Lakshmi"})
    payload = {
        "workout_type": "Strength",
        "date": "2025-07-01",
        "duration_min": 60,
        "notes": "5x5 back squat day",
    }
    r = client.post("/clients/Lakshmi/workouts", json=payload)
    assert r.status_code == 201
    assert r.get_json()["workout_type"] == "Strength"

    r2 = client.get("/clients/Lakshmi/workouts")
    assert r2.status_code == 200
    assert len(r2.get_json()) == 1


def test_log_workout_missing_type_returns_400(client):
    client.post("/clients", json={"name": "Kiran"})
    r = client.post("/clients/Kiran/workouts", json={"duration_min": 45})
    assert r.status_code == 400


def test_log_multiple_workouts(client):
    client.post("/clients", json={"name": "Anand"})
    for wt in ["Strength", "Hypertrophy", "Cardio"]:
        client.post("/clients/Anand/workouts", json={"workout_type": wt})
    r = client.get("/clients/Anand/workouts")
    assert len(r.get_json()) == 3


# ---------- /clients/<name>/bmi ----------

def test_bmi_normal_category(client):
    client.post("/clients", json={"name": "Nisha", "height": 165.0, "weight": 60.0})
    r = client.get("/clients/Nisha/bmi")
    assert r.status_code == 200
    body = r.get_json()
    assert body["category"] == "Normal"
    assert 18.5 <= body["bmi"] < 25


def test_bmi_overweight(client):
    client.post("/clients", json={"name": "Raj", "height": 170.0, "weight": 90.0})
    r = client.get("/clients/Raj/bmi")
    assert r.get_json()["category"] in ("Overweight", "Obese")


def test_bmi_missing_height_returns_400(client):
    client.post("/clients", json={"name": "Srini", "weight": 70.0})
    r = client.get("/clients/Srini/bmi")
    assert r.status_code == 400


def test_bmi_nonexistent_client_returns_404(client):
    r = client.get("/clients/Ghost/bmi")
    assert r.status_code == 404
