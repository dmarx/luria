from __future__ import annotations
from pathlib import Path
from luria import config, lint, link_targets

def _project(root: Path, monkeypatch) -> None:
    (root / 'record' / 'notes.d').mkdir(parents=True, exist_ok=True)
    (root / 'record' / 'log.d').mkdir(parents=True, exist_ok=True)
    (root / 'docs').mkdir(parents=True, exist_ok=True)
    (root / 'luria.toml').write_text('[luria]\nissue_url = "https://example.test/issues/{n}"\n[luria.schemes.NT]\ndir = "record/notes.d"\nrender = "index"\noutput = "docs/notes"\n[luria.journals.log]\ndir = "record/log.d"\noutput = "docs/log"\ngranularity = "day"\n')
    monkeypatch.setenv('LURIA_ROOT', str(root))
    config.reset()

def _note(root: Path, number: int, body: str='Body.') -> Path:
    path = root / 'record' / 'notes.d' / f'NT-{number:03d}.md'
    path.write_text(f"---\nstatus: Active\ntitle: 'A note'\ntags:\n- record\ndate: '2026-01-01'\n---\n\n# NT-{number:03d}: A note\n\n{body}\n")
    return path

def _entry(root: Path, body: str) -> Path:
    path = root / 'record' / 'log.d' / '2026' / '01' / '01' / '120000.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: 'An entry'\ncreated: '2026-01-01T12:00:00'\ntags: [log]\n---\n\n{body}\n")
    return path

def test_a_target_that_resolves_is_silent(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1)
    _note(tmp_path, 2, 'See [NT-001](NT-001.md).')
    assert link_targets.broken()[0] == []

def test_a_target_that_resolves_to_nothing_is_reported(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, 'See [NT-009](NT-009.md).')
    flagged, _ = link_targets.broken()
    assert len(flagged) == 1
    assert 'NT-009.md' in flagged[0] and 'NT-001.md:11' in flagged[0]

def test_a_journal_entry_resolves_from_where_it_renders(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1)
    _entry(tmp_path, 'See [NT-001](../../record/notes.d/NT-001.md).')
    assert link_targets.broken()[0] == []
    _entry(tmp_path, 'See [NT-001](../../../../record/notes.d/NT-001.md).')
    flagged, _ = link_targets.broken()
    assert len(flagged) == 1, 'source-relative depth must not be accepted'
    assert 'docs/log/' in flagged[0], 'the message names the frame it used'

def test_urls_anchors_and_absolute_paths_are_not_checked(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, '[a](https://example.test/x) [b](//host/x) [c](/abs/x) [d](#here) [e](mailto:x@example.test)')
    assert link_targets.broken()[0] == []

def test_a_pattern_is_not_a_path(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, 'uid = "(\\d{4})[.:](\\d{4,5})" and {n} in a url')
    assert link_targets.broken()[0] == []

def test_an_example_in_code_is_not_a_citation(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, 'Write `[NT-009](NT-009.md)`.\n\n```\n[NT-009](NT-009.md)\n```\n')
    assert link_targets.broken()[0] == []

def test_a_fragment_does_not_hide_a_missing_file(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, 'See [NT-009](NT-009.md#context).')
    assert len(link_targets.broken()[0]) == 1

def test_a_percent_encoded_target_resolves_to_the_real_name(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    (tmp_path / 'docs' / 'a note.md').write_text('# A note\n')
    _note(tmp_path, 1, 'See [it](../../docs/a%20note.md).')
    assert link_targets.broken()[0] == []

def test_a_deliberate_target_is_acknowledged_not_deleted(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, '<!-- target-ok: build/out.md — generated, not committed -->\nSee [out](build/out.md).')
    assert link_targets.broken()[0] == []
    _note(tmp_path, 2, '<!-- target-ok: build/out.md — generated, not committed -->\nSee [out](build/out.md).\n\nAnd [NT-009](NT-009.md).')
    flagged, _ = link_targets.broken()
    assert len(flagged) == 1 and 'NT-009.md' in flagged[0]

def test_a_directive_that_acknowledges_nothing_is_reported(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, '<!-- target-ok: build/out.md — generated, not committed -->\nNothing links there any more.')
    flagged, stale = link_targets.broken()
    assert flagged == []
    assert len(stale) == 1 and 'build/out.md' in stale[0]

def test_the_class_is_failable(tmp_path, monkeypatch):
    assert 'broken-targets' in lint.FAILABLE
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, 'See [NT-009](NT-009.md).')
    assert 'broken-targets' in {n for n, _, _ in lint.status_sections()}

def test_a_clean_project_does_not_emit_the_class(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1)
    assert 'broken-targets' not in {n for n, _, _ in lint.status_sections()}
