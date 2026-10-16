# Continuous integration

What continuous integration is, how this project does it with GitHub Actions, and the other common ways to do the same job.

------------------------------------------------------------------------------------------

## What CI is

**Continuous integration (CI):** every push is checked automatically on a fresh, clean machine: install the dependencies, run the tests, build what gets shipped. "It works on my machine" becomes "it works on a clean machine, on every push", and a broken change shows up minutes after it was pushed, not weeks later.

**Continuous delivery / deployment (CD):** the next stage. Once the checks pass, the result is published automatically (e.g. the image pushed to a registry) and, with continuous *deployment*, rolled out to a server or cluster as well. This project adds that in step 4 (AWS).

```
push  →  CI: install, test, build  →  CD: publish the image  →  deploy
         (now)                         (step 4)                 (step 4)
```

------------------------------------------------------------------------------------------

## This project's workflow

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every push and pull request, in two jobs:

1. **test:** check out the code, install Python 3.10, `pip install -r requirements.txt`, `python -m pytest`
2. **build:** `docker build -t study-cloud:ci .`, only if `test` passed

The vocabulary:

- **workflow:** one YAML file in `.github/workflows/`; GitHub finds it automatically
- **trigger (`on:`):** when it runs (`push`, `pull_request`, a schedule, a manual button ...)
- **job:** a group of steps that runs on its own fresh machine; jobs run in parallel unless `needs:` orders them
- **runner:** the machine a job runs on (`runs-on: ubuntu-latest`: a Linux machine hosted by GitHub)
- **step:** one command (`run:`) or a ready-made building block (`uses:`)
- **action:** a reusable step published by someone else, e.g. `actions/checkout` (get the code) or `actions/setup-python` (install Python); the `@v4` is its major version

Design choices worth knowing:

- **No database in CI:** the tests swap in their own SQLite file through FastAPI's `dependency_overrides` (see [tests/test_main.py](../tests/test_main.py)), so the runner needs no PostgreSQL
- **`needs: test`:** a commit with failing tests never produces an image
- **Building the image in CI** catches a broken `Dockerfile` or `requirements.txt` right away; in step 4 the same job will push the image to AWS
- **`cache: pip`** reuses downloaded packages between runs, so later runs are faster

Results show up in the repository's **Actions** tab, per run and per job, with the full log of every step; the badge in the root README shows the latest result.

------------------------------------------------------------------------------------------

## Other ways to do CI

The concepts above (a config file in the repo, triggers, isolated runners, steps, logs, artifacts) are the same everywhere; the syntax and where it runs differ.

| Tool | Where it runs | Configured in | When it fits |
|---|---|---|---|
| **GitHub Actions** | hosted by GitHub, or your own runners | `.github/workflows/*.yml` | code on GitHub; what this project uses |
| **GitLab CI/CD** | hosted by GitLab, or your own runners | `.gitlab-ci.yml` | code on GitLab; common in companies that self-host GitLab |
| **Jenkins** | your own servers | a `Jenkinsfile` (Groovy) or the web UI | the long-standing classic; very flexible, common in larger and older setups, but you run and maintain it yourself |
| **CircleCI** | hosted, or your own runners | `.circleci/config.yml` | a dedicated CI service that works with GitHub and Bitbucket |
| **Azure Pipelines** | hosted by Microsoft, or your own agents | `azure-pipelines.yml` | teams on Azure DevOps or Microsoft tooling |
| **Bitbucket Pipelines** | hosted by Atlassian | `bitbucket-pipelines.yml` | code on Bitbucket, teams using Jira |
| **Buildkite** | your own machines, coordinated by a hosted service | `.buildkite/pipeline.yml` | teams that want their own build machines without running the CI server |
| **AWS CodeBuild / CodePipeline** | inside AWS | `buildspec.yml` | projects that deploy to AWS and want CI next to it (relevant for step 4) |
| **Google Cloud Build** | inside Google Cloud | `cloudbuild.yaml` | the same, for Google Cloud |
| **Tekton, Argo Workflows** | as pods in a Kubernetes cluster | Kubernetes YAML | teams that run everything on Kubernetes, including the pipelines |

Close relatives:

- **Pre-commit hooks** (git hooks, or the `pre-commit` framework): checks such as formatting or linting run on your own machine *before* a commit is created. They are fast feedback, not a replacement for CI: they can be skipped, and they don't run on a clean machine.
- **GitOps tools (Argo CD, Flux):** not CI, but the CD side for Kubernetes: the cluster pulls its desired state from a git repository and applies it, the same idea as `kubectl apply -f kubernetes/` done automatically.

------------------------------------------------------------------------------------------

## Lessons

- **CI checks the repository, not your laptop.** A file that isn't committed doesn't exist for CI; an overly broad `.gitignore` pattern (e.g. `.*`) can silently keep `.github/` itself out of the repository, so the workflow never runs.
- **Tests that need no external services are easy to run anywhere.** The SQLite override makes the test job a plain `pip install` plus `pytest`.
- **Order jobs by what they protect:** test first, build after (`needs:`), publish and deploy last.
- **Pin what CI installs:** the pinned versions in `requirements.txt` make a CI run install exactly what passed locally.

------------------------------------------------------------------------------------------

## This project's files

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): the workflow, jobs `test` and `build`

------------------------------------------------------------------------------------------

## Changes

- 2026-10-17 — first version: CI and CD, this project's GitHub Actions workflow, other CI tools compared
