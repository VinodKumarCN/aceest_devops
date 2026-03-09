# ACEest Fitness & Gym – DevOps CI/CD Pipeline

A Flask REST API for ACEest Fitness & Gym client management, containerised with Docker and deployed through automated CI/CD pipelines using GitHub Actions and Jenkins.

---

## Project Structure

```
aceest-devops/
├── app.py                        # Flask application (core logic + REST endpoints)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── Jenkinsfile                   # Jenkins BUILD pipeline
├── .github/
│   └── workflows/
│       └── main.yml              # GitHub Actions CI/CD pipeline
└── tests/
    └── test_app.py               # Pytest unit test suite
```

---

## Application Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/programs` | List all fitness programs |
| GET | `/programs/<name>` | Get program details |
| GET | `/clients` | List all clients |
| POST | `/clients` | Register a new client |
| GET | `/clients/<name>` | Get a specific client |
| PUT | `/clients/<name>` | Update client details |
| DELETE | `/clients/<name>` | Remove a client |
| GET | `/clients/<name>/calories` | Estimated daily calories |
| POST | `/clients/<name>/progress` | Log weekly adherence |
| GET | `/clients/<name>/progress` | Get adherence history |
| POST | `/clients/<name>/workouts` | Log a workout session |
| GET | `/clients/<name>/workouts` | Get workout history |
| GET | `/clients/<name>/bmi` | Calculate BMI and risk category |

---

## Local Setup and Execution

### Prerequisites
- Python 3.11+
- Docker (optional, for containerised run)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/aceest-devops.git
cd aceest-devops
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the application locally

```bash
python app.py
```

The API starts on `http://localhost:5000`. Test it:

```bash
curl http://localhost:5000/health
curl http://localhost:5000/programs
```

### 4. Run with Docker

```bash
docker build -t aceest-fitness .
docker run -p 5000:5000 aceest-fitness
```

---

## Running Tests Manually

```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Run all tests with verbose output
pytest tests/test_app.py -v

# Run with coverage report
pytest tests/test_app.py -v --cov=app --cov-report=term-missing
```

The test suite covers: health endpoint, program listing, client CRUD operations, calorie calculation, progress logging, workout logging, and BMI calculation. Each test uses an isolated temporary database so tests never interfere with each other.

---

## GitHub Actions Pipeline

Located at `.github/workflows/main.yml`. Triggered on every `push` to `main`/`dev` and on every pull request targeting `main`.

**Pipeline stages:**

1. **Lint** – Runs `flake8` to catch syntax errors and undefined names.
2. **Unit Tests** – Runs the full `pytest` suite directly on the GitHub runner.
3. **Docker Build & Test** – Builds the Docker image, runs `pytest` inside the container, then performs a smoke test hitting `/health` to confirm the app starts cleanly.

All three stages must pass for a build to be considered successful.

---

## Jenkins BUILD Pipeline

Located at `Jenkinsfile`. Configure a Jenkins Multibranch Pipeline or a regular Pipeline job pointed at this repository.

**Pipeline stages:**

| Stage | What it does |
|-------|-------------|
| Checkout | Pulls latest code from GitHub |
| Setup Python Environment | Creates a virtualenv and installs dependencies |
| Lint | `flake8` syntax check |
| Unit Tests | `pytest` test suite |
| Docker Build | Builds image tagged with `BUILD_NUMBER` |
| Docker Test | Re-runs `pytest` inside the built container |
| Smoke Test | Starts the container and verifies `/health` responds |

**Post-build actions:** On success, the image is confirmed ready. On failure, the console output shows exactly which stage failed. The workspace is cleaned after every build.

### Setting up the Jenkins job

1. Install Jenkins and ensure Docker is available on the agent.
2. Create a new **Pipeline** job.
3. Under **Pipeline definition**, select *Pipeline script from SCM*.
4. Set SCM to Git, add the repository URL, and set the script path to `Jenkinsfile`.
5. Save and click **Build Now**.

---

## Fitness Programs

Three programs are built into the application, matching the original ACEest client specification:

| Program | Calorie Factor | Focus |
|---------|---------------|-------|
| Fat Loss (FL) | 22 kcal/kg | 5-day cardio & strength |
| Muscle Gain (MG) | 35 kcal/kg | 6-day barbell strength |
| Beginner (BG) | 26 kcal/kg | Full-body circuit |

Calorie targets are personalised: `estimated_calories = body_weight_kg × factor`.

---

## Version History

The application was iteratively developed from a tkinter desktop prototype (v1.0) through a series of incremental improvements before being re-architected as a Flask REST API for CI/CD integration:

- **v1.0** – Basic tkinter UI with program selector
- **v1.1** – Added client input fields and calorie estimation
- **v1.1.2** – Multi-client list with CSV export and progress charts
- **v2.0.1** – SQLite persistence with load/save client functionality
- **v2.2.4** – Extended schema with workout and body-metrics logging
- **v3.x** – Login/role management, PDF reports, AI program generator
- **Flask API** – Current version; re-architected for containerisation and CI/CD

---

## Notes

- The SQLite database file (`aceest_fitness.db`) is created automatically on first run.
- For production use, the database path can be overridden via the `DB_PATH` environment variable.
- The GitHub Actions pipeline uses `DB_PATH=/tmp/test_aceest.db` to keep test databases isolated from any persistent state.
