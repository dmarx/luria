"""Per-scheme required frontmatter — the cross-scheme move enabler (ADR-040).

`luria migrate` can relocate a document into a scheme whose template asks for
fields the source scheme never had. The machinery cannot invent them, and
silently landing a document that is missing them is how a move degrades a
record. So the move succeeds and the LINT fails, until a human supplies what
the target's template would have prompted for: the machinery relocates, only a
person vouches.
"""

from __future__ import annotations

from pathlib import Path

from luria import config, lint


def _project(root: Path, monkeypatch, requires: str = "") -> Path:
    (root / "record" / "norms.d").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    (root / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.NRM]\ndir = "record/norms.d"\n'
        + (f"requires = [{requires}]\n" if requires else ""))
    doc = root / "record" / "norms.d" / "NRM-001.md"
    doc.write_text("---\nstatus: Active\ntitle: 'A norm'\ntags:\n- record\n"
                   "date: '2026-01-01'\n---\n\n# NRM-001: A norm\n\nBody.\n")
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()
    return doc


def test_no_requires_demands_nothing(tmp_path, monkeypatch):
    """The default: a scheme asks for the standard fields and no more."""
    _project(tmp_path, monkeypatch)
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == []


def test_a_required_field_is_demanded_by_name(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, requires='"approvers"')
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("no `approvers:`" in e and "NRM scheme requires it" in e
               for e in errors), errors


def test_supplying_the_field_clears_it(tmp_path, monkeypatch):
    doc = _project(tmp_path, monkeypatch, requires='"approvers"')
    doc.write_text(doc.read_text().replace(
        "date: '2026-01-01'\n", "date: '2026-01-01'\napprovers:\n- someone\n"))
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == []


def test_an_empty_value_does_not_satisfy_it(tmp_path, monkeypatch):
    """A present-but-empty key is the shape a scaffold leaves behind, and it
    vouches for nothing — the whole point is a human filling it in."""
    doc = _project(tmp_path, monkeypatch, requires='"approvers"')
    doc.write_text(doc.read_text().replace(
        "date: '2026-01-01'\n", "date: '2026-01-01'\napprovers: []\n"))
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("no `approvers:`" in e for e in errors), errors
