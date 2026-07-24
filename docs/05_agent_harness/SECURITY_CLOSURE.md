# Security Closure and Release Gate

This document captures the operational gate used to qualify a release after the security
remediation program.

## Gate inputs

- `scripts/run_security_regression.py`
- `scripts/run_release_gate.py`
- `tests/smoke/test_ci_security_gates.py`
- `tests/smoke/test_platform_hardening.py`
- `tests/integration/test_api_security.py`
- `tests/integration/test_api_limits.py`
- `tests/integration/test_prompt_integrity.py`
- `tests/integration/test_app_runtime.py`

## Release decision criteria

- All security regression suites pass from a clean workspace.
- CI enforces secret scanning, SCA and SBOM publication.
- No unaccepted Critical or High findings remain in the repository.
- Any residual risk must be documented with owner and expiry.

## Evidence retention

- Keep pytest output for the security regression suite.
- Keep CI logs for dependency scans and SBOM generation.
- Keep any formal risk-acceptance notes alongside the release checklist.
