# API Module (`api/`)

This directory contains the FastAPI backend REST API:
- `main.py`: FastAPI application entrypoint with `/health` and `/metrics` (Prometheus) endpoints.
- `routes.py`: API route handlers for `/api/v1/query` and `/api/v1/feedback`.
- `schemas.py`: OpenAPI Pydantic data schemas for requests and responses.
