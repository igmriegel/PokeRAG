.PHONY: help install lint format typecheck test test-unit test-integration test-e2e test-smoke eval quality ingest seed run-api run-ui docker-up docker-down clean

help:
	@echo "Pokemon TCG RAG - Development & Harness Makefile"
	@echo "------------------------------------------------"
	@echo "install          : Install project in editable mode with dev dependencies"
	@echo "lint             : Run ruff check"
	@echo "format           : Run ruff format and black"
	@echo "typecheck        : Run mypy static type analysis"
	@echo "test             : Run all tests with coverage"
	@echo "test-unit        : Run unit tests only"
	@echo "test-integration : Run integration tests only"
	@echo "test-smoke       : Run smoke tests"
	@echo "test-e2e         : Run end-to-end tests"
	@echo "eval             : Run RAG and LLM evaluation suite"
	@echo "ingest           : Run raw data scraping and ingestion pipeline"
	@echo "seed             : Embed chunks and seed Qdrant"
	@echo "run-api          : Launch FastAPI backend server"
	@echo "run-ui           : Launch Streamlit web UI"
	@echo "docker-up        : Start all services via docker-compose"
	@echo "docker-down      : Stop all docker-compose services"
	@echo "clean            : Clean up build artifacts and cache files"
	@echo "quality          : Run full quality gate (ruff + mypy + pytest)"

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	ruff check --fix src/ tests/
	black src/ tests/

typecheck:
	mypy src/

test:
	pytest tests/

test-unit:
	pytest tests/unit/ -m unit

test-integration:
	pytest tests/integration/ -m integration

test-smoke:
	pytest tests/smoke/ -m smoke

test-e2e:
	pytest tests/e2e/ -m e2e

eval:
	pytest tests/evaluation/ -m evaluation

quality: lint typecheck test

ingest:
	python3 scripts/run_ingestion.py

seed:
	python3 scripts/seed_db.py

run-api:
	uvicorn pokemon_tcg_rag.api.main:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	streamlit run src/pokemon_tcg_rag/ui/streamlit_app.py --server.port 8501

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage
