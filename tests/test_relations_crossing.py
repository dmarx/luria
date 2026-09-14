# tests/test_relations_crossing.py
"""A converse that lives on another scheme (#253).

`converse` resolved against the declaring scheme's own fields, so a relation
that crosses a scheme boundary was sayable from one end and unreachable from
the other. `SOTA.introduced_by` holds `LIT` codes; its converse `introduces`
is a field on `LIT` holding `SOTA` codes, and until now that could not be
declared at all — luria.yaml said so out loud on `NOTE.paper`.

Symmetry and same-scheme pairs are the special case where the two schemes
coincide, so every rule here is the old rule with the scheme read off the
field instead of assumed.
"""

from __future__ import annotations

from _config import merged

from pathlib import Path

import pytest

from luria import config, relations

CROSSING = """
schemes:
  SOTA:
    dir: record/practices.d
    output: docs/practices
    references:
      introduced_by:
        scheme: LIT
        required: false
        many: true
        converse: introduces
  LIT:
    references:
      introduces:
        scheme: SOTA
        required: false
        many: true
        converse: introduced_by
"""


def _project(tmp_path, monkeypatch, extra: str | dict = CROSSING) -> Path:
    (tmp_path / "record" / "literature.d").mkdir(parents=True, exist_ok=True)
    (tmp_path / "record" / "practices.d").mkdir(parents=True, exist_ok=True)
    (tmp_path / "luria.yaml").write_text(merged("""
issue_url: https://example.test/issues/{n}
schemes:
  LIT:
    dir: record/literature.d
    output: docs/literature
""", extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def _lit(root: Path, n: int, body: str = "") -> None:
    (root / "record" / "literature.d" / f"LIT-{n:03d}.md").write_text(
        f"---\nstatus: Active\ntitle: 'Paper {n}'\n{body}---\n\n"
        f"# LIT-{n:03d}: Paper {n}\n\nBody.\n")


def _sota(root: Path, n: int, body: str = "") -> None:
    (root / "record" / "practices.d" / f"SOTA-{n:03d}.md").write_text(
        f"---\nstatus: Active\ntitle: 'Practice {n}'\n{body}---\n\n"
        f"# SOTA-{n:03d}: Practice {n}\n\nBody.\n")


# ── declaring it ──────────────────────────────────────────────────────────

def test_a_crossing_pair_can_be_declared(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    pairs = relations.pairs()
    assert ("SOTA", "introduced_by", "introduces", "LIT") in pairs
    assert ("LIT", "introduces", "introduced_by", "SOTA") in pairs


def test_the_converse_must_point_back_at_the_declaring_scheme(
        tmp_path, monkeypatch):
    """A field on the far scheme with the right NAME is not the converse if it
    points somewhere else. Here `LIT` holds a self-consistent pair of its own,
    so the only defect left is that `SOTA.introduced_by` names a converse that
    does not point back at `SOTA`."""
    _project(tmp_path, monkeypatch, """
schemes:
  SOTA:
    dir: record/practices.d
    output: docs/practices
    references:
      introduced_by: {scheme: LIT, required: false, many: true, converse: introduces}
  LIT:
    references:
      introduces: {scheme: LIT, required: false, many: true, converse: introduced_by}
      introduced_by: {scheme: LIT, required: false, many: true, converse: introduces}
""")
    with pytest.raises(ValueError, match="points back at SOTA"):
        config.current()


def test_the_converse_must_exist_on_the_far_scheme(tmp_path, monkeypatch):
    """It is looked up on the scheme whose codes the field holds — which is
    the message a reader needs, since the obvious guess is the near one."""
    import yaml as _yaml
    without = _yaml.safe_load(CROSSING)
    without["schemes"]["LIT"]["references"].pop("introduces")
    _project(tmp_path, monkeypatch, without)
    with pytest.raises(ValueError, match="is not a reference LIT declares"):
        config.current()


def test_it_still_has_to_be_mutual(tmp_path, monkeypatch):
    """Half a pair completes in one direction only, crossing or not."""
    import yaml as _yaml
    half = _yaml.safe_load(CROSSING)
    half["schemes"]["LIT"]["references"]["introduces"].pop("converse")
    _project(tmp_path, monkeypatch, half)
    with pytest.raises(ValueError, match="does not name 'introduced_by' back"):
        config.current()


# ── completing it ─────────────────────────────────────────────────────────

def test_the_far_side_is_written_on_the_other_scheme(tmp_path, monkeypatch):
    """The whole point: state it once, on whichever end knows it."""
    root = _project(tmp_path, monkeypatch)
    _lit(root, 1)
    _sota(root, 7, "introduced_by:\n- LIT-001\n")

    relations.complete(fix=True)

    assert "introduces:\n- SOTA-007" in (
        root / "record" / "literature.d" / "LIT-001.md").read_text()


def test_it_completes_from_the_far_end_too(tmp_path, monkeypatch):
    root = _project(tmp_path, monkeypatch)
    _lit(root, 1, "introduces:\n- SOTA-007\n")
    _sota(root, 7)

    relations.complete(fix=True)

    assert "introduced_by:\n- LIT-001" in (
        root / "record" / "practices.d" / "SOTA-007.md").read_text()


def test_an_agreeing_crossing_pair_needs_nothing(tmp_path, monkeypatch):
    root = _project(tmp_path, monkeypatch)
    _lit(root, 1, "introduces:\n- SOTA-007\n")
    _sota(root, 7, "introduced_by:\n- LIT-001\n")
    assert relations.completions() == []


def test_a_code_that_lands_in_no_document_is_not_an_edge(tmp_path, monkeypatch):
    """A dangling reference is the contract's finding, not a repair here —
    and which scheme it has to land in depends on the field."""
    root = _project(tmp_path, monkeypatch)
    _lit(root, 1)
    _sota(root, 7, "introduced_by:\n- LIT-404\n")
    assert relations.completions() == []


def test_edges_reads_a_crossing_relation_from_either_side(tmp_path, monkeypatch):
    """Before anyone runs the fixer, both readings already agree."""
    root = _project(tmp_path, monkeypatch)
    _lit(root, 1, "introduces:\n- SOTA-007\n")
    _sota(root, 7)
    assert relations.edges("SOTA", "introduced_by")["SOTA-007"] == {"LIT-001"}


def test_the_one_sided_pair_is_reported(tmp_path, monkeypatch):
    root = _project(tmp_path, monkeypatch)
    _lit(root, 1)
    _sota(root, 7, "introduced_by:\n- LIT-001\n")
    said = relations.rows()
    assert any("LIT-001.md" in r and "introduces: SOTA-007" in r for r in said)


def test_same_scheme_pairs_are_unaffected(tmp_path, monkeypatch):
    """The generalization has to leave the existing case alone."""
    root = _project(tmp_path, monkeypatch, merged(CROSSING, """
schemes:
  LIT:
    references:
      extends: {scheme: LIT, required: false, many: true, converse: extended_by}
      extended_by: {scheme: LIT, required: false, many: true, converse: extends}
"""))
    _lit(root, 1, "extends:\n- LIT-002\n")
    _lit(root, 2)

    relations.complete(fix=True)

    assert "extended_by:\n- LIT-001" in (
        root / "record" / "literature.d" / "LIT-002.md").read_text()
