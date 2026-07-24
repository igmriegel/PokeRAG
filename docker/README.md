# Docker Configuration Directory

This directory contains the container definitions for the **Pokemon TCG Rules RAG System**.

## File Summary

- `Dockerfile.app`: Multi-stage Python 3.10 image hosting both the FastAPI backend (`:8000`) and Streamlit frontend (`:8501`).
- `Dockerfile.ingestion`: Dedicated container image for batch scraping, PDF parsing, chunking, embedding generation, and Qdrant index seeding.

## Build and Run Instructions

To build images independently:
```bash
docker build -t pokemon-rag-app -f docker/Dockerfile.app .
docker build -t pokemon-rag-ingestion -f docker/Dockerfile.ingestion .
```

To launch via Docker Compose:
```bash
docker-compose up --build -d
```
