# tests/test_annotations.py
"""A relation stated in prose, and prose owed to a relation (#333).

Push up: `[[LIT-002]]{--extended_by-->here}` states an edge, and a missing
frontmatter field is the fixer's to write. Push down: a reference declared
`explain: true` wants each code it holds cited and annotated in the body —
annotating an existing citation is mechanical, writing the missing prose is
not.
"""

from __future__ import annotations

from pathlib import Path

from _config import merged

from luria import annotations, config, link_refs, lint
from luria.adr_index import parse_frontmatter


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


PAIRED = """
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
      source:
        scheme: LIT
        required: false
"""

EXPLAINED = """
schemes:
  LIT:
    references:
      extends:
        scheme: LIT
        required: false
        many: true
        converse: extended_by
        explain: true
      extended_by:
        scheme: LIT
        required: false
        many: true
        converse: extends
      cites:
        scheme: LIT
        required: false
        many: true
        explain: true
"""


def project(tmp_path, monkeypatch, extra: str = PAIRED) -> Path:
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


def note(root: Path, number: int, body: str = "Body.", **fields) -> Path:
    front = ["---", "status: Active", "title: 'A note'", "tags:",
             "- record", "date: '2026-01-01'"]
    for name, codes in fields.items():
        if isinstance(codes, str):
            front.append(f"{name}: {codes}")
        elif codes:
            front.append(f"{name}:")
            front += [f"- {c}" for c in codes]
    front += ["---", "", f"# LIT-{number:03d}: A note", "", body]
    return write(root, f"record/literature.d/LIT-{number:03d}.md",
                 "\n".join(front) + "\n")


def meta(path: Path) -> dict:
    return parse_frontmatter(path.read_text())[0]


# --- reading annotations -----------------------------------------------------

