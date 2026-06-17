# DevOps Demo Platform

[![CI](https://github.com/Vijay-Pattar/devops-demo-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Vijay-Pattar/devops-demo-platform/actions/workflows/ci.yml)
[![CD (deploy to kind)](https://github.com/Vijay-Pattar/devops-demo-platform/actions/workflows/cd.yml/badge.svg)](https://github.com/Vijay-Pattar/devops-demo-platform/actions/workflows/cd.yml)

A self-contained, end-to-end **CI/CD + containerization + Kubernetes + observability**
project. A small Flask service is built, tested, security-scanned, containerized,
published to GHCR, and deployed to a **real Kubernetes cluster** — all on free
**GitHub-hosted runners**, with **no cloud account, no credentials, and no cost**.

> The application is deliberately simple. The point of this repo is the *platform
> engineering around it*: pipelines, containers, Helm, Terraform, and monitoring.

---

## Architecture

```
                          GitHub Actions (public runners)
   ┌──────────────────────────────────────────────────────────────────────┐
   │  CI workflow                                                           │
   │   ┌─────────┐  ┌──────┐  ┌───────────────┐  ┌────────────┐  ┌────────┐ │
   │   │ ruff /  │→ │ unit │→ │ Trivy / Gitleaks│→ │ hadolint / │→ │ build  │ │
   │   │ bandit  │  │ tests│  │ Helm / TF / TF │  │ promtool   │  │ + push │ │
   │   └─────────┘  └──────┘  └───────────────┘  └────────────┘  └───┬────┘ │
   │                                                                  │      │
   │  CD workflow                                                     ▼      │
   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐  GHCR     │
   │   │ create kind  │ → │ helm install │ → │ smoke test (curl)│  image    │
   │   │  cluster     │   │  the chart   │   │  /health /metrics│           │
   │   └──────────────┘   └──────────────┘   └──────────────────┘           │
   └──────────────────────────────────────────────────────────────────────┘
```

## Tech stack

| Area              | Tooling                                                       |
| ----------------- | ------------------------------------------------------------- |
| Application       | Python 3.12, Flask, Gunicorn                                  |
| Metrics           | prometheus-client (`/metrics` endpoint)                       |
| Container         | Multi-stage Dockerfile, non-root, read-only rootfs, healthcheck |
| CI                | GitHub Actions — ruff, bandit, pytest (80% coverage gate)     |
| Security          | Trivy (fs + image), Gitleaks (secrets), Hadolint (Dockerfile) |
| Registry          | GitHub Container Registry (GHCR) via built-in `GITHUB_TOKEN`  |
| Orchestration     | Kubernetes (kind), Helm chart with HPA + probes              |
| IaC               | Terraform (kubernetes provider: namespace + config)          |
| Observability     | Prometheus config + alert rules (validated with `promtool`)   |

## Repository layout

```
.
├── app/                  # Flask service + tests
│   ├── app.py
│   ├── tests/test_app.py
│   └── requirements*.txt
├── Dockerfile            # multi-stage, rootless runtime
├── docker-compose.yml    # local app + Prometheus
├── helm/demo-app/        # Helm chart (deployment, service, HPA)
├── k8s/                  # plain manifests (alternative to Helm)
├── terraform/            # namespace + config-as-code
├── monitoring/           # prometheus.yml + alert.rules.yml
└── .github/workflows/    # ci.yml, cd.yml
```

## Run it locally

```bash
# Option A: just the app
make docker-build && make docker-run
curl localhost:8000/health

# Option B: app + Prometheus
make compose-up
# app        -> http://localhost:8000
# Prometheus -> http://localhost:9090   (try the "demo-app" target)
```

## Endpoints

| Method | Path          | Description                       |
| ------ | ------------- | -------------------------------- |
| GET    | `/`           | Service info + uptime            |
| GET    | `/health`     | Liveness probe                   |
| GET    | `/ready`      | Readiness probe                  |
| GET    | `/api/tasks`  | List tasks                       |
| POST   | `/api/tasks`  | Create a task `{"title": "..."}` |
| GET    | `/metrics`    | Prometheus metrics               |

## CI/CD pipeline

**CI** (`ci.yml`) runs on every push/PR:
1. **Lint & test** — `ruff`, `bandit`, `pytest` with an 80% coverage gate
2. **IaC validation** — Hadolint, `helm lint`/`template`, `terraform fmt`/`validate`, `promtool`
3. **Security** — Trivy filesystem scan + Gitleaks secret scan
4. **Build & push** — multi-stage image to GHCR (only on push to `main`), then Trivy image scan

**CD** (`cd.yml`) runs on push to `main`:
1. Build the image and **create a real `kind` cluster** in the runner
2. **`helm upgrade --install`** the chart, wait for rollout
3. **Smoke test** `/health`, `/`, `/api/tasks`, `/metrics` via port-forward
4. Dump pod logs/diagnostics automatically if anything fails

## Design notes / talking points

- **Why kind?** It runs a genuine Kubernetes cluster *inside* a GitHub runner, so
  the CD pipeline proves a real deploy without any cloud spend or secrets.
- **Security baked in:** image runs as a non-root user with a read-only root
  filesystem and all Linux capabilities dropped; the pipeline scans code, deps,
  the Dockerfile, and the final image.
- **No secrets required:** image publishing uses the automatically-provided
  `GITHUB_TOKEN`, so the repo works out-of-the-box on any fork.
