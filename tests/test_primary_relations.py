# tests/test_primary_relations.py
"""One side of a directed converse pair is primary and the other derived.

Storing both sides of a relation is a hand-kept projection of one fact
(DP-2, DP-3), and a projection drifts: Nucleation carried 808 one-sided pairs
waiting on a fixer nobody ran. So a pair declares which side is derived —
`derived: true` on that side's reference — and only the primary side is ever
stored. The derived side is read for every reader by `relations.edges()`,
which already unions a relation with its converse.

Writing the derived field is still allowed; it is how an author states the
relation from the document they are holding. `luria repair` moves it: where
both sides are filed the derived entry is dropped, and where only the
derived side is filed it becomes the primary side on the other document.

A self-converse relation has no derived side and keeps the old rule, and so
does a pair that declares no direction — with a lint row saying so.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged

from luria import config, link_refs, lint, relations, repair


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


DIRECTED = """
schemes:
  LIT:
    alias: "LIT-{slug}"
    references:
      extends:
        scheme: LIT
        required: false
        many: true
        converse: extended_by
      extended_by:
        scheme: LIT
        required: false
        many: true
        converse: extends
        derived: true
      compared_against:
        scheme: LIT
        required: false
        many: true
        converse: compared_against
"""

UNDIRECTED = """
schemes:
  LIT:
    references:
      extends:
        scheme: LIT
        required: false
        many: true
        converse: extended_by
      extended_by:
        scheme: LIT
        required: false
        many: true
        converse: extends
