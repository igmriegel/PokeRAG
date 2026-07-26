#!/usr/bin/env bash

set -u -o pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="${TMPDIR:-/tmp}"
INSTALL_LOG="$(mktemp "${TMP_DIR}/ci-check-install.XXXXXX.log")"

declare -a STEP_NAMES=()
declare -a STEP_STATUS=()
declare -a STEP_LOGS=()

record_step() {
  STEP_NAMES+=("$1")
  STEP_STATUS+=("$2")
  STEP_LOGS+=("$3")
}

run_step() {
  local name="$1"
  shift
  local log_file
  log_file="$(mktemp "${TMPDIR}/ci-check.XXXXXX.log")"

  printf '\n==> %s\n' "$name"
  if "$@" >"$log_file" 2>&1; then
    printf 'PASS: %s\n' "$name"
    record_step "$name" "PASS" "$log_file"
  else
    local exit_code=$?
    printf 'FAIL: %s (exit %s)\n' "$name" "$exit_code"
    printf 'Last output:\n'
    tail -n 20 "$log_file" || true
    record_step "$name" "FAIL" "$log_file"
  fi
}

run_install() {
  printf '\n==> Install dependencies\n'
  if {
    python -m pip install --upgrade pip
    python -m pip install -e . -r requirements.runtime.txt -r requirements.dev.txt
    python -m pip install cyclonedx-bom
  } >"$INSTALL_LOG" 2>&1; then
    printf 'PASS: Install dependencies\n'
    record_step "Install dependencies" "PASS" "$INSTALL_LOG"
  else
    local exit_code=$?
    printf 'FAIL: Install dependencies (exit %s)\n' "$exit_code"
    printf 'Last output:\n'
    tail -n 20 "$INSTALL_LOG" || true
    record_step "Install dependencies" "FAIL" "$INSTALL_LOG"
  fi
}

run_install
run_step "Ruff lint" python -m ruff check src/ tests/
run_step "Black format check" python -m black --check src/ tests/
run_step "MyPy types" mypy src/
run_step "Secret scan" python scripts/scan_secrets.py
run_step "Harness consistency" python scripts/check_harness_consistency.py
run_step "Pytest unit + integration" pytest tests/unit/ tests/integration/
run_step "Pytest coverage gate" pytest tests/unit/ tests/integration/ --cov=pokemon_tcg_rag --cov-fail-under=90 --cov-report=xml
run_step "pip-audit" pip-audit
run_step "CycloneDX SBOM" cyclonedx-py environment --output-format json --output-file sbom.json

printf '\n=== CI Check Summary ===\n'
pass_count=0
fail_count=0
for i in "${!STEP_NAMES[@]}"; do
  printf '%-28s %s\n' "${STEP_NAMES[$i]}" "${STEP_STATUS[$i]}"
  if [[ "${STEP_STATUS[$i]}" == "PASS" ]]; then
    pass_count=$((pass_count + 1))
  else
    fail_count=$((fail_count + 1))
  fi
done

printf '\nPassed: %s\nFailed: %s\n' "$pass_count" "$fail_count"
printf 'Install log: %s\n' "$INSTALL_LOG"

if [[ "$fail_count" -ne 0 ]]; then
  exit 1
fi
