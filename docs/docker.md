# Docker

How this project packages the app as an image, runs it as containers, and runs the app and PostgreSQL together with Docker Compose. For the commands, see [Usage](../README.md#usage) in the root README.

------------------------------------------------------------------------------------------

## Big picture

```
Dockerfile  --docker build-->  image  --docker run-->  container (the app, running)
```

- **Dockerfile:** the recipe, one instruction per line, read top to bottom
- **Image:** the built result, a read-only package of everything the app needs (a minimal Linux, Python, the installed packages, the code); it runs the same on any machine with Docker
- **Container:** a running instance of an image; one image can run as many isolated containers as needed (like a class and its objects)

Everything after Docker builds on images: Kubernetes ([kubernetes.md](kubernetes.md)) and AWS never see the Python code, only the image.

------------------------------------------------------------------------------------------

## The Dockerfile

The [Dockerfile](../Dockerfile) in six steps:

1. `FROM python:3.10-slim`: start from an official image that already has Python; `slim` leaves out extras the app doesn't need
2. `WORKDIR /code`: all following paths are relative to `/code` inside the image
3. `COPY requirements.txt .` and `RUN pip install ...`: the dependencies
4. `COPY app/ app/`: the code
5. `EXPOSE 8000`: documents the port the app listens on
6. `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`: the command a container starts with

**Layer caching** decides the order of steps 3 and 4. Docker caches every step and rebuilds a step only when it or a step before it changed. The code changes often, `requirements.txt` rarely; with the dependencies first, a code change rebuilds only step 4 (0.1 s here) instead of reinstalling every package (8.6 s). Steps that change rarely go first.

**`--host 0.0.0.0`:** run directly, uvicorn listens on `127.0.0.1`, "this machine only". Inside a container, "this machine" is the container itself, so nothing outside could reach the app. `0.0.0.0` accepts connections from anywhere, including from outside the container.

------------------------------------------------------------------------------------------

## The build context and .dockerignore

`docker build -t study-cloud .` sends the folder `.` (the **build context**) to Docker; only files in it can be copied into the image. [`.dockerignore`](../.dockerignore) filters it, like `.gitignore` does for git:

- `.venv/`: hundreds of MB, and a Windows virtual environment wouldn't work in a Linux container anyway
- `.env`: the password file never needs to reach the build
- `*.db`: a local SQLite database is data, not code
- `.git/`, `_temp/`, `_documentation`, caches: not needed in the image

------------------------------------------------------------------------------------------

## Running a container

```bash
docker build -t study-cloud .                 # build the image and name ("tag") it
docker run --rm -p 8000:8000 study-cloud      # run it as a container
docker ps -a                                  # containers, including stopped ones
docker images                                 # images on this machine
```

- `-p 8000:8000` maps a port, `<this machine>:<container>`; without it, the app runs but nothing can reach it
- `--rm` deletes the container when it stops, so stopped containers don't pile up
- `docker run hello-world` is the classic first test: it pulls a tiny image from Docker Hub (the public registry) and runs it once

------------------------------------------------------------------------------------------

## Docker Compose

[`docker-compose.yaml`](../docker-compose.yaml) describes several containers in one file, so one command starts them all: `docker compose up --build`.

- **Services:** `app` (built from the Dockerfile with `build: .`) and `db` (the official `postgres:17-alpine` image with `image:`)
- **The network:** Compose creates a private network per project (`study-cloud_default`); every service joins it and is reachable by its **service name** as hostname, so the app connects to `db:5432`. The database needs no `ports:` entry, because only the app talks to it.
- **Naming:** everything is named `<project>-<service>`, and the project defaults to the folder name: image `study-cloud-app`, container `study-cloud-app-1`
- **Volumes:** a container's files disappear with it. The named volume `db-data` lives outside the container, so the data survives `docker compose down`; only `docker compose down -v` deletes it.
- **`${...}`:** Compose fills in values from `.env` next to the file, e.g. `${POSTGRES_PASSWORD}`; the password itself is never written in the compose file
- **`DATABASE_URL`:** the app reads where its database is from this one variable (see [app/db.py](../app/db.py)); Compose sets it to the `db` service, run directly the app falls back to a local SQLite file. The code never changes, only the variable.
- **`depends_on` and `restart`:** `depends_on: db` only means "start db first", not "wait until PostgreSQL accepts connections". If the app is faster, it crashes on startup and `restart: on-failure` starts it again until the database is ready.
- **Inside a running container:** `docker compose exec db psql -U study -d notes` opens PostgreSQL's command-line client in the `db` container
- Log lines are prefixed with the container they came from (`app-1 |`, `db-1 |`)

------------------------------------------------------------------------------------------

## Secrets

- `.env` holds the database user, password and name; it is gitignored and kept out of the build context
- `.env.example` is committed: the same keys with empty values, so everyone knows what `.env` needs
- `python main.py --init` creates `.env` from the example and can generate the password (see [Project Setup with main.py](../README.md#project-setup-with-mainpy))
- PostgreSQL takes `POSTGRES_PASSWORD` only when its data volume is first created; after changing the password in `.env`, the old one stays valid until `docker compose down -v` (which deletes the data)

------------------------------------------------------------------------------------------

## Housekeeping

Docker keeps old images and build cache until told otherwise.

```bash
docker system df            # what Docker stores, and how much of it is unused
docker container prune      # remove stopped containers
docker builder prune -a     # remove all build cache (safe: only rebuild speed-ups)
docker image prune          # remove dangling images (untagged leftovers)
```

- `docker builder prune` without `-a` removes only *dangling* cache, which is often nothing
- `docker image prune -a` removes every image no container uses, including other projects' images; they can be pulled or rebuilt again, but it takes time
- on Windows, Docker Desktop keeps all of this in one disk image; Settings → Resources → Advanced → Disk image location moves it to another drive

------------------------------------------------------------------------------------------

## Lessons

- **Order the Dockerfile by how often things change:** dependencies before code keeps rebuilds fast
- **Inside a container, listen on `0.0.0.0`**, and open the way in with `-p host:container`
- **The image cache:** a second `docker run hello-world` doesn't download anything; the same mechanism makes rebuilds fast
- **`Running pip as the 'root' user` during the build** is a warning for normal machines; inside an isolated image it is harmless (running the app as a non-root user is a later improvement)
- **Containers log in UTC** by default, so their times can differ from the local clock
- **Configuration through the environment** (`DATABASE_URL`, `${...}`) lets one image run against different databases; the same idea carries over to Kubernetes and AWS
- **`depends_on` sets start order, not readiness:** crashing until a dependency is ready, then restarting, is normal

------------------------------------------------------------------------------------------

## This project's files

- [`Dockerfile`](../Dockerfile): the image recipe for the app
- [`.dockerignore`](../.dockerignore): what stays out of the build context
- [`docker-compose.yaml`](../docker-compose.yaml): the app and PostgreSQL, with a named volume for the data
- [`.env.example`](../.env.example): the keys `.env` needs (created with `python main.py --init`)

------------------------------------------------------------------------------------------

## Changes

- 2026-10-14 — first version: concepts and lessons from step 2 (Dockerfile, containers, Compose with PostgreSQL, secrets, housekeeping)
