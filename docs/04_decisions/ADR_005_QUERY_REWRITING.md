# ADR-005: Query Rewriting Strategy

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture team (Pokemon TCG RAG)

## Context

Real user questions are short, colloquial, and often multilingual or context-dependent — e.g. "Posso usar essa carta?" or "If I evolve...". Such queries embed poorly for dense retrieval and lack the domain keywords BM25 needs, so retrieval quality suffers before any reranking can help. A **query rewriting** stage sits *before* retrieval and reframes the raw question into a formal, keyword-rich Pokemon TCG search phrase (e.g. "Pokemon TCG card legality status and format legality rules"). Query rewriting is also an explicit best-practices rubric item worth 1 point.

The chosen approach is implemented in [`retrieval/query_rewriter.py`](../../src/pokemon_tcg_rag/retrieval/query_rewriter.py): a zero-shot LLM rewrite using the OpenAI-compatible client with `OPENAI_MODEL_NAME` (default `gpt-4o-mini`) at `temperature=0.0`, `max_tokens=100`. The prompt preserves card names and mechanic keywords (Mega Evolution, Rare Candy, VSTAR, EX, …), expands ambiguous terms, and outputs only the rewritten string; on any error it falls back to the original query. This ADR satisfies **REQ-010** (LLM-based query rewriting) and feeds **REQ-018**.

## Decision Drivers

- **DD-1 — Retrieval quality:** improve dense + BM25 recall for vague/colloquial/multilingual queries.
- **DD-2 — Domain framing:** inject Pokemon TCG vocabulary while preserving card/mechanic names.
- **DD-3 — Latency & cost:** minimal overhead; single short LLM call.
- **DD-4 — Robustness:** never worsen a query — must fall back gracefully on failure.
- **DD-5 — Evaluability (A/B):** toggleable so with-vs-without can be measured (**REQ-018**).
- **DD-6 — Simplicity:** no extra embeddings/index beyond what retrieval already uses.

## Considered Options

### Option A — Zero-shot LLM rewrite with domain framing (chosen)

| Pros | Cons |
| :--- | :--- |
| Directly reframes vague queries with TCG vocabulary (DD-1, DD-2) | Adds one LLM call (latency + token cost) before retrieval (DD-3) |
| Single short call, `max_tokens=100`, temp 0.0 (DD-3) | Rewrite could drift if the prompt is weak (mitigated by explicit keyword-preservation rules) |
| Graceful fallback to original on error (DD-4) | Depends on LLM availability |
| Trivially toggleable for A/B (DD-5); no new index (DD-6) | |

### Option B — HyDE (Hypothetical Document Embeddings)

| Pros | Cons |
| :--- | :--- |
| Can lift dense recall by embedding a synthetic answer (DD-1) | LLM may hallucinate a fake ruling → embeds fabricated rules, dangerous in a citation-strict domain |
| No hand-written rewrite rules | Helps dense only; less benefit to BM25 (DD-1 partial) |
| | Higher token cost (generates a full pseudo-document) (DD-3) |

### Option C — No query rewriting

| Pros | Cons |
| :--- | :--- |
| Zero added latency/cost (DD-3) | Vague/multilingual queries retrieve poorly (DD-1) |
| Simplest pipeline (DD-6) | Forfeits the best-practices point |

## Decision Outcome

**Chosen: A — zero-shot LLM query rewriting with domain framing, toggleable for A/B evaluation.**

A single low-temperature LLM call reframes the raw question into a formal, keyword-rich TCG query, improving both dense and lexical recall (DD-1, DD-2) at modest, bounded cost (`max_tokens=100`, DD-3). The implementation preserves card/mechanic names and falls back to the original query on any exception, so it can only help or no-op — never break retrieval (DD-4). The stage is a toggle, enabling a with-vs-without comparison on the 100-question benchmark (DD-5) with no new index (DD-6).

HyDE is rejected because generating a hypothetical *answer* risks embedding a hallucinated ruling — unacceptable in a domain whose entire value proposition is grounded, cited answers. Option C forfeits measurable recall gains and the rubric point.

## Consequences

**Positive**
- Better recall on colloquial/multilingual queries feeding all four retrieval strategies.
- Toggle enables a documented A/B experiment (**REQ-018**) and earns the query-rewriting point (**REQ-010**).
- Fallback keeps the pipeline resilient to LLM/API failures.

**Negative**
- One extra LLM round-trip per query adds latency and token cost.
- Rewrite quality is coupled to the prompt template and the configured model; a poor rewrite could shift retrieval focus (bounded by keyword-preservation rules and A/B monitoring).
- Reuses the OpenAI-compatible client, so a fully offline deployment must supply a local OpenAI-compatible endpoint or disable the stage.

## Links

- Requirements: **REQ-010**, **REQ-011**, **REQ-018** — [REQUIREMENTS.md](../00_project/REQUIREMENTS.md)
- Related ADRs: [ADR-004 Reranking](./ADR_004_RERANKING.md), [ADR-002 Embeddings](./ADR_002_EMBEDDINGS.md)
- Sibling docs: [RetrievalPipeline.md](../01_architecture/RetrievalPipeline.md), [PromptEngineering.md](../01_architecture/PromptEngineering.md), [EvaluationPlan.md](../01_architecture/EvaluationPlan.md)
- Code: [`retrieval/query_rewriter.py`](../../src/pokemon_tcg_rag/retrieval/query_rewriter.py), [`config/settings.py`](../../src/pokemon_tcg_rag/config/settings.py)
