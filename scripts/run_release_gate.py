#!/usr/bin/env python3
"""Run the final release qualification gate."""

from __future__ import annotations

import os
import subprocess
import sys

RELEASE_TESTS = [
    "tests/smoke/test_security_regression_harness.py",
    "tests/smoke/test_ci_security_gates.py",
    "tests/smoke/test_platform_hardening.py",
    "tests/smoke/test_full_stack.py",
]


def main() -> None:
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    subprocess.run([sys.executable, "scripts/run_security_regression.py"], check=True, env=env)
    subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", *RELEASE_TESTS],
        check=True,
        env=env,
    )


if __name__ == "__main__":
    main()
