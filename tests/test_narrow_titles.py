from __future__ import annotations
from pathlib import Path
from luria import config, lint, narrow_titles

def _project(root: Path, monkeypatch, terms: str='', generalize: bool=True) -> None:
    (root / 'record' / 'values.d').mkdir(parents=True, exist_ok=True)
    (root / 'docs').mkdir(parents=True, exist_ok=True)
    (root / 'luria.toml').write_text(f'[luria]\nissue_url = "https://example.test/issues/{{n}}"\n[luria.lint]\nnarrow_terms = [{terms}]\n[luria.schemes.VP]\ndir = "record/values.d"\nrender = "document"\noutput = "docs/values.md"\ntitles_generalize = {str(generalize).lower()}\n')
    monkeypatch.setenv('LURIA_ROOT', str(root))
    config.reset()

def _value(root: Path, number: int, title: str, body: str='Body.') -> Path:
    path = root / 'record' / 'values.d' / f'VP-{number:03d}.md'
    path.write_text(f"---\nstatus: Active\ntitle: {title!r}\ntags:\n- craft\ndate: '2026-01-01'\n---\n\n# VP-{number:03d}: {title}\n\n{body}\n")
    return path

def test_no_vocabulary_means_no_check(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, terms='')
    _value(tmp_path, 1, 'A rule about the toolbar and the canvas')
    assert narrow_titles.rows() == []
    assert 'narrow-titles' not in {n for n, _, _ in lint.status_sections()}

def test_a_scheme_that_does_not_claim_to_transfer_is_untouched(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, terms='"toolbar"', generalize=False)
    _value(tmp_path, 1, 'The toolbar renders lazily')
    assert narrow_titles.rows() == []

def test_a_local_noun_in_a_transferable_title_is_reported(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, terms='"toolbar", "canvas"')
    _value(tmp_path, 1, 'Never block the toolbar')
    rows = narrow_titles.rows()
    assert len(rows) == 1
    assert 'VP-001' in rows[0] and 'toolbar' in rows[0]

def test_the_match_is_plural_tolerant_and_case_insensitive(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, terms='"node"')
    _value(tmp_path, 1, 'Nodes are cheap')
    assert len(narrow_titles.rows()) == 1

def test_a_substring_is_not_a_match(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, terms='"node"')
    _value(tmp_path, 1, 'Measure at the anode, not the cathode')
    assert narrow_titles.rows() == []

def test_another_sense_is_acknowledged_not_removed(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, terms='"overlay"')
    _value(tmp_path, 1, 'User choice overlays the baseline', '<!-- broad-ok: overlay — a verb here, not the UI noun -->\n\nBody.')
    assert narrow_titles.rows() == []
    _value(tmp_path, 2, 'The overlay is opaque')
    rows = narrow_titles.rows()
    assert len(rows) == 1 and 'VP-002' in rows[0], 'the acknowledgement is per-document, not global'

def test_the_class_is_failable(tmp_path, monkeypatch):
    assert 'narrow-titles' in lint.FAILABLE
    _project(tmp_path, monkeypatch, terms='"toolbar"')
    _value(tmp_path, 1, 'Never block the toolbar')
    assert 'narrow-titles' in {n for n, _, _ in lint.status_sections()}
