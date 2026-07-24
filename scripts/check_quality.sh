#!/usr/bin/env bash
set -e

echo "=== Running Quality Checks ==="
echo "1. Checking Code Formatting with Ruff..."
ruff check src/ tests/

echo "2. Checking Static Types with MyPy..."
mypy src/

echo "3. Executing Test Suite with 90% Coverage Enforcement..."
pytest tests/

echo "=== All Quality Gates Passed Successfully! ==="
