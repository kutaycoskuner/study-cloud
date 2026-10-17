# Terraform

What Terraform is, the ideas it is built on, how it compares to similar tools, and how this project uses it. This doc grows with step 4.

------------------------------------------------------------------------------------------

## What Terraform is

Terraform is a tool for **infrastructure as code (IaC)**. Infrastructure (servers, networks, databases, containers, DNS entries ...) is described in text files, and Terraform creates, changes and deletes the real thing to match them.

The files live in git, so infrastructure gets the same review, history and reproducibility as code. Without it, infrastructure is built by clicking through web consoles: nobody can review it, repeat it on a second environment, or reliably undo it.

```
main.tf (what should exist)  →  terraform plan  →  terraform apply  →  real infrastructure
                                 "here's what       creates or            (containers, clusters,
                                  I'd change"       changes it             cloud servers ...)
                                         ↕
                               terraform.tfstate (what Terraform created last time)
```

### Is it free?

| | Paid? | What it is |
|---|---|---|
| **Terraform CLI** (the `terraform` command) | free | the tool itself, for personal projects and at work |
| **HCP Terraform** (formerly Terraform Cloud) | free tier and paid plans | HashiCorp's optional hosted service: stores state, runs plan/apply for teams, manages permissions |
| **The infrastructure it creates** | depends on the platform | local Docker containers cost nothing; cloud resources cost what the cloud provider charges, Terraform adds nothing on top |

In 2023 HashiCorp moved Terraform from an open-source license to the Business Source License. It doesn't make Terraform paid for users; it mainly forbids other companies from offering a competing commercial Terraform service built on its code. **OpenTofu** was forked from the last open-source version for those who want a guaranteed open-source tool; it is used almost identically (`tofu plan` instead of `terraform plan`).

------------------------------------------------------------------------------------------

## Core ideas

- **Declarative:** the files say *what* should exist, not the steps to create it; Terraform works out the steps (the same idea as `kubectl apply`, see [kubernetes.md](kubernetes.md))
- **HCL:** Terraform's configuration language, in `.tf` files:
    ```hcl
    resource "docker_container" "app" {
      name  = "study-cloud-app"
      image = docker_image.app.image_id
    }
    ```
- **Providers:** plugins that talk to one platform's API: AWS, Azure, Google Cloud, Docker, Kubernetes, GitHub, Cloudflare and thousands more. Terraform itself knows no platform; the providers do. Their versions are pinned like Python packages.
- **Resources:** the things a provider manages: one container, one network, one cloud server. Resources can refer to each other (`docker_image.app.image_id` above), and Terraform creates them in the right order from those references.
- **The workflow:**
    - `terraform init`: download the providers
    - `terraform plan`: show what would change, change nothing
    - `terraform apply`: make the changes (shows the plan again and asks first)
    - `terraform destroy`: remove everything this configuration created
- **State (`terraform.tfstate`):** Terraform's record of what it created and how that maps to the files, so it can tell "add", "change" and "remove" apart. It can contain secrets (e.g. passwords), so it is **never committed**; teams keep it in remote storage (e.g. a cloud storage bucket) so everyone works from the same state.
- **Variables and outputs:** inputs that make a configuration reusable (`variable "db_password"`), and values it reports back after `apply` (e.g. a server's address)
- **Modules:** reusable bundles of resources, like functions for infrastructure

------------------------------------------------------------------------------------------

## Similar tools

| Tool | How it differs from Terraform |
|---|---|
| **Docker Compose, kubectl apply** | also declarative, but each for one platform only; Terraform spans many, including the infrastructure underneath Compose and Kubernetes |
| **AWS CloudFormation, Azure Bicep** | infrastructure as code from one cloud provider, for that cloud only |
| **Pulumi** | infrastructure as code written in real programming languages (Python, TypeScript ...) instead of HCL |
| **Ansible** | mostly *configures* existing machines (installs packages, edits files) rather than creating infrastructure; often used together with Terraform |
| **OpenTofu** | the open-source fork of Terraform, nearly identical in use |

------------------------------------------------------------------------------------------

## How it fits this project

1. **Docker provider first:** the Compose stack (network, volume, PostgreSQL and the app) rewritten as Terraform, on the local machine and free. It teaches the plan/apply/destroy loop, state, variables and outputs next to a setup that is already familiar ([docker.md](docker.md)).
2. **AWS through Terraform:** cloud resources are created with Terraform from the start instead of being clicked together first; `terraform destroy` removes everything in one command, which keeps costs under control.

------------------------------------------------------------------------------------------

## Changes

- 2026-10-17 — first version: what Terraform is, whether it is free, core ideas, similar tools, plan for this project
