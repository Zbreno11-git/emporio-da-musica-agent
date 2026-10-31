"""Runs the chat page's pure display rules (app/static/format.js) under node's test runner."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_format_rules():
    run = subprocess.run(["node", "--test", *map(str, sorted(HERE.glob("*.test.mjs")))],
                         capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stdout[-3000:] + run.stderr[-2000:]
