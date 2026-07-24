# Scripts Directory (`scripts/`)

Contains executable CLI scripts for data ingestion pipelines, database seeding, automated evaluation runs, and code quality validation:
- `run_ingestion.py`: Launches complete scraping, PDF parsing, chunking, and Qdrant vector indexing.
- `run_evaluation.py`: Runs baseline evaluation over 100 benchmark questions and prints Recall@K / MRR metrics.
- `seed_db.py`: Seeds Qdrant and Postgres databases with baseline test data.
- `check_quality.sh`: Runs linters, static type checkers, and test suite.
