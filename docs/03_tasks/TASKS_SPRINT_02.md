# TASKS_SPRINT_02 — Ingestion: Scraping & PDF Parsing

Granular task specs for **Sprint 2** (`SPRINT_02_INGESTION`). Index:
[`TASK_INDEX.md`](./TASK_INDEX.md) · Graph: [`TASK_DEPENDENCY_GRAPH.md`](./TASK_DEPENDENCY_GRAPH.md).

**Sprint objective:** automatically acquire every official source — Pokegym rulings, three HTML
rule pages, and six PDFs — into `Document` objects and raw persistence, orchestrated end-to-end.

---

### TASK-007 — Pokegym rulings crawler

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_02_INGESTION |
| **REQ covered** | REQ-001 |
| **Depends on** | TASK-003, TASK-005 |
| **Unblocks** | TASK-010 |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/crawler_pokegym.py`, `src/pokemon_tcg_rag/ingestion/__init__.py`, `tests/unit/test_crawler_pokegym.py` |
| **Branch** | `feat/task-007-pokegym-crawler` |

**Description.** Implement `PokegymCrawler.fetch_all_rulings()` scraping
`https://compendium.pokegym.net/all-rulings-by-date/`, extracting per ruling: `date`, `set`,
`card`, `question`, `answer`, `url`; saving raw HTML and emitting `Document` objects with
`DocumentSource.POKEGYM` / `RuleType.RULING` and full `DocumentMetadata`.

**Definition of Ready.** TASK-003, TASK-005 merged. HTML fixtures saved under `tests/fixtures/pokegym/`.

**Steps.**
1. Fetch listing with `requests` (timeout, retry, user-agent); persist raw HTML to `data/raw_data/html/`.
2. Parse rows with BeautifulSoup into structured fields.
3. Build one `Document` per ruling (question+answer as content) with metadata `card_name`,
   `publication_date`, `source_url`.
4. Persist structured output as JSONL to `data/raw_data/json/`.
5. Raise `IngestionError` on network/parse failure.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-018 | `test_parse_ruling_row_fields` | unit (fixture HTML) |
| TEST-019 | `test_missing_field_handled` | unit |
| TEST-020 | `test_emits_documents_with_metadata` | unit |
| TEST-021 | `test_network_error_raises_ingestion_error` | unit (mocked) |

**Definition of Done.** Rulings parsed from fixtures into `Document`s; JSONL persisted; ≥90% coverage; network mocked in tests.

**Acceptance criteria.** Running against fixtures yields ≥1 `Document` per ruling with all six fields populated.

**Commit message.** `feat(ingestion): pokegym rulings crawler (TASK-007)`

---

### TASK-008 — HTML pages scraper (Ban / Promo / Mega)

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_02_INGESTION |
| **REQ covered** | REQ-003 |
| **Depends on** | TASK-003, TASK-005 |
| **Unblocks** | TASK-010 |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/html_scraper.py`, `tests/unit/test_html_scraper.py` |
| **Branch** | `feat/task-008-html-scraper` |

**Description.** Implement `HTMLPageScraper.fetch_all_html_pages()` scraping the Banned Card List,
Promo Legality, and Mega Evolution rule-change pages into `Document`s tagged
`BAN_LIST_HTML` / `PROMO_LEGALITY_HTML` / `MEGA_RULES_HTML` with `RuleType` `BAN_STATUS` /
`PROMO_STATUS` / `MECHANIC_RULE`.

**Definition of Ready.** TASK-003, TASK-005 merged; HTML fixtures for the three pages saved.

**Steps.**
1. Maintain a URL→(`DocumentSource`,`RuleType`) map from [`PROJECT.md`](../00_project/PROJECT.md) §3.
2. Fetch + persist raw HTML; extract main content text stripping nav/boilerplate.
3. Emit one `Document` per page with `source_url`, `publication_date` (scrape date), `document_title`.
4. Raise `IngestionError` on failure.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-022 | `test_scrape_ban_list_content` | unit (fixture) |
| TEST-023 | `test_source_and_ruletype_mapping` | unit |
| TEST-024 | `test_boilerplate_stripped` | unit |

**Definition of Done.** Three `Document`s produced from fixtures with correct source/rule_type; ≥90% coverage.

**Acceptance criteria.** Each of the three pages yields a non-empty `Document` with the correct enums.

**Commit message.** `feat(ingestion): HTML scraper for ban/promo/mega pages (TASK-008)`

---

### TASK-009 — PDF & Rulebook parser

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_02_INGESTION |
| **REQ covered** | REQ-002 |
| **Depends on** | TASK-003, TASK-005 |
| **Unblocks** | TASK-010 |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/pdf_parser.py`, `tests/unit/test_parsers.py` |
| **Branch** | `feat/task-009-pdf-rulebook-parser` |

