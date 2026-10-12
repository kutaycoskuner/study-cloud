<h1 align="center">
    study-cloud
</h1>

<p align="center">
    Study project for deploying a backend: a small FastAPI service, taken step by step through Docker, Kubernetes, AWS and Terraform.
</p>

<p align="center">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/study-cloud" />
</p>

------------------------------------------------------------------------------------------

## Roadmap

1. **Service** (in progress): FastAPI app with a health check and a notes API, plus tests
2. **Docker:** Dockerfile for the API, Docker Compose for API + PostgreSQL
3. **Kubernetes, locally:** the same containers in a local cluster
4. **AWS:** the image in ECR, running on EC2 or ECS (free tier)
5. **Terraform:** the AWS setup as code

------------------------------------------------------------------------------------------

## Folders

```
study-cloud/
├── app/
│   └── main.py          # FastAPI app: /health and the notes endpoints
├── tests/
│   └── test_main.py     # endpoint tests (TestClient, no server needed)
└── requirements.txt     # app and test dependencies
```

------------------------------------------------------------------------------------------

## Usage

| Method | Path              | What it does                         |
|--------|-------------------|--------------------------------------|
| GET    | `/health`         | liveness check, returns `{"status": "ok"}` |
| GET    | `/notes`          | lists all notes                      |
| POST   | `/notes`          | creates a note from `{"text": "..."}` |
| GET    | `/notes/{id}`     | returns one note, 404 if missing     |

Notes are kept in memory for now, so they are lost when the server restarts.

```bash
# Start the server (reloads on code changes)
uvicorn app.main:app --reload

# Interactive API docs
#   http://127.0.0.1:8000/docs

# Run the tests (from the repo root, so `app` is importable)
python -m pytest
```

------------------------------------------------------------------------------------------

## Setup Python Environment

- **Python 3.10+**: [Install Python](https://www.python.org/downloads/)
- **Git**: [Install Git](https://git-scm.com/downloads)

```bash
# 1. Clone the repository
git clone https://github.com/kutaycoskuner/study-cloud.git
cd study-cloud

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#   Windows (PowerShell):
.venv\Scripts\Activate.ps1
#   macOS / Linux:
source .venv/bin/activate

# 4. Install the dependencies
pip install -r requirements.txt

# 5. Run the server
uvicorn app.main:app --reload

# Optional: deactivate the environment when done
deactivate
```
