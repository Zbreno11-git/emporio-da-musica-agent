"""Fixtures compartilhadas.

Os testes que dependem do snapshot real da Artefact procuram a fonte em `EMPORIO_SNAPSHOT` (ZIP ou
diretório) ou em `_insumos_privados/desafio/`. Sem a fonte, eles são pulados com o motivo explícito; os
testes de regra pura e os de validação com dados sintéticos rodam sempre.
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
    candidates = [Path(env)] if env else [ROOT / "_insumos_privados" / "desafio"]
    return next((c for c in candidates if c.exists()), None)


@pytest.fixture(scope="session")
def oracles() -> dict:
    return json.loads((FIXTURES / "oraculos.json").read_text())


@pytest.fixture(scope="session")
def snapshot_build(tmp_path_factory) -> Path:
    """Constrói os bancos do snapshot real num diretório temporário (nunca toca `data/build/`)."""
    from scripts.import_snapshot import build

    source = snapshot_source()
    if source is None:
        pytest.skip("snapshot da Artefact ausente: defina EMPORIO_SNAPSHOT=<ZIP do desafio>")
    out = tmp_path_factory.mktemp("snapshot") / "build"
    build(source, out)
    return out