"""


def project(tmp_path, monkeypatch, extra: str = DIRECTED) -> Path:
    write(tmp_path, "luria.yaml", merged("""
                                  issue_url: https://example.test/issues/{n}
                                  schemes:
                                    LIT:
                                      dir: record/literature.d
                                      output: docs/literature
                                  """, extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def note(root: Path, code: str, title: str = "A note", slug: str = "",
         **fields) -> Path:
    front = ["---", "status: Active", f"title: {title!r}", "tags:",
             "- record", "date: '2026-01-01'"]
    if slug:
        front.append(f"slug: {slug}")
    # What `luria repair` would populate from the filename, so a test sees
    # only the repair it is about.
    if code.split("-", 1)[1].isdigit():
        front.append(f"number: {int(code.split('-', 1)[1])}")
    for name, codes in fields.items():
        if codes:
            front.append(f"{name}:")
            front += [f"- {c}" for c in codes]
    front += ["---", "", f"# {code}: {title}", "", "Body."]
    return write(root, f"record/literature.d/{code}.md",
                 "\n".join(front) + "\n")


def held(path: Path, field: str) -> list[str]:
    from luria.adr_index import parse_frontmatter
    value = parse_frontmatter(path.read_text())[0].get(field)
    if value is None:
        return []
    return [str(v) for v in (value if isinstance(value, list) else [value])]


# --- what the config may declare --------------------------------------------

def test_derived_is_read_from_the_reference(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    refs = {r.field: r for r in config.current().schemes["LIT"].references}
    assert refs["extended_by"].derived is True
    assert refs["extends"].derived is False


def test_a_pair_marking_both_sides_derived_is_refused(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="derived"):
        project(tmp_path, monkeypatch, """
                                       schemes:
                                         LIT:
                                           references:
                                             extends:
                                               scheme: LIT
                                               many: true
                                               converse: extended_by
                                               derived: true
                                             extended_by:
                                               scheme: LIT
                                               many: true
                                               converse: extends
                                               derived: true
                                       """)
        config.current()


def test_a_self_converse_relation_cannot_be_derived(tmp_path, monkeypatch):
    """It is both sides of its own pair: marking it marks both."""
    with pytest.raises(ValueError, match="derived"):
        project(tmp_path, monkeypatch, """
                                       schemes:
                                         LIT:
                                           references:
                                             compared_against:
                                               scheme: LIT
                                               many: true
                                               converse: compared_against
                                               derived: true
                                       """)
        config.current()


def test_derived_without_a_converse_is_refused(tmp_path, monkeypatch):
    """Derived from what? A field with no converse has nothing to move to."""
    with pytest.raises(ValueError, match="derived"):
        project(tmp_path, monkeypatch, """
                                       schemes:
                                         LIT:
                                           references:
                                             extended_by:
                                               scheme: LIT
                                               many: true
                                               derived: true
                                       """)
        config.current()


# --- normalization ----------------------------------------------------------

def test_both_sides_filed_drops_the_derived_entry(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original", extended_by=["LIT-002"])
    new = note(root, "LIT-002", "The successor", extends=["LIT-001"])
    before = new.read_text()
    changed = repair.apply()
    assert old in changed
    assert held(old, "extended_by") == []
    assert "extended_by" not in old.read_text()
    assert new.read_text() == before


def test_derived_only_is_rewritten_to_the_primary_side(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original", extended_by=["LIT-002"])
    new = note(root, "LIT-002", "The successor")
    changed = repair.apply()
    assert set(changed) >= {old, new}
    assert held(new, "extends") == ["LIT-001"]
    assert "extended_by" not in old.read_text()


def test_primary_only_is_untouched(tmp_path, monkeypatch):
    """The derived side is computed, so a primary edge alone is complete —
    not one-sided, not repaired, not reported."""
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original")
    new = note(root, "LIT-002", "The successor", extends=["LIT-001"])
    texts = (old.read_text(), new.read_text())
    assert repair.apply() == []
    assert (old.read_text(), new.read_text()) == texts
    assert relations.rows() == []
    assert relations.derived_rows() == []
    # Every reader still sees the derived side.
    assert relations.edges("LIT", "extended_by")["LIT-001"] == {"LIT-002"}


def test_a_derived_entry_naming_an_alias_moves(tmp_path, monkeypatch):
    """The derived entry names its target by readable alias; the move finds
    the document, drops the spelling as written, and writes the primary side
    in the spelling a person would choose."""
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original", slug="origin")
    new = note(root, "LIT-002", "The successor", slug="sequel",
               extended_by=["LIT-origin"])
    # LIT-002 says LIT-origin (LIT-001) is extended by it — i.e. LIT-001
    # extends LIT-002. Odd as history, fine as a fixture.
    repair.apply()
    assert "extended_by" not in new.read_text()
    assert held(old, "extends") == ["LIT-sequel"]


def test_a_derived_entry_naming_a_temporary_code_moves(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original",
               extended_by=["LIT-tmpabcde"])
    temp = note(root, "LIT-tmpabcde", "A draft successor")
    repair.apply()
    assert held(temp, "extends") == ["LIT-001"]
    assert "extended_by" not in old.read_text()


def test_a_derived_entry_on_a_temporary_document_moves(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original")
    temp = note(root, "LIT-tmpabcde", "A draft predecessor",
                extended_by=["LIT-001"])
    repair.apply()
    assert held(old, "extends") == ["LIT-tmpabcde"]
    assert "extended_by" not in temp.read_text()


def test_a_derived_entry_naming_nothing_is_reported_not_written(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original", extended_by=["LIT-099"])
    before = old.read_text()
    assert repair.apply() == []
    assert old.read_text() == before
    row, = relations.derived_rows()
    assert "LIT-099" in row and "LIT-001" in row


def test_normalization_is_idempotent(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, "LIT-001", "The original", extended_by=["LIT-002", "LIT-003"])
    note(root, "LIT-002", "One successor", extends=["LIT-001"])
    note(root, "LIT-003", "Another successor")
    assert repair.apply()
    assert repair.apply() == []


def test_a_move_that_would_make_a_cycle_is_reported_not_written(
        tmp_path, monkeypatch):
    """LIT-001 extends LIT-002 and says LIT-002 extends it: moving the
    second writes half of a 2-cycle. A contradiction, not a completion."""
    root = project(tmp_path, monkeypatch)
    one = note(root, "LIT-001", "One", extends=["LIT-002"],
               extended_by=["LIT-002"])
    two = note(root, "LIT-002", "Two")
    texts = (one.read_text(), two.read_text())
    assert repair.apply() == []
    assert (one.read_text(), two.read_text()) == texts
    assert any("LIT-002" in r and "both" in r
               for r in relations.derived_rows())


def test_the_derived_row_names_repair(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, "LIT-001", "The original", extended_by=["LIT-002"])
    note(root, "LIT-002", "The successor")
    row, = relations.derived_rows()
    assert "extended_by" in row and "`luria repair`" in row
    assert "derived-relations" in {n for n, _, _ in lint.status_sections()}
    assert "derived-relations" in lint.FAILABLE
    repair.apply()
    assert relations.derived_rows() == []


def test_link_fix_leaves_a_directed_pair_alone(tmp_path, monkeypatch):
    """No back-reference is completed for a directed pair: writing the
    derived side would be writing the entry repair removes."""
    root = project(tmp_path, monkeypatch)
    old = note(root, "LIT-001", "The original")
    note(root, "LIT-002", "The successor", extends=["LIT-001"])
    before = old.read_text()
    link_refs.run(fix=True)
    assert old.read_text() == before


# --- what keeps the old rule ------------------------------------------------

def test_a_symmetric_relation_keeps_completion(tmp_path, monkeypatch):
    """No derived side: repair leaves it, `link --fix` completes it, and the
    one-sided finding still stands until it does."""
    root = project(tmp_path, monkeypatch)
    one = note(root, "LIT-001", "One", compared_against=["LIT-002"])
    two = note(root, "LIT-002", "Two")
    assert repair.apply() == []
    assert relations.rows()
    link_refs.run(fix=True)
    assert held(two, "compared_against") == ["LIT-001"]
    assert held(one, "compared_against") == ["LIT-002"]


def test_an_undirected_pair_keeps_completion_and_is_reported(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, UNDIRECTED)
    old = note(root, "LIT-001", "The original")
    note(root, "LIT-002", "The successor", extends=["LIT-001"])
    assert repair.apply() == []
    assert relations.rows()
    row, = relations.undirected_rows()
    assert "extends" in row and "extended_by" in row and "derived" in row
    assert "undirected-relations" in {n for n, _, _ in lint.status_sections()}
    link_refs.run(fix=True)
    assert held(old, "extended_by") == ["LIT-002"]


def test_a_directed_record_reports_no_undirected_pair(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    assert relations.undirected_rows() == []


def test_relate_says_where_each_side_lives(tmp_path, monkeypatch):
    from luria import relate
    root = project(tmp_path, monkeypatch)
    note(root, "LIT-001", "The original")
    note(root, "LIT-002", "The successor")
    note(root, "LIT-003", "Another")
    primary = relate.relate("LIT-002", "extends", "LIT-001")
    assert any("derived" in n and "never stored" in n
               for n in primary.notes), primary.notes
    derived = relate.relate("LIT-001", "extended_by", "LIT-003")
    assert any("`luria repair` moves it" in n
               for n in derived.notes), derived.notes
    assert relations.direction("LIT", "compared_against") == "symmetric"
