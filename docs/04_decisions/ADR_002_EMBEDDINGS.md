# ADR-002: Embedding Model Selection

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture team (Pokemon TCG RAG)

## Context

Dense retrieval encodes both indexed chunks and user queries into vectors that are searched in Qdrant (see [ADR-001](./ADR_001_VECTOR_DB.md)). The choice of embedding model fixes retrieval quality, cost, vector dimensionality, and whether the system can run fully offline. The rubric and the plan ([PlanejamentoRAG_Pokemon](../../PlanejamentoRAG_Pokemon), "Experimentos planejados") explicitly require comparing **at least two** embedding models, so this decision must name a default *and* a comparison model.

The current code already loads the primary model via `sentence-transformers` in [`retrieval/dense.py`](../../src/pokemon_tcg_rag/retrieval/dense.py) (`self.model_name = settings.EMBEDDING_MODEL_PRIMARY`). The configured values in [`settings.py`](../../src/pokemon_tcg_rag/config/settings.py) are:

| Setting | Value |
| :--- | :--- |
| `EMBEDDING_MODEL_PRIMARY` | `BAAI/bge-large-en-v1.5` |
| `EMBEDDING_MODEL_SECONDARY` | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | `1024` |

This ADR satisfies **REQ-006** (dense retrieval with `BAAI/bge-large-en-v1.5`) and feeds **REQ-018** (retrieval evaluation). Comparative methodology is detailed in [EmbeddingStrategy.md](../01_architecture/EmbeddingStrategy.md).

## Decision Drivers

- **DD-1 — Retrieval quality** on English rules/QA text.
- **DD-2 — Offline / self-hosted:** default must run with no external API (the domain data is public but the system should not require paid keys to index or query).
- **DD-3 — Cost:** default should be free; API models incur per-token cost at index and query time.
- **DD-4 — Dimensionality fit:** must match the Qdrant collection (`EMBEDDING_DIMENSION = 1024`).
- **DD-5 — Reproducibility:** pinned, versioned weights (**REQ-017** / reproducibility rubric); `bge-large-en-v1.5` is a fixed checkpoint.
- **DD-6 — Experimentation:** at least two models compared under identical retrieval eval (**REQ-018**).

## Considered Options

### Option A — `BAAI/bge-large-en-v1.5` (chosen default)

| Pros | Cons |
| :--- | :--- |
| Strong English retrieval quality (DD-1) | Larger model → higher local RAM/latency than base |
| Fully offline via `sentence-transformers` (DD-2) | First load downloads ~1.3 GB weights |
| Free (DD-3) | GPU preferred for large batch indexing |
| Native 1024-d output matches the collection (DD-4) | |
| Pinned checkpoint = reproducible (DD-5) | |

### Option B — `text-embedding-3-small` (chosen comparison)

| Pros | Cons |
| :--- | :--- |
| Very good quality with tiny client footprint (DD-1) | Requires `OPENAI_API_KEY`, breaks offline guarantee (DD-2) |
| No local model to host | Per-token cost at both index and query time (DD-3) |
| Simple API integration | Native 1536-d ≠ 1024-d; needs a separate collection or dimension reduction (DD-4) |
| Configured as `EMBEDDING_MODEL_SECONDARY` for A/B (DD-6) | External dependency + rate limits reduce reproducibility (DD-5) |

### Option C — `BAAI/bge-base-en-v1.5`

| Pros | Cons |
| :--- | :--- |
| Lighter/faster than large; free & offline (DD-2, DD-3) | 768-d output ≠ configured 1024-d (DD-4) |
| Same family/tooling as the chosen default | Lower retrieval ceiling than `bge-large` on this domain (DD-1) |

## Decision Outcome

**Chosen: A (`BAAI/bge-large-en-v1.5`) as the production default, with B (`text-embedding-3-small`) retained as the comparison experiment.**

`bge-large-en-v1.5` maximizes offline retrieval quality at zero marginal cost, and its native 1024-d output matches the `pokemon_tcg_rules` collection exactly (DD-1, DD-2, DD-3, DD-4). It is a pinned checkpoint, so indexing is reproducible (DD-5). `text-embedding-3-small` is kept as `EMBEDDING_MODEL_SECONDARY` and benchmarked head-to-head on the 100-question retrieval set to demonstrate multi-approach evaluation and justify the default (DD-6); because it emits 1536-d vectors it is evaluated against a separate parallel collection rather than the production one. `bge-base` is rejected: its 768-d output does not match the configured dimension and it offers no advantage over the large variant given the offline default is already free.

## Consequences

**Positive**
- Zero-cost, offline default enables reproducible indexing without API keys (**REQ-017**).
- Dimension parity with Qdrant avoids reprojection logic on the default path.
- A documented BGE-vs-OpenAI comparison directly earns the retrieval-evaluation rubric points (**REQ-018**).

**Negative**
- Large model raises local memory/latency; batch indexing benefits from GPU.
- The OpenAI comparison requires a second 1536-d collection and a funded key, adding evaluation setup.
- Any future model swap that changes dimensionality forces a Qdrant collection recreation (see [ADR-001](./ADR_001_VECTOR_DB.md)).

## Links

- Requirements: **REQ-006**, **REQ-017**, **REQ-018** — [REQUIREMENTS.md](../00_project/REQUIREMENTS.md)
- Related ADRs: [ADR-001 Vector DB](./ADR_001_VECTOR_DB.md), [ADR-003 Chunking](./ADR_003_CHUNKING.md)
- Sibling docs: [EmbeddingStrategy.md](../01_architecture/EmbeddingStrategy.md), [EvaluationPlan.md](../01_architecture/EvaluationPlan.md)
- Code: [`config/settings.py`](../../src/pokemon_tcg_rag/config/settings.py), [`retrieval/dense.py`](../../src/pokemon_tcg_rag/retrieval/dense.py)