def test_scan_reads_both_directions_on_every_citation_shape(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    text = ("---\ntitle: x\n---\n\n"
            "See [[LIT-2]]{--extends-->here}, [LIT-003](LIT-003.md){here--extends-->}"
            " and LIT-004{ here - source -> }.\n")
    cites, orphans = annotations.scan(text)
    assert [(c.code, c.relation, c.incoming) for c in cites] == [
        ("LIT-002", "extends", True), ("LIT-003", "extends", False),
        ("LIT-004", "source", False)]
    assert orphans == []


def test_quoted_annotations_are_specimens(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    text = ("---\ntitle: x\n---\n\n`[[LIT-2]]{--extends-->here}`\n\n"
            "```\n[[LIT-2]]{--extends-->here}\n```\n\n"
            "<!-- [[LIT-2]]{--extends-->here} -->\n")
    assert annotations.scan(text) == ([], [])


def test_an_annotation_on_nothing_is_an_orphan(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    text = "---\ntitle: x\n---\n\nloose {--extends-->here} text\n"
    assert annotations.scan(text) == ([], [5])


# --- push up -----------------------------------------------------------------

def test_an_outgoing_annotation_is_written_into_this_documents_field(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    b = note(root, 2, "Builds on [[LIT-1]]{here--extends-->}.")
    s = annotations.survey()
    assert len(s.unrecorded) == 1 and "extends: LIT-001" in s.unrecorded[0]
    annotations.complete(fix=True)
    assert meta(b)["extends"] == ["LIT-001"]
    assert annotations.survey().unrecorded == []


def test_an_incoming_annotation_is_written_here_as_the_converse(
        tmp_path, monkeypatch):
    """`[[LIT-2]]{--extends-->here}` says LIT-002 extends this one. The
    prose is here, so the fact is written here — as `extended_by` — and the
    converse completion writes LIT-002's side."""
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, "Carried further by [[LIT-2]]{--extends-->here}.")
    b = note(root, 2)
    link_refs.run(fix=True)
    assert meta(a)["extended_by"] == ["LIT-002"]
    assert meta(b)["extends"] == ["LIT-001"]
    assert "[LIT-2](LIT-002.md){--extends-->here}" in a.read_text()
    s = annotations.survey()
    assert s.unrecorded == [] and s.bad == []


def test_an_edge_held_by_the_converse_side_is_already_recorded(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "Carried further by [[LIT-2]]{--extends-->here}.")
    note(root, 2, extends=["LIT-001"])
    assert annotations.survey().unrecorded == []


def test_without_a_converse_the_tail_document_holds_it(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, "LIT-002 draws on this: [[LIT-2]]{--source-->here}.")
    b = note(root, 2)
    annotations.complete(fix=True)
    assert meta(b)["source"] == "LIT-001"
    assert "source" not in meta(a)


def test_a_scalar_already_holding_another_code_is_not_overwritten(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 3)
    b = note(root, 2, "From [[LIT-1]]{here--source-->}.", source="LIT-003")
    s = annotations.complete(fix=True)
    assert s.writes == [] and "contradicts" in s.bad[0]
    assert meta(b)["source"] == "LIT-003"


def test_what_the_record_cannot_hold_is_a_bad_annotation(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 2, "[[LIT-1]]{here--refutes-->} and [[LIT-9]]{here--extends-->}"
                  " and [[LIT-2]]{here--extends-->}.")
    bad = " ".join(annotations.survey().bad)
    assert "declares no reference `refutes`" in bad
    assert "LIT-009 is no document" in bad
    assert "to itself" in bad


# --- push down ---------------------------------------------------------------

def test_an_explained_relation_cited_plainly_is_annotated(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1, extended_by=["LIT-002"])
    b = note(root, 2, "Nothing here is new (see [[LIT-1]]).",
             extends=["LIT-001"], cites=["LIT-001"])
    # One citation carries one annotation: the first relation takes it, and
    # the second has no plain citation left, so it is the author's to explain
    # — said before the fix as well as after.
    s = annotations.survey()
    assert len(s.unannotated) == 1 and len(s.unexplained) == 1
    annotations.complete(fix=True)
    assert "[[LIT-1]]{--extended_by-->here}" in b.read_text()
    s = annotations.survey()
    assert s.unannotated == []
    assert len(s.unexplained) == 1 and "`cites: LIT-001`" in s.unexplained[0]


def test_an_uncited_explained_relation_is_reported_not_fixed(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    b = note(root, 2, "foo bar baz.", cites=["LIT-001"])
    before = b.read_text()
    s = annotations.complete(fix=True)
    assert len(s.unexplained) == 1
    assert "{here--cites-->}" in s.unexplained[0]
    assert b.read_text() == before


def test_unexplained_ok_acknowledges_one_code(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 3)
    note(root, 2, "<!-- unexplained-ok: LIT-001 — the title says it -->\n"
                  "foo.", cites=["LIT-001", "LIT-003"])
    rows = annotations.survey().unexplained
    assert len(rows) == 1 and "LIT-003" in rows[0]


def test_an_annotated_relation_is_explained(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1, extended_by=["LIT-002"])
    note(root, 2, "Builds on [[LIT-1]]{here--extends-->}.",
         extends=["LIT-001"])
    s = annotations.survey()
    assert (s.unrecorded, s.unannotated, s.unexplained, s.bad) == (
        [], [], [], [])


def test_relations_without_explain_ask_nothing_of_prose(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, extended_by=["LIT-002"])
    note(root, 2, extends=["LIT-001"])
    s = annotations.survey()
    assert (s.unannotated, s.unexplained) == ([], [])


# --- the lint ----------------------------------------------------------------

def test_every_class_is_a_lint_class(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 2, "[[LIT-1]]{here--extends-->} loose {here--cites-->}",
         cites=["LIT-001"])
    names = {n for n, _, _ in lint.status_sections()}
    for name in ("unrecorded-relations", "unexplained-relations",
                 "bad-annotations"):
        assert name in lint.FAILABLE and name in names
    assert "unannotated-relations" in lint.FAILABLE
