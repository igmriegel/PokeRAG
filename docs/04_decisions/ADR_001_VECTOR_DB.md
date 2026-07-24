# ADR-001: Vector Database Selection

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture team (Pokemon TCG RAG)

## Context

The Pokemon TCG Rules RAG system indexes chunks derived from official rulebooks, tournament handbooks, errata, ban/promo/mega HTML pages, and the Pokegym rulings compendium (see [PROJECT.md](../00_project/PROJECT.md) section 3). Retrieval must support four strategies — Dense, BM25, Hybrid via Reciprocal Rank Fusion (RRF), and Hybrid+Rerank — plus rich metadata filtering (`source`, `rule_type`, `card_name`, `page_number`, `publication_date`) so that a query about, e.g., ban legality can be scoped to the relevant `DocumentSource`.

The vector store must persist 1024-dimensional embeddings (`EMBEDDING_DIMENSION = 1024`) produced by `BAAI/bge-large-en-v1.5` into a single collection, and it must run as a container inside `docker compose` alongside the API, UI, Postgres, Prometheus, and Grafana services. This ADR selects the vector database. It satisfies **REQ-005** (index embeddings into a vector DB) and underpins **REQ-006** / **REQ-008** / **REQ-009**.

The configured target is already reflected in [`settings.py`](../../src/pokemon_tcg_rag/config/settings.py):

| Setting | Value |
| :--- | :--- |
| `QDRANT_HOST` | `localhost` |
| `QDRANT_PORT` | `6333` (REST) |
| `QDRANT_GRPC_PORT` | `6334` (gRPC) |
| `QDRANT_COLLECTION_NAME` | `pokemon_tcg_rules` |
| `EMBEDDING_DIMENSION` | `1024` |

## Decision Drivers

- **DD-1 — Metadata filtering:** must filter on payload fields at query time (e.g. restrict to `rule_type = ban_list`).
- **DD-2 — Hybrid search support:** must fuse dense and lexical results; native sparse/hybrid primitives are a plus (RRF is implemented in-process in [`retrieval/hybrid.py`](../../src/pokemon_tcg_rag/retrieval/hybrid.py) with `RETRIEVAL_HYBRID_RRF_K = 60`).
- **DD-3 — Reranking friendliness:** must return enough candidates (`RETRIEVAL_TOP_K_DENSE = 10`, over-fetched ×2) to feed the `BAAI/bge-reranker-large` cross-encoder.
- **DD-4 — Docker-native operation:** first-class server image for `docker compose up` (**REQ-016**).
- **DD-5 — Cost & offline:** free, self-hosted, no external API dependency.
- **DD-6 — Operational simplicity:** minimal moving parts, a maintained Python client, and clear persistence semantics.

## Considered Options

### Option A — Qdrant (chosen)

| Pros | Cons |
| :--- | :--- |
| Rich payload indexing and filtering (DD-1) | Adds a dedicated service to the compose stack |
| Native named vectors + sparse-vector/hybrid primitives (DD-2) | Team must learn Qdrant-specific collection config |
| Returns scored candidates ideal for a rerank stage (DD-3) | Separate process to operate vs. reusing Postgres |
| Official `qdrant/qdrant` Docker image, REST 6333 + gRPC 6334 (DD-4) | |
| Free, self-hosted, offline (DD-5) | |
| Mature `qdrant-client` Python SDK (DD-6) | |

### Option B — Chroma

| Pros | Cons |
| :--- | :--- |
| Very simple embedded/local mode (DD-6) | Metadata filtering less expressive than Qdrant (DD-1) |
| Free and offline (DD-5) | Weaker/less mature hybrid + sparse-vector story (DD-2) |
| Lightweight Python API | Server/persistence story historically less robust for containerized multi-service deploys (DD-4) |

### Option C — pgvector (PostgreSQL extension)

| Pros | Cons |
| :--- | :--- |
| Reuses the Postgres instance already required for feedback — one fewer service (DD-4, DD-6) | Hybrid search requires hand-rolled SQL joining `tsvector`/BM25-like ranking with vector distance (DD-2) |
| Transactional metadata filtering via plain SQL `WHERE` (DD-1) | Coupling the analytical vector workload to the OLTP feedback DB risks resource contention |
| Free and offline (DD-5) | ANN indexing (HNSW/IVFFlat) tuning is more manual than Qdrant defaults |

## Decision Outcome

**Chosen option: A — Qdrant.**

Qdrant is the only option that satisfies every driver without custom engineering. Its payload filtering directly serves domain-scoped queries (DD-1), it exposes native primitives for hybrid/sparse retrieval that complement the in-process RRF fusion (DD-2), it returns cleanly scored candidate lists that feed the cross-encoder rerank stage (DD-3), and it ships as a first-class Docker service exposing REST `6333` and gRPC `6334` that slots into `docker compose` (DD-4). It is free and fully offline (DD-5) with a mature Python client (DD-6).

pgvector's appeal — reusing Postgres — is outweighed by the manual hybrid-search SQL and the risk of coupling vector workloads to the transactional feedback store. Chroma's simplicity does not compensate for its weaker filtering and hybrid capabilities. The system commits to a single collection `pokemon_tcg_rules` of dimension `1024`.

## Consequences

**Positive**
- Native metadata filtering enables source-scoped retrieval and precise citation.
- One collection, one clear indexing target — reproducible via [`scripts/seed_db.py`](../../scripts/seed_db.py) and the ingestion service.
- Docker-native deployment keeps the whole stack in `docker compose up` (**REQ-016**).
- Scored candidate lists integrate cleanly with the RRF and rerank stages.

**Negative**
- Adds a standalone service (extra container, port surface, and persistence volume to operate).
- Qdrant-specific collection configuration and client code become a project dependency.
- The 1024-d assumption is coupled to the primary embedding model; switching to a different-dimension model requires recreating the collection (see [ADR-002](./ADR_002_EMBEDDINGS.md)).

## Links

- Requirements: **REQ-005**, **REQ-006**, **REQ-008**, **REQ-009**, **REQ-016** — [REQUIREMENTS.md](../00_project/REQUIREMENTS.md)
- Related ADRs: [ADR-002 Embeddings](./ADR_002_EMBEDDINGS.md), [ADR-004 Reranking](./ADR_004_RERANKING.md)
- Sibling docs: [DataModel.md](../01_architecture/DataModel.md), [RetrievalPipeline.md](../01_architecture/RetrievalPipeline.md), [Deployment.md](../01_architecture/Deployment.md)
- Code: [`config/settings.py`](../../src/pokemon_tcg_rag/config/settings.py), [`retrieval/dense.py`](../../src/pokemon_tcg_rag/retrieval/dense.py), [`retrieval/hybrid.py`](../../src/pokemon_tcg_rag/retrieval/hybrid.py)
