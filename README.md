<h1 align="center">
    study-cloud
</h1>

<p align="center">
    Study project for deploying a backend: a small FastAPI service, taken step by step through Docker, Kubernetes, AWS and Terraform.
</p>

<p align="center">
    <img alt="CI" src="https://github.com/kutaycoskuner/study-cloud/actions/workflows/ci.yml/badge.svg" />
    <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue" />
    <img alt="Last Update" src="https://img.shields.io/github/last-commit/kutaycoskuner/study-cloud" />
</p>

------------------------------------------------------------------------------------------

## Roadmap

1. **Service** (done): FastAPI app with a health check and a notes API, plus tests
2. **Docker** (done): Dockerfile, Compose with PostgreSQL, data in a volume
3. **Kubernetes, locally** (done): app and PostgreSQL on a local kind cluster: Deployments, Services, Secret, persistent storage, health probes
4. **Terraform** (in progress): infrastructure as code: the Compose stack with Terraform's Docker provider first (local, free), then AWS created through Terraform (the image in ECR, running on EC2 or ECS)

------------------------------------------------------------------------------------------

## Documentation

- [docs/](docs/README.md): background and explanations, indexed
    - [Docker](docs/docker.md): the image, containers, and the app with PostgreSQL in Docker Compose
    - [Continuous integration](docs/continuous-integration.md): tests and image build on every push (GitHub Actions), and other CI tools
    - [Kubernetes](docs/kubernetes.md): the objects this project uses (Deployment, Service, Secret, storage) and how they fit together
    - [Terraform](docs/terraform.md): infrastructure as code, the ideas behind Terraform, and how this project uses it

------------------------------------------------------------------------------------------

## Folders

```
study-cloud/
├── .github/
│   └── workflows/
│       └── ci.yml       # CI: tests, then a Docker image build, on every push
├── app/
│   ├── db.py            # database connection and the notes table
│   └── main.py          # FastAPI app: /health and the notes endpoints
├── docs/
│   ├── README.md        # index of the docs
│   ├── continuous-integration.md  # CI concepts, this workflow, other CI tools
│   ├── docker.md        # Docker and Compose concepts and lessons
│   ├── kubernetes.md    # Kubernetes concepts and lessons
│   └── terraform.md     # Terraform concepts and how this project uses it
├── kubernetes/
│   ├── app-deployment.yaml  # keeps 2 app pods running
│   ├── app-service.yaml     # stable name "app" in front of the app pods
│   ├── db-deployment.yaml   # 1 PostgreSQL pod, credentials from the Secret
│   ├── db-service.yaml      # stable name "db" in front of the db pod
│   └── db-storage.yaml      # storage claim for the database data
├── scripts/
│   └── init_env.py      # creates .env from .env.example (run via main.py --init)
├── tests/
│   └── test_main.py     # endpoint tests (TestClient, no server needed)
├── .dockerignore        # what stays out of the image build
├── .env.example         # keys for .env (database user, password, name); .env is gitignored
├── docker-compose.yaml  # local stack: app + PostgreSQL
├── Dockerfile           # image recipe for the app
├── main.py              # project tasks: python main.py --init
└── requirements.txt     # app and test dependencies
```

------------------------------------------------------------------------------------------

## Project Setup with main.py

`main.py` in the repo root collects the project's setup tasks behind short commands, so you don't need to remember script paths. It is not the web app (that is `app/main.py`).

```bash
# List the available tasks (runs nothing)
python main.py

# Create .env from .env.example: asks before writing and can generate the database password
python main.py --init

# Show what --init would do, without writing anything
python main.py --init --dry-run
```

- `--init` is safe to run again: on an existing `.env` it only offers to append keys that `.env.example` gained, and never changes your values
- generated passwords are written to `.env` only, never printed; open the file to see them
- `.env` is gitignored, `.env.example` (keys only, no values) is committed

------------------------------------------------------------------------------------------

## Usage

| Method | Path              | What it does                         |
|--------|-------------------|--------------------------------------|
| GET    | `/health`         | liveness check, returns `{"status": "ok"}` |
| GET    | `/notes`          | lists all notes                      |
| POST   | `/notes`          | creates a note from `{"text": "..."}` |
| GET    | `/notes/{id}`     | returns one note, 404 if missing     |

Notes are stored in the database `DATABASE_URL` points to: PostgreSQL in Docker Compose, a local `notes.db` (SQLite) otherwise. Tests use their own temporary database.

```bash
# Start the server (reloads on code changes)
uvicorn app.main:app --reload

# Interactive API docs
#   http://127.0.0.1:8000/docs

# Run the tests (from the repo root, so `app` is importable)
python -m pytest

# Build the image and run it as a container (http://127.0.0.1:8000/docs)
docker build -t study-cloud .
docker run --rm -p 8000:8000 study-cloud

# Or start the whole stack (app + PostgreSQL); needs .env
docker compose up --build
#   stop: Ctrl+C, then
docker compose down
```

How the image, the containers and Compose work: [docs/docker.md](docs/docker.md).

------------------------------------------------------------------------------------------

## Run on Kubernetes (local)

Needs Docker Desktop, kind and kubectl (see "Setup Python Environment"). What these objects are and how they fit together: [docs/kubernetes.md](docs/kubernetes.md).

```bash
# 1. Create a local cluster (a Docker container running Kubernetes)
kind create cluster --name study-cloud

# 2. Build the image with a fixed tag and copy it into the cluster
docker build -t study-cloud:dev .
kind load docker-image study-cloud:dev --name study-cloud

# 3. Create the database Secret from .env (python main.py --init creates .env)
kubectl create secret generic db-credentials --from-env-file=.env

# 4. Create the app and database objects
kubectl apply -f kubernetes/
kubectl get pods

# 5. Open a tunnel to the Service (http://127.0.0.1:8000/docs)
kubectl port-forward service/app 8000:8000

# Pause / resume the cluster, or delete it completely
docker stop study-cloud-control-plane
docker start study-cloud-control-plane
kind delete cluster --name study-cloud
```

The app pods are stateless: notes live in PostgreSQL on the PersistentVolumeClaim and survive replaced app and db pods.

------------------------------------------------------------------------------------------

## Setup Python Environment

- **Python 3.10+**: [Install Python](https://www.python.org/downloads/)
- **Git**: [Install Git](https://git-scm.com/downloads)
- **Docker Desktop** (optional, for the container): [Install Docker](https://docs.docker.com/get-docker/)
- **kind** and **kubectl** (optional, for the local cluster): [Install kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation), [Install kubectl](https://kubernetes.io/docs/tasks/tools/)

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

# 5. Create .env (see "Project Setup with main.py")
python main.py --init

# 6. Run the server
uvicorn app.main:app --reload

# Optional: deactivate the environment when done
deactivate
```