**Description.** Implement `PDFParser.parse_pdf_file(file_path, source, rule_type)` using
`pymupdf4llm`/PyMuPDF to extract structured text **preserving page numbers and section titles**,
emitting one `Document` per logical section with `page_number` and `section_title` metadata.
Covers the Rulebook, Tournament Handbook, Alternative Play Handbook, Errata, and Deck List Guide
PDFs. (This is the plan's "Rulebook parser" task.)

**Definition of Ready.** TASK-003, TASK-005 merged; a small sample PDF fixture under `tests/fixtures/pdf/`.

**Steps.**
1. Open the PDF with PyMuPDF; extract per-page markdown via `pymupdf4llm.to_markdown` (page chunks).
2. Detect section boundaries from heading markers; carry `section_title` forward.
3. Build `Document`s with `page_number`, `section_title`, `document_title`, `checksum`,
   passed `source`/`rule_type`.
4. Raise `ParsingError` on unreadable/corrupt PDF.
5. Verify page-count and non-empty text invariants.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-025 | `test_parse_extracts_text` | unit (fixture PDF) |
| TEST-026 | `test_page_numbers_preserved` | unit |
| TEST-027 | `test_section_titles_detected` | unit |
| TEST-028 | `test_corrupt_pdf_raises_parsing_error` | unit |

**Definition of Done.** Sample PDF parsed into ≥1 `Document` with correct page numbers; ≥90% coverage.

**Acceptance criteria.** For each real PDF the parser returns `Document`s whose `page_number` values match the source pagination.

**Commit message.** `feat(ingestion): PyMuPDF rulebook/PDF parser (TASK-009)`

---

### TASK-010 — Ingestion orchestrator: download & raw persistence

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_02_INGESTION |
| **REQ covered** | REQ-001, REQ-002, REQ-003 |
| **Depends on** | TASK-007, TASK-008, TASK-009 |
| **Unblocks** | TASK-011, TASK-012 |
| **Files affected** | `src/pokemon_tcg_rag/ingestion/pipeline.py`, `tests/integration/test_ingestion_pipeline.py` |
| **Branch** | `feat/task-010-ingestion-orchestrator` |

**Description.** Implement `IngestionPipeline` that downloads the six PDFs, runs the crawler and
HTML scraper, invokes the PDF parser, aggregates all `Document`s, and persists raw + processed
artifacts under `data/raw_data/` and `data/processed/`.

**Definition of Ready.** TASK-007, TASK-008, TASK-009 merged.

**Steps.**
1. Add a PDF download step (URLs from `PROJECT.md`) saving to `data/raw_data/pdfs/` with checksum de-dup.
2. Compose crawler + scraper + parser; collect a single `list[Document]`.
3. Persist processed Documents as JSONL/Parquet to `data/processed/`.
4. Log counts (docs per source) via structlog; raise `IngestionError` on partial failure with context.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-029 | `test_pipeline_aggregates_all_sources` | integration (mocked fetchers) |
| TEST-030 | `test_download_dedup_by_checksum` | integration |
| TEST-031 | `test_processed_persistence_written` | integration |

**Definition of Done.** Pipeline returns Documents from all sources (mocked); artifacts written; ≥90% coverage.

**Acceptance criteria.** One `IngestionPipeline.run()` call produces Documents covering all 9 `DocumentSource` values.

**Commit message.** `feat(ingestion): orchestrate download and raw persistence (TASK-010)`

---

### TASK-011 — Ingestion CLI & Docker ingestion service

| Field | Value |
| :--- | :--- |
| **Sprint** | SPRINT_02_INGESTION |
| **REQ covered** | REQ-016 |
| **Depends on** | TASK-010, TASK-006 |
| **Unblocks** | TASK-039 |
| **Files affected** | `scripts/run_ingestion.py`, `docker/Dockerfile.ingestion`, `docker-compose.yml` (ingestion service), `Makefile` |
| **Branch** | `feat/task-011-ingestion-cli` |

**Description.** Expose the pipeline as a CLI (`python -m` / `scripts/run_ingestion.py`) and wire
the `ingestion` Compose service so the automated pipeline runs on `docker compose up`.

**Definition of Ready.** TASK-010, TASK-006 merged.

**Steps.**
1. Implement `scripts/run_ingestion.py` invoking `IngestionPipeline.run()` with argparse flags
   (`--sources`, `--out-dir`).
2. Finalize `docker/Dockerfile.ingestion` and the compose `ingestion` service (command + volumes + env).
3. Add `make ingest` target.

**Mandatory tests.**

| TEST | Name | Type |
| :--- | :--- | :--- |
| TEST-032 | `test_run_ingestion_cli_smoke` | smoke (mocked pipeline) |
| TEST-033 | `test_ingestion_service_in_compose` | smoke |

**Definition of Done.** CLI runs end-to-end (mocked); ingestion service present in compose; `make ingest` works.

**Acceptance criteria.** `docker compose run ingestion` executes the pipeline and exits 0.

**Commit message.** `feat(ingestion): CLI entrypoint and compose service (TASK-011)`

---

## Sprint 2 Definition of Done (roll-up)

- [ ] All three source families (Pokegym, HTML pages, PDFs) parse into `Document`s.
- [ ] Orchestrator persists raw + processed artifacts; ingestion runs from CLI and Compose.
- [ ] Networked calls mocked in tests; ≥90% coverage per module.
- [ ] Sprint 2 tasks marked `Done` in [`TASK_INDEX.md`](./TASK_INDEX.md).
