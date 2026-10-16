# Kubernetes

The Kubernetes objects this project uses, what each one is for, and how they fit together. For the commands to run it, see [Run on Kubernetes (local)](../README.md#run-on-kubernetes-local) in the root README.

------------------------------------------------------------------------------------------

## Big picture

Kubernetes replaces `docker compose`, not the app. The app, the Dockerfile and the image stay the same; only the part that runs the containers changes:

```
step 2:   docker-compose.yaml  →  docker compose up   →  Docker runs the containers
step 3:   kubernetes/*.yaml    →  kubectl apply       →  Kubernetes runs the containers
```

Kubernetes never builds anything: it only runs finished images. And it is declarative: the YAML files describe what *should* exist, and `kubectl apply -f kubernetes/` makes the cluster match them (`created`, `configured` or `unchanged`). The cluster then keeps comparing what should exist with what does exist, and fixes any difference.

------------------------------------------------------------------------------------------

## From Compose to Kubernetes

| In `docker-compose.yaml` | In Kubernetes | What it does |
|---|---|---|
| a service (`app:`, `db:`) | **Deployment** | keeps N pods of an image running |
| the service name as hostname (`db`) | **Service** | a stable name and address in front of changing pods |
| `ports: "8000:8000"` | Service + `kubectl port-forward` | the way in from outside |
| `${POSTGRES_PASSWORD}` from `.env` | **Secret** | sensitive values, handed to containers as environment variables |
| `environment:` settings | **ConfigMap** (or `env:` in the Deployment) | non-secret settings |
| volume `db-data` | **PersistentVolumeClaim** | storage that outlives pods |
| (no equivalent) | `replicas`, probes | several copies, health checks with automatic restarts |

------------------------------------------------------------------------------------------

## Cluster parts

- **Cluster:** a set of machines (nodes) running Kubernetes
- **Node:** one machine of the cluster; with kind, a node is a Docker container (`study-cloud-control-plane`)
- **kind** ("Kubernetes in Docker"): creates a real, local cluster as Docker containers; an official Kubernetes project, also common in CI
- **kubectl:** the command-line client; it only sends requests to a cluster's API
- **Context:** which cluster kubectl talks to; `kind create cluster` sets it to `kind-study-cloud`
- **Namespace:** a folder inside the cluster that groups objects; everything here lives in `default`

The control plane is the cluster's "brain". With kind, all of it runs as containers inside the one node (`docker exec study-cloud-control-plane crictl images` lists them):

| Component | Its job |
|---|---|
| `kube-apiserver` | the front door: every kubectl command goes here |
| `etcd` | the cluster's database: everything that should exist |
| `kube-scheduler` | decides which node a new pod runs on |
| `kube-controller-manager` | the "keep it so" loops, e.g. "2 pods wanted, 1 running: start one" |
| `kube-proxy` | routes Service traffic to the right pods |
| `coredns` | the cluster's DNS: makes Service names like `db` resolvable |
| `kindnetd` | the network between pods (the CNI) |
| `local-path-provisioner` | creates storage for PersistentVolumeClaims (the StorageClass `standard`) |

The cluster has its own image storage, separate from your laptop's Docker. Local images get in with `kind load docker-image <image> --name study-cloud`; in the cloud, a registry (e.g. AWS ECR) takes that role.

------------------------------------------------------------------------------------------

## Pod and Deployment

- **Pod:** the smallest thing Kubernetes runs, a wrapper around one container (sometimes a few). Pods get generated names (`app-66d7666d65-4vjxq`: Deployment name, blueprint hash, random suffix) and are never started by hand.
- **Deployment:** declares "keep N pods of this image running". The controller creates the pods and keeps the count true:
    - a deleted or crashed pod is replaced within seconds (self-healing)
    - `kubectl scale deployment app --replicas=5` changes the count
    - a new image tag plus `kubectl apply` replaces the pods one by one (rolling update)
- **Labels and selectors:** Kubernetes connects objects by labels, not by names. The Deployment's `selector` finds its pods by the label in the pod `template` (`app: study-cloud`); Services and `kubectl ... -l app=study-cloud` use the same labels.
- **`RESTARTS`** in `kubectl get pods` counts container restarts in the same pod (e.g. after the node was stopped and started); a count that keeps rising on a running cluster usually means a crashing app.

------------------------------------------------------------------------------------------

## Service

Pods come and go, and each new pod gets a new name and IP address, so nothing should connect to a pod directly. A **Service** gives a group of pods one stable name and address, and spreads traffic across whichever pods currently carry its `selector` label.

- inside the cluster, the Service name works as a hostname: the app reaches PostgreSQL at `db:5432`, just like in Compose
- `port` is the Service's port, `targetPort` the container port it forwards to
- `kubectl port-forward service/app 8000:8000` tunnels `localhost:8000` to the Service; the tunnel sticks to one pod and breaks when that pod is replaced

------------------------------------------------------------------------------------------

## Storage (PVC)

A container's own files disappear with the container. Data that must survive goes on a volume:

```
PersistentVolumeClaim db-data   →   PersistentVolume pvc-...   →   mounted into the db pod
"I need 1 GiB"                      created by the StorageClass     at /var/lib/postgresql/data
```

- **PersistentVolumeClaim (PVC):** a request for storage (`1Gi`, `ReadWriteOnce` = one node writes at a time); status `Bound` once real storage is attached
- **PersistentVolume (PV):** the actual storage, created automatically by the StorageClass (`standard` in kind)
- a replaced db pod mounts the same claim, so the data is still there
- `PGDATA` points to a subfolder of the mount, so PostgreSQL always finds an empty directory to initialize
- the db Deployment uses `strategy: Recreate`: the old pod stops before the new one starts, so two PostgreSQL servers never write to the same files (the default strategy starts the new pod first)
- in real clusters, databases usually run as a **StatefulSet** or outside Kubernetes as a managed service (e.g. AWS RDS); a one-replica Deployment is the simplest way to learn the pieces

------------------------------------------------------------------------------------------

## Secret

A **Secret** holds sensitive values and hands them to containers as environment variables.

- created from the existing `.env`, so the password stays in one place and no secret YAML is committed:
    ```bash
    kubectl create secret generic db-credentials --from-env-file=.env
    ```
- `generic` (type `Opaque`): plain key/value pairs; `kubectl get secrets` shows the number of entries (3 here)
- `envFrom: - secretRef: name: db-credentials` turns every entry into an environment variable, exactly the `POSTGRES_*` names the postgres image expects
- by default, Secrets are only base64-encoded, not encrypted: anyone with access to the cluster can read them. They keep passwords out of YAML files and images; real encryption comes from the cloud provider or extra tools

------------------------------------------------------------------------------------------

## Connecting the app

The app reads where its database is from `DATABASE_URL` (see [app/db.py](../app/db.py)), the same as in Compose. The app Deployment builds it from the Secret:

```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom: { secretKeyRef: { name: db-credentials, key: POSTGRES_PASSWORD } }
  # ... POSTGRES_USER and POSTGRES_DB the same way
  - name: DATABASE_URL
    value: postgresql+psycopg://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@db:5432/$(POSTGRES_DB)
```

- `secretKeyRef` takes one entry from a Secret (`envFrom` takes all of them)
- `$(NAME)` is filled in from variables defined earlier in the same list, so the password never appears in a file; it's the Kubernetes counterpart of `${...}` in Compose
- `db:5432` is the db Service, so the URL is the same as in Compose
- the image doesn't change: only the environment does

**Rolling update:** changing the pod template and running `kubectl apply` replaces the pods one by one. The new pods get a new blueprint hash in their names (`app-66d7666d65-...` became `app-856585f7f5-...`); old pods leave the Service and stop once the new ones are ready.

**The file is the wish, `apply` sends it:** editing a YAML file changes nothing in the cluster until `kubectl apply`. Pods that still carry the old hash still run the old blueprint.

------------------------------------------------------------------------------------------

## Health probes

Kubernetes calls the app's `/health` endpoint to decide what to do with a pod:

| Probe | Question | When it fails |
|---|---|---|
| **readinessProbe** | can this pod take traffic? | the pod is taken out of the Service until it answers again; new pods show `0/1` until then |
| **livenessProbe** | is this pod still alive? | Kubernetes restarts the container (self-healing for hung pods, not only deleted ones) |

- `periodSeconds` sets how often it asks, `initialDelaySeconds` how long it waits after the start
- a probe is only as good as the endpoint behind it: `/health` here only shows that the web server answers, not that the database is reachable; a readiness check that also tests the database would be the next improvement

------------------------------------------------------------------------------------------

## How the pieces connect

```
app pods ──"db:5432"──▶ Service db ──▶ db pod (kept running by Deployment db)
   ▲   │                                  │
   │   └── DATABASE_URL from              ├── env from Secret db-credentials
   │       Secret db-credentials          └── mounts PVC db-data (the data)
Service app (readiness probe decides which pods get traffic)
   ▲
kubectl port-forward (your browser)
```

With this, the app pods are stateless: deleting all of them loses nothing, because the notes live in PostgreSQL on the claim.

------------------------------------------------------------------------------------------

## Lessons

- **Pods hold no data.** Without a database, each app pod kept notes in its own SQLite file inside the container; deleting the pods deleted the notes, and with 2 replicas each pod even had a separate database. Pods are disposable by design; data belongs in a database on persistent storage.
- **Never deploy `:latest`.** Kubernetes always tries to download a fresh `:latest` image, which fails for a local one; use a fixed tag like `study-cloud:dev`.
- **The cluster can't see local images** until `kind load docker-image` copies them in.
- **kubectl version skew:** kubectl is supported within one minor version of the cluster. Docker Desktop ships its own (older) kubectl; check with `kubectl version` (client and server) and `Get-Command kubectl -All` (which copy comes first on PATH).
- **PowerShell and commas:** an unquoted comma makes a list, so `kubectl get pods,pvc` arrives as two words and fails with `pods "pvc" not found`; quote it: `kubectl get "pods,pvc"`. Bash doesn't need the quotes.
- **Same hash, old blueprint.** After editing a Deployment file, the change only takes effect with `kubectl apply`; if the pod names still carry the old hash, the cluster is still running the old version.
- **Reading errors:** `Error from server (NotFound): pods "pvc" not found` means kubectl reached the cluster and the cluster answered: no pod named `pvc`. Look at the command first.
- **Exit code 127** means "command not found": the tool isn't installed or the terminal was opened before the install.

------------------------------------------------------------------------------------------

## This project's files

All in [`kubernetes/`](../kubernetes/), applied together with `kubectl apply -f kubernetes/`:

- `app-deployment.yaml`: 2 pods of `study-cloud:dev`, label `app: study-cloud`, `DATABASE_URL` built from the Secret, readiness and liveness probes on `/health`
- `app-service.yaml`: the name `app` on port 8000 in front of the app pods
- `db-deployment.yaml`: 1 PostgreSQL pod (`postgres:17-alpine`), credentials from the Secret, data on the PVC, `strategy: Recreate`
- `db-service.yaml`: the name `db` on port 5432 in front of the db pod
- `db-storage.yaml`: the PersistentVolumeClaim `db-data` (1 GiB)
- the Secret `db-credentials` has no file: it is created from `.env` with `kubectl create secret`

------------------------------------------------------------------------------------------

## Changes

- 2026-10-14 — added "Connecting the app" (DATABASE_URL from the Secret, rolling update, apply) and "Health probes"; app file entry, connection diagram and lessons updated for step 3 part 5
- 2026-10-14 — first version: concepts and lessons from step 3 parts 1-4 (cluster, app Deployment and Service, Secret, PostgreSQL with storage)
