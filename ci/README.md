# CI/CD Infrastructure Directory

This directory contains Continuous Integration (CI) workflows, scripts, and quality validation harnesses.

## File Summary

- `workflows/ci.yml`: GitHub Actions automated workflow enforcing:
  1. Linter checks (`ruff`)
  2. Formatting compliance (`black --check`)
  3. Strict static type analysis (`mypy`)
  4. Unit test suite execution with hard 90% coverage enforcement (`pytest --cov-fail-under=90`).
