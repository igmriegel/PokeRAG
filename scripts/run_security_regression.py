#!/usr/bin/env python3
"""Run the consolidated security regression suite."""

from __future__ import annotations

import os
import subprocess
import sys

SECURITY_TESTS = [
    "tests/integration/test_api_security.py",
    "tests/integration/test_api_limits.py",
    "tests/integration/test_prompt_integrity.py",
    "tests/integration/test_app_runtime.py",
    "tests/smoke/test_ci_security_gates.py",
    "tests/smoke/test_platform_hardening.py",
]


def main() -> None:
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", *SECURITY_TESTS],
        check=True,
        env=env,
    )


if __name__ == "__main__":
    main()
