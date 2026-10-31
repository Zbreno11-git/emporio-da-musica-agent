"""Shared fixtures.

Tests that depend on the real Artefact snapshot look for it in `EMPORIO_SNAPSHOT` (ZIP or directory) or in
`_private_inputs/challenge/`. Without it they are skipped with an explicit reason; pure-rule tests and
validation tests on synthetic data always run.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def snapshot_source() -> Path | None:
    env = os.environ.get("EMPORIO_SNAPSHOT")
    candidates = [Path(env)] if env else [ROOT / "_private_inputs" / "challenge"]
    return next((c for c in candidates if c.exists()), None)


@pytest.fixture(scope="session")
def oracles() -> dict:
    return json.loads((FIXTURES / "oracles.json").read_text())


@pytest.fixture(scope="session")
def snapshot_build(tmp_path_factory) -> Path:
    """Build the real snapshot databases in a temporary directory (never touches `data/build/`)."""
    from scripts.import_snapshot import build

    source = snapshot_source()
    if source is None:
        pytest.skip("Artefact snapshot missing: set EMPORIO_SNAPSHOT=<challenge ZIP>")
    out = tmp_path_factory.mktemp("snapshot") / "build"
    build(source, out)
    from scripts.build_policy_index import main as build_index

    build_index(["--source", str(source), "--out", str(out / "policy_sections.json")])
    return out


@pytest.fixture(scope="session")
def policy_index(snapshot_build):
    from app.tools.policies import PolicyIndex

    path = snapshot_build / "policy_sections.json"
    if not path.exists():
        pytest.skip("store manual missing: policy index not built")
    return PolicyIndex.load(path)


@pytest.fixture
def settings(snapshot_build):
    """App settings on the real snapshot with the scripted fake model (tests/fakes.py)."""
    from dataclasses import replace

    from app.config import Settings

    return replace(Settings(), data_dir=snapshot_build, gemini_model="fake-scripted")

