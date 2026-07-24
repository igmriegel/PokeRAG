# TASKS_SPRINT_08 — Monitoring & Deployment

Granular task specs for **Sprint 8** (`SPRINT_08_MONITORING_DEPLOY`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** ship Prometheus metrics + a Grafana dashboard (≥5 charts), verify the full
Docker Compose stack with smoke tests, and provide cloud deployment IaC. See
[`Observability.md`](../01_architecture/Observability.md) and
[`Deployment.md`](../01_architecture/Deployment.md).

---

### TASK-037 — Prometheus metrics collector

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_08_MONITORING_DEPLOY |
| **REQ covered** | REQ-015 |
| **Depends on** | TASK-029 |
| **Unblocks** | TASK-038 |
| **Files affected** | `src/pokemon_tcg_rag/monitoring/metrics_collector.py`, `src/pokemon_tcg_rag/api/main.py`, `tests/unit/test_metrics_collector.py` |
| **Branch** | `feat/task-037-metrics-collector` |

**Description.** Implement `MetricsCollector` with `prometheus-client` counters/histograms
(`record_query(model, latency, num_docs, status)`, `record_feedback(rating)`) and expose a
`/metrics` endpoint on the API for Prometheus scraping.

**Definition of Ready.** TASK-029 merged.

**Steps.**
1. Define metrics: query count, query latency histogram, retrieved-doc count, feedback counters by rating, source-distribution.
2. Implement `record_query` / `record_feedback`; call them from the `/query` and `/feedback` routes.
3. Mount a `/metrics` ASGI endpoint in `main.py`.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-118 | `test_record_query_increments` | unit |
| TEST-119 | `test_record_feedback_by_rating` | unit |
| TEST-120 | `test_metrics_endpoint_exposes_prometheus` | integration (TestClient) |

**Definition of Done.** Metrics recorded and exposed at `/metrics`; routes instrumented; ≥90%.

**Acceptance criteria.** `GET /metrics` returns Prometheus text with query/feedback series.

**Commit message.** `feat(monitoring): prometheus metrics collector and /metrics (TASK-037)`

---

### TASK-038 — Prometheus config + Grafana dashboard (≥5 charts)

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_08_MONITORING_DEPLOY |
| **REQ covered** | REQ-015 |
| **Depends on** | TASK-037 |
| **Unblocks** | TASK-039 |
| **Files affected** | `docker/prometheus/prometheus.yml`, `docker/grafana/provisioning/`, `docker/grafana/dashboards/pokemon_rag.json`, `docker-compose.yml` (prometheus/grafana services) |
| **Branch** | `feat/task-038-grafana-dashboard` |

**Description.** Configure Prometheus to scrape the API `/metrics` and provision a Grafana
dashboard with **at least 5 charts**: queries per day, average latency, retrieved-doc count,
positive vs negative feedback, and source distribution / top questions.

**Definition of Ready.** TASK-037 merged.

**Steps.**
1. `prometheus.yml`: scrape job for the API target.
2. Grafana provisioning: datasource (Prometheus) + dashboard JSON auto-load.
3. Author `pokemon_rag.json` with ≥5 panels covering the metrics above.
4. Wire prometheus/grafana services + volumes in compose.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-121 | `test_prometheus_config_valid_yaml` | smoke |
| TEST-122 | `test_dashboard_has_min_5_panels` | smoke (parse JSON) |
| TEST-123 | `test_grafana_datasource_provisioned` | smoke |

**Definition of Done.** Prometheus scrapes the API; Grafana auto-loads a ≥5-panel dashboard; configs validate.

**Acceptance criteria.** Grafana shows ≥5 populated charts after traffic flows through the API.

**Commit message.** `feat(monitoring): prometheus scrape config and grafana dashboard (TASK-038)`

---

### TASK-039 — Full Docker Compose integration + smoke tests

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_08_MONITORING_DEPLOY |
| **REQ covered** | REQ-016 |
| **Depends on** | TASK-011, TASK-029, TASK-030, TASK-038 |
| **Unblocks** | TASK-040 |
| **Files affected** | `docker-compose.yml`, `docker/Dockerfile.app`, `tests/smoke/test_services_health.py`, `README.md` |
| **Branch** | `feat/task-039-compose-integration` |

**Description.** Finalize the full stack so `docker compose up` brings up qdrant, postgres,
prometheus, grafana, api, ui, and ingestion — all healthy and wired — and add smoke tests that
verify service health and a basic query round-trip.

**Definition of Ready.** TASK-011, TASK-029, TASK-030, TASK-038 merged.

**Steps.**
1. Finalize `Dockerfile.app` (serves API + UI) and all service commands/ports/env in compose.
2. Ensure `depends_on` + healthchecks order startup (qdrant/postgres before api).
3. Smoke tests: `/health` 200, Qdrant reachable, Postgres connects, a stub `/query` responds.
4. Update `README.md` run instructions (`docker compose up`).

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-124 | `test_all_services_healthy` | smoke |
| TEST-125 | `test_end_to_end_query_roundtrip` | smoke |
| TEST-126 | `test_postgres_and_qdrant_reachable` | smoke |

**Definition of Done.** `docker compose up` yields a healthy stack; smoke tests green; README updated.

**Acceptance criteria.** A clean `docker compose up` serves UI + API and answers a query within the SLA.

**Commit message.** `feat(deploy): full docker-compose integration and smoke tests (TASK-039)`

---

### TASK-040 — Cloud deployment IaC

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_08_MONITORING_DEPLOY |
| **REQ covered** | REQ-020 |
| **Depends on** | TASK-039 |
| **Unblocks** | — |
| **Files affected** | `deploy/k8s/*.yaml`, `deploy/render.yaml`, `docs/01_architecture/Deployment.md` |
| **Branch** | `feat/task-040-cloud-iac` |

**Description.** Provide cloud deployment manifests (Kubernetes and/or Render/Railway) mirroring
the compose topology, targeting the bonus "deployment to the cloud" rubric points.

**Definition of Ready.** TASK-039 merged.

**Steps.**
1. Author K8s manifests (Deployments/Services/PVCs for api, ui, qdrant, postgres, prometheus, grafana) or a `render.yaml`.
2. Externalize secrets/config via env/secret objects.
3. Document the deploy procedure in `Deployment.md`.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-127 | `test_k8s_manifests_valid` | smoke (`kubectl --dry-run` / yaml parse) |
| TEST-128 | `test_all_services_have_manifests` | smoke |

**Definition of Done.** Valid IaC covering every service; deploy documented.

**Acceptance criteria.** Manifests validate and a documented procedure deploys the stack to a cloud target.

**Commit message.** `feat(deploy): cloud deployment IaC manifests (TASK-040)`

---

## Sprint 8 Definition of Done (roll-up)

- [ ] Prometheus metrics exposed; Grafana dashboard with ≥5 charts provisioned.
- [ ] `docker compose up` brings the full stack healthy; smoke tests green.
- [ ] Cloud IaC provided and documented.
- [ ] Sprint 8 tasks `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md); project rubric-complete.
