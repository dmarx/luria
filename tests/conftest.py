"""Shared fixtures.

Every test runs against *this* repo's record, because Luria's first consumer is
Luria ([ADR-009](../docs/decisions/adr-009-extracted-with-provenance.md)) — a
check that passes on a synthetic fixture and fails on a real corpus has told you
nothing. Tests that need a controlled tree build one and repoint the config at
it via `LURIA_ROOT`.
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import config  # noqa: E402


@pytest.fixture(autouse=True)
def _repo_root(monkeypatch):
    """Pin the config to this repo unless a test overrides it."""
    monkeypatch.setenv("LURIA_ROOT", str(REPO))
    config.reset()
    yield
    config.reset()


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A minimal but complete record, for tests that need a controlled tree."""
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
    )
    (tmp_path / "docs" / "design-principles.md").write_text(
        "# Design principles\n\n## 1. First value\n\nBody.\n"
    )
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()
