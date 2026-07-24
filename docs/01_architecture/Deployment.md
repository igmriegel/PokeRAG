# Deployment.md — Docker Compose, Kubernetes IaC & Cloud Deployment

## Objective

Provide the **operational deployment guide** for the Pokemon TCG RAG system: a
service-by-service description of the Docker Compose stack, the one-command bootstrap
sequence, environment configuration, cloud-deployment options (bonus), Kubernetes manifests,
and rollback/data-persistence notes. Grounded in
[`docker-compose.yml`](../../docker-compose.yml), [`.env.example`](../../.env.example),
[`Makefile`](../../Makefile), and [`deploy/k8s/stack.yaml`](../../deploy/k8s/stack.yaml).

## Scope

- **In scope:** local/prod Compose deployment, env config, startup order, cloud options
  (Render/Railway/AWS), K8s reference, rollback & persistence.
- **Out of scope:** security hardening detail ([`Security.md`](./Security.md)), metrics/dash
  config ([`Observability.md`](./Observability.md)), ingestion internals
  ([`IndexingPipeline.md`](./IndexingPipeline.md)).

Satisfies [REQ-016](../00_project/REQUIREMENTS.md) (all services in Compose),
[REQ-020](../00_project/REQUIREMENTS.md) (IaC/K8s), and [SC-014](../00_project/SUCCESS_CRITERIA.md)
/ [SC-024](../00_project/SUCCESS_CRITERIA.md) (reproducibility).

---

## 1. Service Topology

```mermaid
graph TD
    subgraph Compose Network
        API["api<br/>FastAPI :8000"]
        UI["ui<br/>Streamlit :8501"]
        QD[("qdrant :6333/:6334")]
        PG[("postgres :5432")]
        ING["ingestion<br/>(profile: ingestion)"]
        PROM["prometheus :9090"]
        GRAF["grafana :3000"]
    end
    API -->|dense/bm25/hybrid search| QD
    API -->|feedback + logs| PG
    UI -->|query/feedback| API
    ING -->|index chunks| QD
    PROM -->|scrape /metrics| API
    GRAF -->|query datasource| PROM
    USER([User]) --> UI
    OPERATOR([Operator]) --> GRAF
```

> **Note on service naming:** the current Compose stack separates the interfaces into
> `api` and `ui` services, both built from `docker/Dockerfile.app`. The Kubernetes
> reference mirrors that split instead of using a single combined app container.

---

## 2. Service-by-Service Reference

Grounded field-for-field in [`docker-compose.yml`](../../docker-compose.yml).

| Service | Image / Build | Ports | Volumes | depends_on | Healthcheck |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **qdrant** | `qdrant/qdrant:v1.7.4` | `6333`, `6334` | `qdrant_storage:/qdrant/storage` | — | `curl -f http://localhost:6333/healthz` (10s/5s×5) |
| **postgres** | `postgres:16-alpine` | `5432` | `postgres_data:/var/lib/postgresql/data` | — | `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` (5s/5s×5) |
| **ingestion** | build `docker/Dockerfile.ingestion` | — | `./data:/app/data`, `./config:/app/config` | qdrant (healthy), postgres (healthy) | — (batch job, `profiles: [ingestion]`) |
| **api** | build `docker/Dockerfile.app` | `8000` | `./data:/app/data`, `./config:/app/config` | qdrant (healthy), postgres (healthy) | `curl -f http://localhost:8000/health` (10s/5s×5) |
| **ui** | build `docker/Dockerfile.app` | `8501` | `./data:/app/data`, `./config:/app/config` | api (healthy) | `curl -f http://localhost:8501/_stcore/health` (10s/5s×5) |
| **prometheus** | `prom/prometheus:v2.48.1` | `9090` | `./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml`, `prometheus_data:/prometheus` | api (healthy) | — |
| **grafana** | `grafana/grafana:10.2.3` | `3000` | `./docker/grafana/provisioning:/etc/grafana/provisioning`, `./docker/grafana/dashboards:/etc/grafana/dashboards`, `grafana_data:/var/lib/grafana` | prometheus | — |

Named volumes (persistent): `qdrant_storage`, `postgres_data`, `prometheus_data`,
`grafana_data`. `restart: unless-stopped` is set on qdrant, postgres, api, ui, prometheus,
grafana.

Key environment wiring (Compose → container):
- `api`: `QDRANT_HOST=qdrant`, `QDRANT_PORT=6333`, `POSTGRES_HOST=postgres`,
  `POSTGRES_PORT=5432`, `POSTGRES_USER/PASSWORD/DB`, `OPENAI_API_KEY`, `ENVIRONMENT`.
- `ui`: `POKERAG_API_URL=http://api:8000/api/v1`, `ENVIRONMENT`.
- `ingestion`: `QDRANT_HOST=qdrant`, `QDRANT_PORT=6333`, `OPENAI_API_KEY`, `ENVIRONMENT`.
- Service hostnames use **compose DNS names** (`qdrant`, `postgres`), overriding the
  `localhost` defaults in [`.env.example`](../../.env.example) — this is why config must
  come from env, never hardcoded ([`CodingStandards.md`](./CodingStandards.md) §7).

