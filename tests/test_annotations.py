# tests/test_annotations.py
"""A relation stated in prose, and prose owed to a relation (#333).

Push up: `[[extends::LIT-2]]` names this document's `extends` relation, and a
missing frontmatter value is the fixer's to write. Push down: a reference
declared `explain: true` wants each code it holds cited in the body with the
relation named — naming it on an existing citation is mechanical, writing the
missing prose is not. Nothing here is special to any one relation: every
fixture relation is user-declared, and the built-in successor works too.
"""

from __future__ import annotations

from pathlib import Path

from _config import merged

from luria import annotations, config, doc_refs, link_refs, link_targets, lint
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


# --- reading and expanding ---------------------------------------------------

def test_scan_reads_a_relation_from_a_wikilink_or_a_link_title(
        tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    text = ("---\ntitle: x\n---\n\n"
            "See [[extends::LIT-2|the base]], [LIT-3](LIT-003.md \"source\"),"
            " [LIT-4](LIT-004.md \"A tooltip\") and LIT-5.\n")
    assert [(c.code, c.relation, c.kind)
            for c in annotations.scan(text)] == [
        ("LIT-002", "extends", "wiki"), ("LIT-003", "source", "link"),
        ("LIT-004", "", "link"), ("LIT-005", "", "bare")]


def test_quoted_citations_are_specimens(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    text = ("---\ntitle: x\n---\n\n`[[extends::LIT-2]]`\n\n"
            "```\n[[extends::LIT-2]]\n```\n\n"
            "<!-- [[extends::LIT-2]] -->\n")
    assert annotations.scan(text) == []


def test_a_typed_wikilink_expands_to_a_titled_link(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 2)
    a = note(root, 1, "Builds on [[extends::LIT-2|the base]].")
    new, n = doc_refs.expand_wikilinks(a.read_text(), a)
    assert n == 1 and '[the base](LIT-002.md "extends")' in new


def test_a_titled_link_is_still_checked_for_its_target(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, 'See [LIT-9](LIT-009.md "extends").')
    flagged, _ = link_targets.broken([a])
    assert len(flagged) == 1 and "LIT-009.md" in flagged[0]


# --- push up -----------------------------------------------------------------

def test_a_named_relation_is_written_into_this_documents_field(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1)
    b = note(root, 2, "Builds on [[extends::LIT-1]].")
    s = annotations.survey()
    assert len(s.unrecorded) == 1 and "extends: LIT-001" in s.unrecorded[0]
    link_refs.run(fix=True)
    assert meta(b)["extends"] == ["LIT-001"]
    assert meta(a)["extended_by"] == ["LIT-002"]       # the converse, too
    assert '[LIT-1](LIT-001.md "extends")' in b.read_text()
    s = annotations.survey()
    assert (s.unrecorded, s.bad) == ([], [])


def test_the_converse_name_states_the_other_direction(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, "Carried further by [[extended_by::LIT-2]].")
    b = note(root, 2)
    link_refs.run(fix=True)
    assert meta(a)["extended_by"] == ["LIT-002"]
    assert meta(b)["extends"] == ["LIT-001"]


def test_an_edge_held_by_the_converse_side_is_already_recorded(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "Carried further by [[extended_by::LIT-2]].")
    note(root, 2, extends=["LIT-001"])
    assert annotations.survey().unrecorded == []


def test_a_scalar_relation_is_written_as_a_scalar(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    b = note(root, 2, "From [[source::LIT-1]].")
    annotations.complete(fix=True)
    assert meta(b)["source"] == "LIT-001"


def test_the_builtin_successor_is_a_relation_like_any_other(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 2)
    a = note(root, 1, "Replaced by [[superseded_by::LIT-2]].")
    annotations.complete(fix=True)
    assert meta(a)["superseded_by"] == ["LIT-002"]


def test_a_scalar_already_holding_another_code_is_not_overwritten(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 3)
    b = note(root, 2, "From [[source::LIT-1]].", source="LIT-003")
    s = annotations.complete(fix=True)
    assert s.writes == [] and "contradicts" in s.bad[0]
    assert meta(b)["source"] == "LIT-003"


def test_what_the_record_cannot_hold_is_a_bad_annotation(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 2, "[[refutes::LIT-1]] and [[extends::LIT-9]] and "
                  "[[extends::LIT-2]] and [LIT-1](LIT-001.md \"refuted\").")
    bad = " ".join(annotations.survey().bad)
    assert "declares no reference `refutes`" in bad
    assert "declares no reference `refuted`" in bad
    assert "LIT-009 is no document" in bad
    assert "to itself" in bad


# --- push down ---------------------------------------------------------------

def test_an_explained_relation_cited_plainly_is_named(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1, extended_by=["LIT-002"])
    b = note(root, 2, "Nothing here is new (see [[LIT-1]]).",
             extends=["LIT-001"], cites=["LIT-001"])
    # One citation names one relation: the first takes it, and the second
    # has no plain citation left, so it is the author's to explain — said
    # before the fix as well as after.
    s = annotations.survey()
    assert len(s.unannotated) == 1 and len(s.unexplained) == 1
    annotations.complete(fix=True)
    assert "[[extends::LIT-1]]" in b.read_text()
    s = annotations.survey()
    assert s.unannotated == []
    assert len(s.unexplained) == 1 and "`cites: LIT-001`" in s.unexplained[0]


def test_a_plain_link_and_a_bare_code_are_named_too(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 3)
    b = note(root, 2, "See [LIT-1](LIT-001.md) and LIT-3.",
             cites=["LIT-001", "LIT-003"])
    link_refs.run(fix=True)
    text = b.read_text()
    assert '[LIT-1](LIT-001.md "cites")' in text
    assert '(LIT-003.md "cites")' in text and "[[" not in text
    assert annotations.survey().unannotated == []


def test_an_uncited_explained_relation_is_reported_not_fixed(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    b = note(root, 2, "foo bar baz.", cites=["LIT-001"])
    before = b.read_text()
    s = annotations.complete(fix=True)
    assert len(s.unexplained) == 1
    assert "[[cites::LIT-001]]" in s.unexplained[0]
    assert b.read_text() == before


def test_unexplained_ok_acknowledges_one_code(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 3)
    note(root, 2, "<!-- unexplained-ok: LIT-001 — the title says it -->\n"
                  "foo.", cites=["LIT-001", "LIT-003"])
    rows = annotations.survey().unexplained
    assert len(rows) == 1 and "LIT-003" in rows[0]


def test_a_named_relation_is_explained(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1, extended_by=["LIT-002"])
    note(root, 2, "Builds on [[extends::LIT-1]].", extends=["LIT-001"])
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
    note(root, 3)
    note(root, 2, "[[extends::LIT-1]] [[refutes::LIT-3]] LIT-3",
         cites=["LIT-001", "LIT-003"])
    names = {n for n, _, _ in lint.status_sections()}
    for name in ("unrecorded-relations", "unannotated-relations",
                 "unexplained-relations", "bad-annotations"):
        assert name in lint.FAILABLE and name in names
