import os
import sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from luria import config

@pytest.fixture(autouse=True)
def _repo_root(monkeypatch):
    monkeypatch.setenv('LURIA_ROOT', str(REPO))
    config.reset()
    yield
    config.reset()

@pytest.fixture
def project(tmp_path, monkeypatch):
    (tmp_path / 'docs' / 'decisions').mkdir(parents=True)
    (tmp_path / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n')
    (tmp_path / 'docs' / 'design-principles.md').write_text('# Design principles\n\n## 1. First value\n\nBody.\n')
    monkeypatch.setenv('LURIA_ROOT', str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()
