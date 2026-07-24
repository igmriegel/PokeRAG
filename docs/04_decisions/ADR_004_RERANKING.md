# ADR-004: Re-ranking Strategy

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture team (Pokemon TCG RAG)

## Context

The retrieval layer's fourth strategy is **Hybrid + Re-ranking**: after Hybrid RRF fusion produces a candidate set, a cross-encoder re-scores each `(query, chunk)` pair to sharpen top-of-list precision before the LLM sees the context. First-stage retrievers (dense bi-encoder, BM25) score query and document independently; a cross-encoder jointly attends to both and is markedly more precise, which matters when a citation must point to the exact governing rule. Re-ranking is also an explicit best-practices rubric item worth 1 point.

The pipeline over-fetches (`RETRIEVAL_TOP_K_DENSE = 10` / `RETRIEVAL_TOP_K_BM25 = 10`, fused via RRF) and the reranker trims to `RETRIEVAL_FINAL_TOP_K = 5`. The chosen model is already wired into [`retrieval/reranker.py`](../../src/pokemon_tcg_rag/retrieval/reranker.py) via `sentence-transformers` `CrossEncoder`, reading `RERANKER_MODEL` from [`settings.py`](../../src/pokemon_tcg_rag/config/settings.py):

| Setting | Value |
| :--- | :--- |
| `RERANKER_MODEL` | `BAAI/bge-reranker-large` |
| `RETRIEVAL_FINAL_TOP_K` | `5` |

This ADR satisfies **REQ-009** (cross-encoder re-ranking) and contributes to **REQ-018**.

## Decision Drivers

- **DD-1 — Precision gain:** meaningfully improve top-5 relevance over Hybrid RRF alone.
- **DD-2 — Offline / self-hosted:** default must run without an external API.
- **DD-3 — Cost:** default free; API rerankers bill per query/document.
- **DD-4 — Latency:** acceptable added latency for re-scoring ~20 candidates.
- **DD-5 — Reproducibility:** pinned model weights (**REQ-017**).
- **DD-6 — Flexibility:** allow an alternative API reranker for comparison without rewriting the pipeline.

## Considered Options

### Option A — `BAAI/bge-reranker-large` cross-encoder, local (chosen default)

| Pros | Cons |
| :--- | :--- |
| Strong cross-encoder precision on English (DD-1) | CPU inference is the latency hotspot; GPU preferred (DD-4) |
| Fully offline via `sentence-transformers` `CrossEncoder` (DD-2) | Adds model weights to the image/volume |
| Free (DD-3) | Higher memory footprint than a bi-encoder |
| Pinned checkpoint = reproducible (DD-5) | |
| Already implemented in `retrieval/reranker.py` | |

### Option B — Cohere Rerank (API)

| Pros | Cons |
| :--- | :--- |
| High quality, no local model to host | Requires an API key; breaks offline guarantee (DD-2) |
| Offloads compute; low local memory | Per-call cost at query time (DD-3) |
| Simple API | Network latency + rate limits; external reproducibility risk (DD-4, DD-5) |

### Option C — No re-ranking (Hybrid RRF only)

| Pros | Cons |
| :--- | :--- |
| Lowest latency; simplest (DD-4) | Forfeits the precision gain and the rubric point (DD-1) |
| No extra model/dependency | RRF fusion alone leaves near-duplicate/weak candidates near the top |

## Decision Outcome

**Chosen: A (`BAAI/bge-reranker-large`, local) as default, with B (Cohere Rerank) available as an optional, config-swappable backend.**

The local BGE cross-encoder delivers the precision lift that motivates the whole rerank stage (DD-1) while remaining free and offline (DD-2, DD-3) and reproducible via a pinned checkpoint (DD-5). It is already integrated and re-scores the fused candidate set down to `RETRIEVAL_FINAL_TOP_K = 5`. Cohere Rerank is retained as an optional comparison backend selected behind the same reranker interface, so it can be A/B-tested (DD-6) without touching the retrieval pipeline. Option C is rejected: it forgoes both the measurable precision gain and the best-practices point.

## Consequences

**Positive**
- Higher top-5 relevance → better citation accuracy and downstream faithfulness.
- Free, offline, reproducible default earns the re-ranking rubric point (**REQ-009**).
- The optional Cohere path enables a documented rerank comparison (**REQ-018**).

**Negative**
- Cross-encoder scoring is the pipeline's main latency contributor on CPU; a GPU or a smaller reranker may be needed to meet latency targets.
- Adds model weights to the container image / cache volume.
- Maintaining two reranker backends requires a stable abstraction and duplicate configuration.

## Links

- Requirements: **REQ-009**, **REQ-017**, **REQ-018** — [REQUIREMENTS.md](../00_project/REQUIREMENTS.md)
- Related ADRs: [ADR-001 Vector DB](./ADR_001_VECTOR_DB.md), [ADR-005 Query Rewriting](./ADR_005_QUERY_REWRITING.md)
- Sibling docs: [RetrievalPipeline.md](../01_architecture/RetrievalPipeline.md), [EvaluationPlan.md](../01_architecture/EvaluationPlan.md), [PromptEngineering.md](../01_architecture/PromptEngineering.md)
- Code: [`retrieval/reranker.py`](../../src/pokemon_tcg_rag/retrieval/reranker.py), [`retrieval/hybrid.py`](../../src/pokemon_tcg_rag/retrieval/hybrid.py), [`config/settings.py`](../../src/pokemon_tcg_rag/config/settings.py)
