# REQUIREMENTS.md - Traceable Requirements Specification

## Requirement Matrix

| ID | Category | Requirement Description | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-001** | Functional | Ingest and scrape Pokegym rulings from specified web URL into JSON format. | High | Pending |
| **REQ-002** | Functional | Download and extract text/layout from 5 official PDF documents using PyMuPDF/PyMuPDF4LLM. | High | Pending |
| **REQ-003** | Functional | Scrape HTML pages for Ban List, Promo Legality, and Mega Evolution rule changes. | High | Pending |
| **REQ-004** | Functional | Normalize extracted text and chunk documents into tokenized segments with metadata. | High | Pending |
| **REQ-005** | Functional | Index vector embeddings into Qdrant vector database collection. | High | Pending |
| **REQ-006** | Functional | Implement Dense Vector retrieval using `BAAI/bge-large-en-v1.5`. | High | Pending |
| **REQ-007** | Functional | Implement Lexical Keyword retrieval using BM25 (`rank-bm25`). | High | Pending |
| **REQ-008** | Functional | Implement Hybrid Search combining Dense and BM25 using Reciprocal Rank Fusion (RRF). | High | Pending |
| **REQ-009** | Functional | Implement Cross-Encoder Re-ranking using `BAAI/bge-reranker-large`. | High | Pending |
| **REQ-010** | Functional | Implement LLM-based User Query Rewriting prior to retrieval. | High | Pending |
| **REQ-011** | Functional | Enforce Certified Judge persona prompt restricting answers to retrieved context only. | High | Pending |
| **REQ-012** | Functional | Every generated answer must include explicit source document citations. | High | Pending |
| **REQ-013** | Functional | Build interactive Streamlit Web UI displaying answer, sources, chunks, and feedback buttons. | High | Pending |
| **REQ-014** | Functional | Collect user feedback (thumbs up / thumbs down + comments) and persist in PostgreSQL. | High | Pending |
| **REQ-015** | Non-Functional| Provide Prometheus metrics exporter and Grafana dashboard with at least 5 charts. | High | Pending |
| **REQ-016** | Non-Functional| Orchestrate all services (App, Ingestion, Qdrant, Postgres, Prometheus, Grafana) in Docker Compose. | High | Pending |
| **REQ-017** | Non-Functional| Achieve minimum 90% unit and integration test coverage enforced by CI. | High | Pending |
| **REQ-018** | Evaluation | Evaluate retrieval strategies (Dense vs BM25 vs Hybrid vs Reranker) measuring Recall@K and MRR. | High | Pending |
| **REQ-019** | Evaluation | Evaluate LLM generation quality measuring Faithfulness and Correctness. | High | Pending |
| **REQ-020** | Deployment | Provide Kubernetes / IaC deployment manifests for cloud hosting. | Medium | Pending |
| **REQ-021** | Security / Supply Chain | Use a reproducible, vulnerability-managed dependency and artifact supply chain with locked dependencies, SBOMs, immutable images, provenance, and time-bound risk exceptions. | Critical | Pending |
| **REQ-022** | Security / Access Control | Authenticate API callers and enforce default-deny, least-privilege authorization for protected routes and owned resources. | Critical | Pending |
| **REQ-023** | Security / Availability | Bound payload size, request rate, concurrency, retries, provider timeouts, retrieval depth, and per-principal LLM cost. | Critical | Pending |
| **REQ-024** | Security / Network | Prevent SSRF and unintended network reachability through trusted destination configuration, egress allowlists, service isolation, and redirect/IP validation. | Critical | Pending |
| **REQ-025** | Security / LLM | Treat prompts, user input, and retrieved content as distinct trust zones; resist direct/indirect prompt injection and verify citation integrity. | Critical | Pending |
| **REQ-026** | Security / Privacy | Minimize response and retained data; protect feedback integrity; redact logs and errors; enforce explicit CORS, diagnostic, retention, and deletion policies. | High | Pending |
| **REQ-027** | Security / Platform | Run minimal rootless containers and restricted Kubernetes workloads with least privilege, bounded resources, secure probes, and policy-as-code validation. | High | Pending |
| **REQ-028** | Security / Secrets & Data | Scope secrets per service, eliminate default credentials, segment networks, encrypt transport, and use least-privilege database identities. | Critical | Pending |
| **REQ-029** | Security / Ingestion | Treat downloaded documents as untrusted: allowlist sources, bound downloads/parsers, validate content, preserve provenance, and quarantine suspicious inputs. | High | Pending |
| **REQ-030** | Security / Assurance | Enforce continuous security verification in CI/CD, including secret history, SAST, SCA, IaC/container scanning, DAST, adversarial LLM testing, and a release risk gate. | Critical | Pending |
| **REQ-031** | Runtime Architecture | Compose all production dependencies explicitly, separate liveness/readiness, honor query contracts, and provide a functional authenticated query/feedback lifecycle. | Critical | Pending |
| **REQ-032** | Data Reproducibility | Provide a legal, versioned, deterministic corpus/bootstrap manifest and keep dense, lexical and incremental ingestion state in verifiable parity. | Critical | Pending |
| **REQ-033** | Quality Assurance | Enforce green formatting/lint/type checks, ≥90% application coverage, real infrastructure integration tests and full-stack end-to-end tests. | High | Pending |
| **REQ-034** | Documentation / Reproducibility | Ensure clean-clone installation and every runtime, API, evaluation and deployment claim are executable and linked to current retained evidence. | High | Pending |
| **REQ-035** | Evaluation Data | Maintain a versioned, licensed, diverse and human-reviewed benchmark with source-resolvable relevance and answer labels. | High | Pending |
| **REQ-036** | Retrieval Evaluation | Evaluate production retrieval implementations through reproducible ablations and enforce corpus/configuration-matched quality regression gates. | High | Pending |
| **REQ-037** | LLM Evaluation | Evaluate real prompt/model outputs with calibrated automatic and human methods, claim-level citation validation, safety, latency and cost gates. | High | Pending |
| **REQ-038** | Observability / FinOps | Provide redacted end-to-end tracing, SLI/SLO metrics, token/cost metering, actionable alerts, live dashboards and feedback telemetry. | High | Pending |
| **REQ-039** | Product Experience | Provide an accessible user workflow with history, safe citation actions, feedback comments, explicit degraded states and supported operational analytics. | Medium | Pending |
| **REQ-040** | Performance / Scalability | Implement isolation-safe caching, metadata/diversity policies, warm-up, bounded batching/backpressure and reproducible capacity/latency/cost qualification. | High | Pending |
| **REQ-041** | Cloud / Resilience | Deploy immutable approved artifacts to TLS staging and prove remote operation, backup/restore, rollback and DORA measurement. | High | Pending |
| **REQ-042** | Production Governance | Make production release contingent on a fresh scorecard that traces all audit findings to passing tests, evidence and accountable residual-risk decisions. | Critical | Pending |
