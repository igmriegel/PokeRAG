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
