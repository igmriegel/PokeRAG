# ADR-003: Document Chunking Strategy

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture team (Pokemon TCG RAG)

## Context

The corpus mixes two structurally different content types (see [PROJECT.md](../00_project/PROJECT.md) section 3 and the plan's Fase 2):

1. **Pokegym rulings compendium** — naturally atomic **Question → Answer** units, each already a self-contained ruling with `card_name`, `publication_date`, and `source_url`.
2. **Official PDFs and HTML pages** (rulebook, tournament/alternative-play handbooks, errata, deck-list guide, ban/promo/mega pages) — long-form prose organized as **sections → paragraphs**.

Chunk quality directly bounds retrieval Recall and citation precision. Over-large chunks dilute dense similarity and BM25 term weighting; over-small chunks fragment a single ruling across records. The plan mandates a chunking experiment (Fixed × Semantic, and chunk size 256 × 512 × 1024 tokens). This ADR satisfies **REQ-004** (normalize and chunk into tokenized segments with metadata) and feeds **REQ-018**.

The current [`ingestion/chunker.py`](../../src/pokemon_tcg_rag/ingestion/chunker.py) implements fixed-size overlapping chunking with defaults `chunk_size=512`, `chunk_overlap=64`, propagating `document.metadata` onto every `Chunk`. This ADR formalizes that default and defines the hybrid policy around it.

## Decision Drivers

- **DD-1 — Preserve ruling atomicity:** a Pokegym Q&A must not be split (splitting an answer away from its question destroys meaning).
- **DD-2 — Retrieval granularity:** PDF chunks small enough for precise matching, large enough to carry a coherent rule.
- **DD-3 — Metadata & citation fidelity:** every chunk keeps `source`, `page_number`, `section_title`, `card_name`, `rule_type` for citation (**REQ-012**).
- **DD-4 — Context continuity:** overlap so a rule spanning a boundary is not lost.
- **DD-5 — Experimentation:** support a chunk-size sweep for evaluation (**REQ-018**).
- **DD-6 — Implementation simplicity & reproducibility:** deterministic, testable chunking (`test_chunk_size`, `test_overlap`, `test_preserve_metadata`).

## Considered Options

### Option A — Fixed-size overlapping chunks everywhere

| Pros | Cons |
| :--- | :--- |
| Simple, deterministic, easy to test (DD-6) | Splits atomic Pokegym Q&A across records (violates DD-1) |
| Overlap preserves cross-boundary context (DD-4) | Ignores document structure; may cut mid-section |
| Trivial to sweep sizes 256/512/1024 (DD-5) | |

### Option B — Semantic / section-based chunks everywhere

| Pros | Cons |
| :--- | :--- |
| Respects document structure; clean section boundaries (DD-2, DD-3) | Section sizes vary wildly; long sections exceed model context |
| Good for well-structured PDFs | Requires reliable heading detection; brittle on messy PDF layout |
| | Harder to run a clean fixed-token-size sweep (DD-5) |

### Option C — Per-record chunking driven only by source type (per-Q&A only)

| Pros | Cons |
| :--- | :--- |
| Perfect for Pokegym Q&A atomicity (DD-1) | No strategy for long PDF prose — would create huge chunks (DD-2) |
| Maximal citation precision for rulings (DD-3) | Not a complete solution on its own |

### Option D — Hybrid: per-Q&A for Pokegym + section→paragraph fixed-overlap for PDFs (chosen)

| Pros | Cons |
| :--- | :--- |
| Keeps rulings atomic (DD-1) and prose granular (DD-2) | Two code paths to maintain |
| Full metadata propagation on both paths (DD-3) | Requires source-type dispatch in the chunker |
| Fixed 512/64 default is deterministic and sweepable (DD-4, DD-5, DD-6) | |

## Decision Outcome

**Chosen: D — a hybrid, source-aware strategy.**

- **Pokegym rulings:** one chunk per Question→Answer ruling (Option C behavior), preserving atomicity and per-ruling metadata (DD-1, DD-3).
- **PDFs / HTML prose:** normalize into sections → paragraphs, then apply the fixed-size overlapping splitter with the configured defaults **`chunk_size = 512`, `chunk_overlap = 64`** as implemented in [`ingestion/chunker.py`](../../src/pokemon_tcg_rag/ingestion/chunker.py) (DD-2, DD-4).
- **Experiment:** the `256 / 512 / 1024`-token sweep is run over the retrieval benchmark to pick the best default, with `512/64` as the accepted baseline (DD-5).

This captures the strengths of each pure approach where each is appropriate, while the fixed splitter keeps the PDF path deterministic and testable (DD-6). Options A and B are rejected as single-strategy answers that each fail one content type; Option C is incomplete for long-form prose.

## Consequences

**Positive**
- Rulings stay retrievable and citable as whole units; long documents become granular.
- Uniform metadata propagation preserves citation quality (**REQ-012**).
- The chunk-size sweep provides evidence for the chosen configuration (**REQ-018**).

**Negative**
- Source-type dispatch adds branching and a second test surface in the ingestion path.
- The current chunker splits on whitespace-token counts (word count), which approximates — but is not identical to — model token counts; the sweep must account for this. This approximation is recorded in [Assumptions.md](../00_project/Assumptions.md).
- Section/paragraph segmentation quality depends on upstream PDF normalization ([`ingestion/normalizer.py`](../../src/pokemon_tcg_rag/ingestion/normalizer.py)).

## Links

- Requirements: **REQ-004**, **REQ-012**, **REQ-018** — [REQUIREMENTS.md](../00_project/REQUIREMENTS.md)
- Related ADRs: [ADR-002 Embeddings](./ADR_002_EMBEDDINGS.md), [ADR-006 Ingestion Orchestrator](./ADR_006_INGESTION_ORCHESTRATOR.md)
- Sibling docs: [IndexingPipeline.md](../01_architecture/IndexingPipeline.md), [DataModel.md](../01_architecture/DataModel.md), [Assumptions.md](../00_project/Assumptions.md)
- Code: [`ingestion/chunker.py`](../../src/pokemon_tcg_rag/ingestion/chunker.py), [`ingestion/pipeline.py`](../../src/pokemon_tcg_rag/ingestion/pipeline.py)
