"""Shared fixtures.

Every test runs against *this* repo's record, because Luria's first consumer is
Luria ([ADR-009](../record/decisions.d/ADR-009.md)) — a
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
    # `status:` is a field a scheme declares (#181), so a record that wants
    # its words checked says which vocabulary backs them.
    (tmp_path / "record" / "decisions.d").mkdir(parents=True, exist_ok=True)
    (tmp_path / "record" / "decisions.d" / "statuses.yaml").write_text(
        "Active:\n  blurb: in force\nProposed:\n  blurb: not yet\n"
        "Deferred:\n  blurb: parked\nSuperseded:\n  blurb: replaced\n"
        "Rejected:\n  blurb: declined\n"
    )
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        # Declaring a family replaces the shipped one (ADR-047), so the
        # scheme is written out whole rather than having a `fields` table
        # bolted onto a default that then vanishes.
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        'output = "docs/decisions"\nactive = "Active"\nrender = "index"\n'
        '[luria.schemes.ADR.fields.status]\nvocabulary = "statuses"\n'
    )
    (tmp_path / "docs" / "design-principles.md").write_text(
        "# Design principles\n\n## 1. First value\n\nBody.\n"
    )
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()