---

## 3. Bootstrap Sequence (`docker compose up`)

```mermaid
sequenceDiagram
    participant Op as Operator
    participant DC as Docker Compose
    participant QD as qdrant
    participant PG as postgres
    participant ING as ingestion
    participant API as api
    participant UI as ui
    participant PR as prometheus
    participant GR as grafana
    Op->>DC: cp .env.example .env (set OPENAI_API_KEY)
    Op->>DC: docker compose up --build -d
    DC->>QD: start → healthcheck /healthz
    DC->>PG: start → pg_isready
    QD-->>DC: healthy
    PG-->>DC: healthy
    Op->>ING: docker compose --profile ingestion up ingestion
    ING->>QD: scrape → parse → chunk → embed → index
    DC->>API: start (waits for qdrant & postgres healthy)
    API-->>DC: /health 200 (healthy)
    DC->>UI: start (waits for API healthy)
    DC->>PR: start → scrape api:8000/metrics
    DC->>GR: start → provision datasource + dashboard
    Op->>GR: open :3000, view dashboard
```

Ordering guarantees from Compose `depends_on ... condition: service_healthy`:
`qdrant` + `postgres` become healthy **before** `api` starts; `ui` waits on healthy `api`;
`ingestion` waits on healthy `qdrant` and `postgres`; `grafana` waits on `prometheus`.

Target: stack healthy in **< 60 s** with images pre-pulled and models cached
([SC-014](../00_project/SUCCESS_CRITERIA.md); build/model-download excluded — see
[`Assumptions.md`](../00_project/Assumptions.md) ASSUMPTION-008).

---

## 4. One-Command Reproducibility

From a clean clone ([SC-024](../00_project/SUCCESS_CRITERIA.md)):

```bash
git clone <repo> && cd RAG_Pokemon
cp .env.example .env                 # set OPENAI_API_KEY (and prod passwords)
make docker-up                       # docker-compose up --build -d  (Makefile)
make ingest                          # OR: docker compose --profile ingestion up ingestion
#   → UI:          http://localhost:8501
#   → API:         http://localhost:8000  (/health, /query, /feedback, /metrics)
#   → Grafana:     http://localhost:3000  (admin/admin — change in prod)
#   → Prometheus:  http://localhost:9090
make docker-down                     # docker-compose down -v  (removes volumes)
```

Relevant `Makefile` targets: `docker-up`, `docker-down`, `ingest`, `seed-db`, `run-api`,
`run-ui`. Reproducibility rests on pinned deps ([`requirements.txt`](../../requirements.txt),
`pyproject.toml`) and pinned images ([SC-019](../00_project/SUCCESS_CRITERIA.md)).

---

## 5. Environment Configuration

All runtime config comes from `.env` (loaded by `config/settings.py`). Minimum to run:

| Variable | Purpose | Prod action |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | LLM + `text-embedding-3-small` access | **required** secret |
| `POSTGRES_USER/PASSWORD/DB` | feedback store creds | override dev defaults |
| `QDRANT_HOST/PORT` | vector DB (set to `qdrant`/`6333` in compose) | internal only |
| `EMBEDDING_MODEL_PRIMARY`, `EMBEDDING_DIMENSION` | `bge-large-en-v1.5`, 1024 | keep in sync with collection |
| `OPENAI_MODEL_NAME`, `OPENAI_TEMPERATURE` | `gpt-4o-mini`, `0.0` | tune per eval |
| `ENVIRONMENT`, `LOG_LEVEL` | runtime mode + logging | `production`, `INFO` |

Full list: [`.env.example`](../../.env.example). See [`Security.md`](./Security.md) §2 for
secret handling.

---

## 6. Cloud Deployment (Bonus — [REQ-020](../00_project/REQUIREMENTS.md) / [SC-023](../00_project/SUCCESS_CRITERIA.md))

A public reachable URL earns the bonus. Three grounded options:

### 6.1 Render (Compose-friendly, simplest)

1. Push repo to GitHub.
2. Create separate **Web Services** from `docker/Dockerfile.app` for the API (`8000`) and UI (`8501`).
3. Add **Managed PostgreSQL** (Render add-on) → set `POSTGRES_*` env vars.
4. Run **Qdrant** as a Render Private Service (from `qdrant/qdrant:v1.7.4`) with a persistent
   disk mounted at `/qdrant/storage`; set `QDRANT_HOST` to its internal address.
5. Set `OPENAI_API_KEY` and other env vars in the Render dashboard (secrets).
6. Run ingestion as a one-off Render Job before first traffic.

### 6.2 Railway

1. New project → deploy service from `docker/Dockerfile.app`.
2. Add Railway **Postgres** plugin (auto-injects `DATABASE_URL`; map to `POSTGRES_*`).
3. Deploy Qdrant from its Docker image with a volume; wire `QDRANT_HOST`.
4. Configure env vars/secrets; expose the API and UI publicly; verify `/health` returns 200.

