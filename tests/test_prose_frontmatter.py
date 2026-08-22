"""`origin:` is prose: references in it are linked and lint-checked."""
from pathlib import Path
from luria import config, doc_refs


def _project(root: Path, monkeypatch) -> None:
    (root / "record" / "principles.d").mkdir(parents=True)
    (root / "record" / "decisions.d").mkdir(parents=True)
    (root / "docs").mkdir(exist_ok=True)
    (root / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        '[luria.schemes.DP]\ndir = "record/principles.d"\n'
        'render = "document"\noutput = "docs/design-principles.md"\n')
    (root / "record" / "decisions.d" / "ADR-007.md").write_text(
        "---\nstatus: Active\ntitle: 'A decision'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# ADR-007: A decision\n\nBody.\n")
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()


def test_a_bare_reference_in_origin_is_rewritten(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    dp = tmp_path / "record" / "principles.d" / "DP-001.md"
    dp.write_text(
        "---\nstatus: Active\ntitle: 'A value'\ntags:\n- record\n"
        "date: '2026-01-01'\norigin: >-\n  The episode recorded in ADR-007.\n"
        "---\n\n# DP-001: A value\n\nBody.\n")
    linked, count = doc_refs.linkify(dp.read_text(), dp)
    assert count == 1, linked
    assert "[ADR-007](" in linked, linked


def test_a_data_field_is_still_data(tmp_path, monkeypatch):
    """`issue:` is read by value and never rendered — a link there is a link
    inside a data field, so the fixer must leave it alone."""
    _project(tmp_path, monkeypatch)
    dp = tmp_path / "record" / "principles.d" / "DP-002.md"
    dp.write_text(
        "---\nstatus: Active\ntitle: 'Another'\ntags:\n- record\n"
        "date: '2026-01-01'\nissue: 'ADR-007'\n---\n\n"
        "# DP-002: Another\n\nBody.\n")
    linked, count = doc_refs.linkify(dp.read_text(), dp)
    assert count == 0, linked
