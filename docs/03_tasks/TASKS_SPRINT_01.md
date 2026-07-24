# TASKS_SPRINT_01 — Foundation & Infrastructure

Granular task specs for **Sprint 1** (`SPRINT_01_FOUNDATION`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** stand up the package skeleton, pinned dependencies, configuration,
domain contracts, logging, and the container skeleton every later task builds on.

---

### TASK-001 — Project scaffold, dependency pinning & tooling

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_01_FOUNDATION |
| **REQ covered** | REQ-016, REQ-017 |
| **Depends on** | — |
| **Unblocks** | TASK-002, TASK-003, TASK-004, TASK-006 |
| **Files affected** | `pyproject.toml`, `requirements.txt`, `.env.example`, `.gitignore`, `Makefile`, `scripts/check_quality.sh`, `src/pokemon_tcg_rag/__init__.py` |
| **Branch** | `chore/task-001-project-scaffold` |

**Description.** Establish the `pokemon_tcg_rag` package under `src/`, pin every runtime and
dev dependency to an exact version, and wire the tooling (ruff, mypy, pytest+coverage) so all
later tasks inherit a green baseline. Grounds REQ-017 (90% coverage gate) and REQ-016
(reproducible, pinned environment).

**Definition of Ready.** Repo cloned; Python 3.11+ available; brief and REQUIREMENTS read.

**Steps.**
1. Verify/complete `pyproject.toml`: `[project]` metadata, `src` layout, and `[tool.ruff]`,
   `[tool.mypy]` (strict), `[tool.pytest.ini_options]` with `--cov=pokemon_tcg_rag --cov-fail-under=90`.
2. Pin all deps in `requirements.txt` with `==` (qdrant-client, sentence-transformers,
   rank-bm25, pymupdf4llm, fastapi, streamlit, sqlalchemy, psycopg2-binary, prometheus-client,
   structlog, ragas/deepeval, pydantic-settings).
3. Provide `.env.example` covering every `Settings` key; ensure `.gitignore` excludes `.env`, `data/`, caches.
4. Add `Makefile` targets (`install`, `lint`, `typecheck`, `test`, `quality`) and
   `scripts/check_quality.sh` running ruff + mypy + pytest.
5. Confirm `import pokemon_tcg_rag` succeeds and `make quality` runs (empty suite passes).

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-001 | `test_package_importable` | unit |
| TEST-002 | `test_requirements_are_pinned` | unit (assert no unpinned lines) |

**Definition of Done.** `make quality` green; package imports; all deps pinned with `==`;
`.env.example` matches `Settings`.

**Acceptance criteria.** A fresh `pip install -r requirements.txt` reproduces the environment;
`ruff`, `mypy`, and `pytest` all run via `make`.

**Commit message.** `chore(scaffold): pin dependencies and configure tooling baseline (TASK-001)`

---

### TASK-002 — Application settings module

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_01_FOUNDATION |
| **REQ covered** | REQ-016 |
| **Depends on** | TASK-001 |
| **Unblocks** | TASK-005, TASK-006, TASK-014, TASK-021, TASK-026 |
| **Files affected** | `src/pokemon_tcg_rag/config/settings.py`, `src/pokemon_tcg_rag/config/__init__.py`, `tests/unit/test_settings.py` |
| **Branch** | `feat/task-002-settings` |

**Description.** Centralize all configuration in a `pydantic-settings` `Settings` class loaded
from `.env`, exposing OpenAI, embeddings, Qdrant, Postgres, retrieval, and path settings plus a
`postgres_uri` property and a cached `get_settings()` accessor. No hardcoded config anywhere else.

**Definition of Ready.** TASK-001 merged; `.env.example` present.

**Steps.**
1. Confirm `Settings` fields match the brief (dim 1024, collection `pokemon_tcg_rules`, RRF k=60,
   top_k dense/bm25=10, final top_k=5, models per brief).
2. Implement `postgres_uri` property and `@lru_cache get_settings()`.
3. Ensure `env_file=".env"`, `extra="ignore"`, and `ENVIRONMENT` literal incl. `"test"`.
4. Write tests loading via monkeypatched env vars.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-003 | `test_settings_defaults` | unit |
| TEST-004 | `test_postgres_uri_composition` | unit |
| TEST-005 | `test_env_override` | unit |
| TEST-006 | `test_get_settings_cached` | unit |

**Definition of Done.** Settings load from env with correct defaults; `postgres_uri` well-formed;
coverage ≥90% on module.

**Acceptance criteria.** No other module reads `os.environ` directly; all config flows through `get_settings()`.

**Commit message.** `feat(config): typed settings loaded from environment (TASK-002)`

---

### TASK-003 — Domain models & enums

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_01_FOUNDATION |
| **REQ covered** | REQ-004, REQ-012 |
| **Depends on** | TASK-001 |
| **Unblocks** | TASK-007, TASK-008, TASK-009, TASK-012, TASK-014, TASK-024, TASK-026, TASK-028, TASK-032, TASK-033 |
| **Files affected** | `src/pokemon_tcg_rag/domain/models.py`, `src/pokemon_tcg_rag/domain/__init__.py`, `tests/unit/test_domain_models.py` |
| **Branch** | `feat/task-003-domain-models` |

**Description.** Freeze the shared domain contracts: enums `DocumentSource`, `RuleType` and
Pydantic models `DocumentMetadata`, `Document`, `Chunk`, `RetrievedChunk`, `AnswerResponse`,
`FeedbackRecord`. These types are the stable interface every downstream task codes against.

**Definition of Ready.** TASK-001 merged. Reference `docs/01_architecture/DomainModel.md`.

**Steps.**
1. Confirm enum members match the sources in [`PROJECT.md`](../00_project/PROJECT.md) §3
   (9 `DocumentSource`, 7 `RuleType`).
2. Confirm `DocumentMetadata` fields: source, document_title, page_number, section_title,
   card_name, rule_type, publication_date, source_url, checksum.
3. Ensure `Chunk` carries `chunk_id`, `document_id`, `text`, `metadata`, optional `embedding`;
   `RetrievedChunk` adds `score`; `AnswerResponse` carries answer, citations, chunks, latency,
   model_name; `FeedbackRecord` carries rating/comment.
4. Add validators (non-empty text, rating ∈ {-1, 1}).

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-007 | `test_document_source_enum_members` | unit |
| TEST-008 | `test_rule_type_enum_members` | unit |
| TEST-009 | `test_chunk_requires_metadata` | unit |
| TEST-010 | `test_feedback_rating_validation` | unit |
| TEST-011 | `test_retrieved_chunk_has_score` | unit |

**Definition of Done.** All models importable, validated, JSON-serializable; ≥90% coverage.

**Acceptance criteria.** No downstream module redefines these types; `conftest.py` fixtures build without error.

**Commit message.** `feat(domain): define core entities and enums (TASK-003)`

---

### TASK-004 — Domain exceptions

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_01_FOUNDATION |
| **REQ covered** | REQ-017 |
| **Depends on** | TASK-001 |
| **Unblocks** | TASK-007, TASK-009, TASK-014, TASK-021 |
| **Files affected** | `src/pokemon_tcg_rag/domain/exceptions.py`, `tests/unit/test_exceptions.py` |
| **Branch** | `feat/task-004-domain-exceptions` |

**Description.** Define the typed exception hierarchy (`PokemonRAGError` base + `IngestionError`,
`ParsingError`, `RetrievalError`, `VectorStoreError`, `LLMError`, `ConfigurationError`) so failures
across layers are catchable and testable rather than raw exceptions.

**Definition of Ready.** TASK-001 merged.

**Steps.**
1. Create `PokemonRAGError(Exception)` base with a `message` attribute.
2. Add one subclass per layer listed above.
3. Document when each is raised in module docstrings.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-012 | `test_exception_hierarchy` | unit |
| TEST-013 | `test_exceptions_carry_message` | unit |

**Definition of Done.** All exceptions subclass the base; importable; ≥90% coverage.

**Acceptance criteria.** Later tasks raise these typed errors, never bare `Exception`.

**Commit message.** `feat(domain): add typed exception hierarchy (TASK-004)`

---

### TASK-005 — Structured JSON logging

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_01_FOUNDATION |
| **REQ covered** | REQ-015 |
| **Depends on** | TASK-002 |
| **Unblocks** | TASK-007, TASK-008, TASK-009 |
| **Files affected** | `src/pokemon_tcg_rag/monitoring/logger.py`, `src/pokemon_tcg_rag/monitoring/__init__.py`, `tests/unit/test_logger.py` |
| **Branch** | `feat/task-005-structured-logging` |

**Description.** Provide `setup_logging()` configuring `structlog` for JSON output at the level
from `Settings.LOG_LEVEL`, so all services emit machine-parseable logs for observability.

**Definition of Ready.** TASK-002 merged.

**Steps.**
1. Implement `setup_logging()` reading `get_settings().LOG_LEVEL`.
2. Configure structlog processors: timestamp, level, JSON renderer.
3. Expose a `get_logger(name)` helper.
4. Test that a logged event serializes to JSON with expected keys.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-014 | `test_setup_logging_json_output` | unit |
| TEST-015 | `test_log_level_from_settings` | unit |

**Definition of Done.** JSON logs emitted; level honored; ≥90% coverage.

**Acceptance criteria.** Any module calling `get_logger()` produces structured JSON lines.

**Commit message.** `feat(monitoring): structured JSON logging via structlog (TASK-005)`

---

### TASK-006 — Docker Compose & service Dockerfiles skeleton

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_01_FOUNDATION |
| **REQ covered** | REQ-016 |
| **Depends on** | TASK-001, TASK-002 |
| **Unblocks** | TASK-011, TASK-039 |
| **Files affected** | `docker-compose.yml`, `docker/Dockerfile.app`, `docker/Dockerfile.ingestion`, `docker/README.md` |
| **Branch** | `feat/task-006-docker-skeleton` |

**Description.** Author the Compose skeleton declaring the six services (qdrant, postgres,
prometheus, grafana, app/api+ui, ingestion) with named volumes, healthchecks, a shared network,
and env wired from `.env`. Later tasks fill in service internals; this establishes REQ-016.

**Definition of Ready.** TASK-001, TASK-002 merged.

**Steps.**
1. Define services with pinned image tags (qdrant, postgres:16, prom/prometheus, grafana/grafana)
   and build contexts for `docker/Dockerfile.app` and `docker/Dockerfile.ingestion`.
2. Add healthchecks and `depends_on` ordering; mount named volumes for qdrant/postgres/grafana.
3. Map ports (Qdrant 6333/6334, Postgres 5432, Prometheus 9090, Grafana 3000, API 8000, UI 8501).
4. Reference env vars from `.env`; run `docker compose config` to validate.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-016 | `test_compose_config_valid` | smoke (`docker compose config`) |
| TEST-017 | `test_all_six_services_declared` | smoke |

**Definition of Done.** `docker compose config` valid; six services + volumes + network present.

**Acceptance criteria.** `docker compose up` starts infra services (qdrant/postgres/prometheus/grafana) healthy even before app code lands.

**Commit message.** `feat(infra): docker-compose skeleton for all services (TASK-006)`

---

## Sprint 1 Definition of Done (roll-up)

- [ ] Package imports; `make quality` green on an empty/near-empty suite.
- [ ] Settings, domain models, exceptions, logging all merged with ≥90% coverage.
- [ ] `docker compose config` valid; infra services boot.
- [ ] All Sprint 1 tasks flipped to `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
