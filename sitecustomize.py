"""
Test bootstrap customizations for local pytest runs.
"""

from __future__ import annotations

import os
import sys


def _is_pytest_process() -> bool:
    return any("pytest" in arg for arg in sys.argv)


if _is_pytest_process():
    extra_opts = (
        "-p no:rerunfailures "
        "-p no:pytest_rerunfailures "
        "-p no:langsmith "
        "-p no:deepeval "
        "-p no:repeat "
        "-p no:xdist"
    )
    current_opts = os.environ.get("PYTEST_ADDOPTS", "").strip()
    if extra_opts not in current_opts:
        os.environ["PYTEST_ADDOPTS"] = f"{extra_opts} {current_opts}".strip()
