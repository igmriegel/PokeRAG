# TASKS_SPRINT_03 — Normalization, Chunking & Indexing

Granular task specs for **Sprint 3** (`SPRINT_03_CHUNKING_INDEXING`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** turn raw `Document`s into normalized, metadata-rich `Chunk`s, then embed
and index them into the Qdrant collection `pokemon_tcg_rules` (dim 1024).

---

### TASK-012 — Document normalizer

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_03_CHUNKING_INDEXING |
| **REQ covered** | REQ-004 |
| **Depends on** | TASK-003, TASK-010 |
| **Unblocks** | TASK-013 |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/normalizer.py`, `tests/unit/test_normalizer.py` |
| **Branch** | `feat/task-012-normalizer` |

**Description.** Implement `DocumentNormalizer.normalize(document)` cleaning whitespace, fixing
PDF de-hyphenation, normalizing unicode, stripping artifacts, and computing a stable `checksum`,
returning a cleaned `Document` while preserving all metadata.

**Definition of Ready.** TASK-003, TASK-010 merged.

**Steps.**
1. Collapse repeated whitespace/newlines; join hyphen-broken words.
2. NFKC unicode normalization; strip control chars.
3. Recompute `checksum` (sha256 of normalized text) into metadata.
4. Guarantee metadata is unchanged except `checksum`.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-034 | `test_whitespace_collapsed` | unit |
| TEST-035 | `test_dehyphenation` | unit |
| TEST-036 | `test_unicode_normalized` | unit |
| TEST-037 | `test_metadata_preserved` | unit |

**Definition of Done.** Normalization deterministic; metadata preserved; ≥90% coverage.

**Acceptance criteria.** Same input → identical normalized text + checksum across runs.

**Commit message.** `feat(ingestion): document text normalizer (TASK-012)`

---

### TASK-013 — Document chunker

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_03_CHUNKING_INDEXING |
| **REQ covered** | REQ-004 |
| **Depends on** | TASK-012 |
| **Unblocks** | TASK-015, TASK-016, TASK-018 |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/chunker.py`, `tests/unit/test_chunker.py` |
| **Branch** | `feat/task-013-chunker` |

**Description.** Implement `DocumentChunker(chunk_size=512, chunk_overlap=64).chunk_document(document)`
producing `Chunk`s with unique `chunk_id`, propagated metadata, and configurable token size/overlap.
Pokegym Q&A stays a single chunk; long PDF sections split with overlap.

**Definition of Ready.** TASK-012 merged.

**Steps.**
1. Token-aware splitting at `chunk_size` with `chunk_overlap`.
2. Single-chunk path for Pokegym rulings (source == POKEGYM).
3. Generate deterministic `chunk_id` (`{document_id}#{index}`); copy metadata.
4. Handle empty/short documents and very long paragraphs.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-038 | `test_chunk_size_respected` | unit |
| TEST-039 | `test_overlap_applied` | unit |
| TEST-040 | `test_metadata_propagated` | unit |
| TEST-041 | `test_empty_document` | unit |
| TEST-042 | `test_pokegym_single_chunk` | unit |
| TEST-043 | `test_unicode_and_long_paragraph` | unit |

**Definition of Done.** Chunks respect size/overlap; metadata propagated; edge cases covered; ≥90%.

**Acceptance criteria.** No chunk exceeds `chunk_size`; Pokegym ruling yields exactly one chunk.

**Commit message.** `feat(ingestion): configurable token chunker (TASK-013)`

---

### TASK-014 — Qdrant vector store client

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_03_CHUNKING_INDEXING |
| **REQ covered** | REQ-005 |
| **Depends on** | TASK-002, TASK-003 |
| **Unblocks** | TASK-015, TASK-017 |
| **Files affected** | `src/pokemon_tcg_rag/storage/vector_db.py`, `src/pokemon_tcg_rag/storage/__init__.py`, `tests/unit/test_vector_db.py` |
| **Branch** | `feat/task-014-qdrant-client` |

**Description.** Implement `VectorDatabase` wrapping the Qdrant client: `init_collection()`
(collection `pokemon_tcg_rules`, size 1024, cosine), `upsert_chunks(chunks)` writing vectors +
metadata payload, and `search_dense(query_vector, top_k)` returning `RetrievedChunk`s with scores
and payload filtering support.

**Definition of Ready.** TASK-002, TASK-003 merged; Qdrant reachable or client mocked.

**Steps.**
1. Init client from settings (host/port/grpc/api_key); `init_collection` idempotent.
2. `upsert_chunks`: map `Chunk`→point (vector + payload from metadata).
3. `search_dense`: query, map hits→`RetrievedChunk` with `score`; support payload filters (rule_type, source).
4. Raise `VectorStoreError` on client failure.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-044 | `test_init_collection_dim_1024` | unit (mocked client) |
| TEST-045 | `test_upsert_maps_payload` | unit |
| TEST-046 | `test_search_returns_retrieved_chunks` | unit |
| TEST-047 | `test_search_error_raises` | unit |
| TEST-048 | `test_upsert_search_roundtrip` | integration (real Qdrant, marked) |

**Definition of Done.** Collection init idempotent; upsert/search work against mocked + (marked) real Qdrant; ≥90%.

**Acceptance criteria.** Round-trip: upsert N chunks → `search_dense` returns them ranked by score.

**Commit message.** `feat(storage): qdrant vector store client (TASK-014)`

---

### TASK-015 — Embedding & indexing job

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_03_CHUNKING_INDEXING |
| **REQ covered** | REQ-005 |
| **Depends on** | TASK-013, TASK-014 |
| **Unblocks** | TASK-016 |
| **Files affected** | `scripts/seed_db.py`, `tests/integration/test_indexing.py` |
| **Branch** | `feat/task-015-indexing-job` |

**Description.** Implement `scripts/seed_db.py`: load processed chunks, embed them with the primary
model `BAAI/bge-large-en-v1.5` (1024-d) in batches, and upsert into Qdrant via `VectorDatabase`.

**Definition of Ready.** TASK-013, TASK-014 merged.

**Steps.**
1. Load chunks (from `data/chunks/` or produced in-memory); load SentenceTransformer (BGE).
2. Batch-encode texts to 1024-d vectors; attach to `Chunk.embedding`.
3. `init_collection()` then `upsert_chunks()`; log indexed count.
4. Add `make seed` target; idempotent re-runs.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-049 | `test_embedding_dimension_1024` | integration (small model or mocked) |
| TEST-050 | `test_seed_upserts_all_chunks` | integration (mocked embed + Qdrant) |
| TEST-051 | `test_seed_idempotent` | integration |

**Definition of Done.** Chunks embedded to 1024-d and indexed; idempotent; ≥90%.

**Acceptance criteria.** After seeding, Qdrant reports point count == number of chunks.

**Commit message.** `feat(indexing): embed chunks and seed qdrant (TASK-015)`

---

### TASK-016 — Ingestion→index integration + chunks Parquet

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_03_CHUNKING_INDEXING |
| **REQ covered** | REQ-004, REQ-005 |
| **Depends on** | TASK-013, TASK-015 |
| **Unblocks** | — |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/pipeline.py`, `tests/integration/test_ingestion_pipeline.py` |
| **Branch** | `feat/task-016-pipeline-index-integration` |

**Description.** Extend `IngestionPipeline.run()` to normalize → chunk all Documents, persist
chunks as Parquet to `data/chunks/`, and (optionally) trigger the indexing job — wiring the full
raw→processed→chunks→indexed flow.

**Definition of Ready.** TASK-013, TASK-015 merged.

**Steps.**
1. After aggregation, run `DocumentNormalizer` then `DocumentChunker` over all Documents.
2. Persist chunks to `data/chunks/*.parquet`; return `list[Chunk]`.
3. Add `--index` flag delegating to the seed job.
4. Assert counts: documents → chunks → indexed points are consistent.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-052 | `test_pipeline_produces_chunks` | integration |
| TEST-053 | `test_chunks_parquet_written` | integration |
| TEST-054 | `test_end_to_end_counts_consistent` | integration (mocked embed/Qdrant) |

**Definition of Done.** Full raw→chunks flow runs; Parquet written; counts consistent; ≥90%.

**Acceptance criteria.** `run(index=True)` ends with Qdrant point count == chunk count.

**Commit message.** `feat(ingestion): wire normalize/chunk/index into pipeline (TASK-016)`

---

## Sprint 3 Definition of Done (roll-up)

- [ ] Documents normalized and chunked with propagated metadata.
- [ ] Qdrant collection `pokemon_tcg_rules` (dim 1024) created and populated.
- [ ] Full ingestion→index flow runs from the pipeline; ≥90% coverage per module.
- [ ] Sprint 3 tasks marked `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