### 6.3 AWS (most control)

| Concern | AWS service |
| :--- | :--- |
| App container(s) | ECS Fargate (or EKS — see §7) running the API + UI from `Dockerfile.app` |
| Vector DB | Qdrant on ECS/EC2 with EBS volume, **or** Qdrant Cloud |
| Relational | RDS PostgreSQL 15 |
| Secrets | AWS Secrets Manager / SSM Parameter Store → injected as env |
| Ingress/TLS | ALB + ACM certificate → API `:8000` and UI `:8501` |
| Metrics | Prometheus + Grafana on ECS, or Amazon Managed Grafana |

Common steps: build & push images to ECR → define task/service → attach RDS + Qdrant
endpoints via env → run ingestion task once → point ALB at the API and UI.

---

## 7. Kubernetes (IaC reference)

[`deploy/k8s/stack.yaml`](../../deploy/k8s/stack.yaml) provides the reference Kubernetes stack:

- **Namespace** `pokemon-rag`.
- **StatefulSets** for `qdrant` and `postgres` with PVC-backed persistence.
- **Deployments** for `api`, `ui`, `prometheus`, and `grafana`.
- **Job** for `ingestion`.
- **Services** expose `api:8000`, `ui:8501`, `prometheus:9090`, and `grafana:3000`.

To harden this for production, add image pinning, external secrets management, ingress/TLS,
and separate observability storage/retention policies.

---

## 8. Rollback & Data Persistence

### 8.1 Persistence

| Data | Backing store | Volume | Loss on `down -v`? |
| :--- | :--- | :--- | :--- |
| Vector index | Qdrant | `qdrant_storage` | **yes** — re-run `make ingest` to rebuild |
| Feedback + logs | Postgres | `postgres_data` | **yes** — back up before teardown |
| Metrics history | Prometheus | `prometheus_data` | yes (non-critical) |
| Dashboards/state | Grafana | `grafana_data` | yes (dashboard re-provisioned from `docker/grafana/`) |
| Raw/processed/chunks | host bind mount | `./data` | no (persists on host) |

`make docker-down` runs `docker-compose down -v` and **deletes named volumes** — use plain
`docker compose down` (no `-v`) to preserve data across restarts.

### 8.2 Rollback

1. **Application:** pin image tags per release; roll back by redeploying the previous tag
   (K8s: `kubectl rollout undo deployment/pokemon-rag-app`; Compose: change tag + `up -d`).
2. **Data:** back up Postgres (`pg_dump`) and Qdrant snapshots before upgrades; restore on
   rollback. The vector index is fully reproducible from source via `make ingest`.
3. **Config/dashboards:** version-controlled under `config/` and re-provisioned on restart,
   so a bad dashboard/datasource change is reverted by redeploy.
4. **Quality gate:** the retrieval/LLM **regression gate** (baseline in
   `data/evaluation/`) blocks promotion of a change that worsens metrics — see
   [`EvaluationPlan.md`](./EvaluationPlan.md) §6 and [`TestingStrategy.md`](./TestingStrategy.md) §7.

---

## 9. Acceptance Criteria

| ID | Criterion | Verified by |
| :--- | :--- | :--- |
| DEP-AC-1 | All services start via a single `docker compose up` | [REQ-016](../00_project/REQUIREMENTS.md), `make docker-up` |
| DEP-AC-2 | Stack healthy < 60 s (images pre-pulled) | [SC-014](../00_project/SUCCESS_CRITERIA.md) |
| DEP-AC-3 | Clean-clone reproducibility works end-to-end | [SC-024](../00_project/SUCCESS_CRITERIA.md) |
| DEP-AC-4 | `api` healthcheck `/health` green; UI + API reachable | compose healthcheck, [SC-021](../00_project/SUCCESS_CRITERIA.md) |
| DEP-AC-5 | K8s manifests provided | [REQ-020](../00_project/REQUIREMENTS.md), `deploy/k8s/stack.yaml` |
| DEP-AC-6 | (Bonus) public cloud URL reachable, `/health` 200 | [SC-023](../00_project/SUCCESS_CRITERIA.md) |
| DEP-AC-7 | Data persists across `down`/`up` (without `-v`); rollback documented | this doc §8 |

---

## Cross-References

- [`Observability.md`](./Observability.md) — Prometheus scrape, Grafana provisioning.
- [`Security.md`](./Security.md) — port exposure, secrets, TLS.
- [`IndexingPipeline.md`](./IndexingPipeline.md) — ingestion service internals.
- [`SUCCESS_CRITERIA.md`](../00_project/SUCCESS_CRITERIA.md) — SC-014/021/023/024.
- [`REQUIREMENTS.md`](../00_project/REQUIREMENTS.md) — REQ-016, REQ-020.
- [`Assumptions.md`](../00_project/Assumptions.md) — ASSUMPTION-008 (startup timing), ASSUMPTION-009 (cloud).
