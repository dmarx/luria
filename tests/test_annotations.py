# tests/test_annotations.py
"""A relation stated in prose, and prose owed to a relation (#333).

A relation is stated with the directive grammar every acknowledgement uses,
named by the field that holds it: `<!-- ref::extends: LIT-2 -->`. `[[extends::X]]`
is shorthand the link fixer expands into a link plus that statement.

Push up: a statement missing from frontmatter is the fixer's to write. Push
down: a reference declared `explain:` wants each code it holds accounted for
in the body — cited anywhere (`cited`, or `true`), or cited with a statement
governing the citation (`stated`); at either strength a statement's `—
reason` also counts. Nothing here is special to any one relation: every
fixture relation is user-declared, and the built-in successor works too.
"""

from __future__ import annotations

from pathlib import Path

import pytest
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
        explain: stated
      extended_by:
        scheme: LIT
        required: false
        many: true
        converse: extends
      cites:
        scheme: LIT
        required: false
        many: true
        explain: stated
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


def stated(path: Path) -> list[tuple[str, str]]:
    names = set(annotations.fields_of(path))
    return [(s.relation, s.code) for s in
            annotations.statements(path, path.read_text(), names)[0]]


# --- the grammar -------------------------------------------------------------

def test_a_statement_is_a_directive_named_by_the_field(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, "Builds on it. <!-- ref::extends: LIT-2, LIT-3 -->\n\n"
                      "<!-- ref::extended_by-file: LIT-4 — the follow-up -->")
    assert stated(a) == [("extends", "LIT-002"), ("extends", "LIT-003"),
                         ("extended_by", "LIT-004")]


DOI_REMOTE = r"""
remotes:
  DOI:
    uid: 10\.\d{4,9}/[^\s\]\)>,;]+
    delim: ':'
    url: https://doi.org/{uid}
"""


def test_a_remote_code_with_no_hyphen_is_read_not_crashed_on(
        tmp_path, monkeypatch):
    """A DOI composes with `:`, so its code has no `-` to split a tail
    from. `luria lint` on the anthology died here, with nothing opted in."""
    project(tmp_path, monkeypatch, PAIRED + DOI_REMOTE)
    text = ("---\ntitle: x\n---\n\n"
            "[DOI:10.1109/72.238311](https://doi.org/10.1109/72.238311)\n")
    assert [c.code for c in annotations.citations(text)] == [
        "DOI:10.1109/72.238311"]


def test_quoted_and_frontmatter_statements_say_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, "`<!-- ref::extends: LIT-2 -->`\n\n"
                      "```\n<!-- ref::extends: LIT-2 -->\n```")
    text = a.read_text().replace("date:", "# extends: LIT-2\ndate:")
    a.write_text(text)
    assert stated(a) == []


def test_a_typed_wikilink_expands_to_a_link_and_a_statement(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 2)
    a = note(root, 1, "Builds on [[extends::LIT-2|the base]].")
    new, n = doc_refs.expand_wikilinks(a.read_text(), a)
    assert n == 1
    assert "[the base](LIT-002.md)<!-- ref::extends: LIT-002 -->" in new


def test_a_typed_wikilink_this_document_cannot_hold_is_not_expanded(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 2)
    a = note(root, 1, "Contra [[refutes::LIT-2]].")
    assert doc_refs.expand_wikilinks(a.read_text(), a)[1] == 0
    errors: list[str] = []
    lint.check_wikilinks(errors)
    assert any("`refutes`" in e for e in errors)


def test_a_field_may_not_end_in_a_scope_suffix(tmp_path, monkeypatch):
    for name in ("extends-block", "notes-file"):
        with pytest.raises(ValueError, match="-block. or .-file"):
            project(tmp_path, monkeypatch, f"""
                                           schemes:
                                             LIT:
                                               references:
                                                 {name}:
                                                   scheme: LIT
                                                   required: false
                                           """)
            config.current()


def test_the_namespace_frees_the_directive_vocabulary(tmp_path, monkeypatch):
    """`pin` is a directive; `ref::pin` is a relation. A field may take any
    name the fixed vocabulary spends."""
    root = project(tmp_path, monkeypatch, """
                                          schemes:
                                            LIT:
                                              references:
                                                pin:
                                                  scheme: LIT
                                                  required: false
                                                  many: true
                                          """)
    note(root, 2)
    a = note(root, 1, "<!-- ref::pin: LIT-2 -->")
    annotations.complete(fix=True)
    assert meta(a)["pin"] == ["LIT-002"]


def test_a_misspelt_field_is_reported_not_ignored(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 2)
    note(root, 1, "<!-- ref::extnds: LIT-2 -->")
    bad = annotations.survey().bad
    assert len(bad) == 1 and "`ref::extnds` names no reference field" in bad[0]


def test_a_titled_link_is_still_checked_for_its_target(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, 'See [LIT-9](LIT-009.md "a tooltip").')
    flagged, _ = link_targets.broken([a])
    assert len(flagged) == 1 and "LIT-009.md" in flagged[0]


# --- push up -----------------------------------------------------------------

def test_a_stated_relation_is_written_into_this_documents_field(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1)
    b = note(root, 2, "Builds on [[extends::LIT-1]].")
    s = annotations.survey()
    assert len(s.unrecorded) == 1 and "`ref::extends: LIT-001`" in s.unrecorded[0]
    link_refs.run(fix=True)
    assert meta(b)["extends"] == ["LIT-001"]
    assert meta(a)["extended_by"] == ["LIT-002"]       # the converse, too
    assert "[LIT-1](LIT-001.md)<!-- ref::extends: LIT-001 -->" in b.read_text()
    s = annotations.survey()
    assert (s.unrecorded, s.bad) == ([], [])


def test_the_converse_name_states_the_other_direction(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    a = note(root, 1, "Carried further. <!-- ref::extended_by: LIT-2 -->")
    b = note(root, 2)
    link_refs.run(fix=True)
    assert meta(a)["extended_by"] == ["LIT-002"]
    assert meta(b)["extends"] == ["LIT-001"]


def test_an_edge_held_by_the_converse_side_is_already_recorded(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "Carried further. <!-- ref::extended_by: LIT-2 -->")
    note(root, 2, extends=["LIT-001"])
    assert annotations.survey().unrecorded == []


def test_a_scalar_relation_is_written_as_a_scalar(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    b = note(root, 2, "From it. <!-- ref::source: LIT-1 -->")
    annotations.complete(fix=True)
    assert meta(b)["source"] == "LIT-001"


def test_the_builtin_successor_is_a_relation_like_any_other(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 2)
    a = note(root, 1, "Replaced. <!-- ref::superseded_by: LIT-2 -->")
    annotations.complete(fix=True)
    assert meta(a)["superseded_by"] == ["LIT-002"]


def test_a_scalar_already_holding_another_code_is_not_overwritten(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 3)
    b = note(root, 2, "<!-- ref::source: LIT-1 -->", source="LIT-003")
    s = annotations.complete(fix=True)
    assert s.writes == [] and "contradicts" in s.bad[0]
    assert meta(b)["source"] == "LIT-003"


def test_what_the_record_cannot_hold_is_a_bad_annotation(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 2, "<!-- ref::extends: LIT-9, LIT-2, nonsense -->")
    bad = " ".join(annotations.survey().bad)
    assert "LIT-009 is no document" in bad
    assert "to itself" in bad
    assert "`ref::extends: nonsense` names no code" in bad


def test_an_expired_statement_states_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 2, "<!-- ref::extends: LIT-1 until 2000-01-01 -->")
    assert annotations.survey().unrecorded == []


# --- push down ---------------------------------------------------------------

def test_a_plain_citation_of_an_explained_relation_gains_its_statement(
        tmp_path, monkeypatch):
    """Both explained relations holding LIT-001 are stated beside the one
    citation — a citation can carry any number of statements."""
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1, extended_by=["LIT-002"])
    b = note(root, 2, "Nothing here is new (see [[LIT-1]]).",
             extends=["LIT-001"], cites=["LIT-001"])
    s = annotations.survey()
    assert len(s.unannotated) == 2 and s.unexplained == []
    link_refs.run(fix=True)
    text = b.read_text()
    assert "<!-- ref::extends: LIT-001 -->" in text
    assert "<!-- ref::cites: LIT-001 -->" in text
    s = annotations.survey()
    assert (s.unannotated, s.unexplained) == ([], [])


def test_a_statement_governs_the_paragraph_it_introduces(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 2, "<!-- ref::cites-block: LIT-1 -->\n"
                  "The whole paragraph is about\nwhat [LIT-1](LIT-001.md) did.",
         cites=["LIT-001"])
    s = annotations.survey()
    assert (s.unannotated, s.unexplained) == ([], [])


def test_a_statement_far_from_any_citation_explains_nothing(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 2, "<!-- ref::cites: LIT-1 -->\n\nfoo.\n\nLater: LIT-1.",
         cites=["LIT-001"])
    rows = annotations.survey().unexplained
    assert len(rows) == 1 and "no citation beside it" in rows[0]


def test_a_statements_reason_is_its_explanation(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 2, "<!-- ref::cites-file: LIT-1 — the method section is its -->",
         cites=["LIT-001"])
    s = annotations.survey()
    assert (s.unannotated, s.unexplained) == ([], [])


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


def test_relations_without_explain_ask_nothing_of_prose(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, extended_by=["LIT-002"])
    note(root, 2, "See LIT-1.", extends=["LIT-001"])
    s = annotations.survey()
    assert (s.unannotated, s.unexplained) == ([], [])


# --- the lint ----------------------------------------------------------------

def test_every_class_is_a_lint_class(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, EXPLAINED)
    note(root, 1)
    note(root, 3)
    note(root, 4)
    note(root, 2, "<!-- ref::extends: LIT-1, LIT-9 --> LIT-3",
         cites=["LIT-003", "LIT-004"])
    names = {n for n, _, _ in lint.status_sections()}
    for name in ("unrecorded-relations", "unannotated-relations",
                 "unexplained-relations", "bad-annotations"):
        assert name in lint.FAILABLE and name in names


# --- strengths ---------------------------------------------------------------

CITED = EXPLAINED.replace("explain: stated", "explain: cited")


def test_explain_takes_a_strength(tmp_path, monkeypatch):
    for raw, want in (("cited", "cited"), ("stated", "stated"),
                      ("true", "cited"), ("false", "")):
        project(tmp_path, monkeypatch,
                EXPLAINED.replace("explain: stated", f"explain: {raw}"))
        refs = {r.field: r.explain
                for r in config.current().schemes["LIT"].references}
        assert refs["cites"] == want


def test_an_unknown_strength_is_refused(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="not a strength"):
        project(tmp_path, monkeypatch,
                EXPLAINED.replace("explain: stated", "explain: always"))
        config.current()


def test_cited_takes_any_citation_as_the_explanation(tmp_path, monkeypatch):
    """The weaker strength: a plain citation serves the relation, so there is
    nothing to annotate and nothing for the fixer to write."""
    root = project(tmp_path, monkeypatch, CITED)
    note(root, 1, extended_by=["LIT-002"])
    b = note(root, 2, "Nothing here is new (see [[LIT-1]]).",
             extends=["LIT-001"], cites=["LIT-001"])
    before = b.read_text()
    s = annotations.complete(fix=True)
    assert (s.unannotated, s.unexplained, s.inserts) == ([], [], [])
    assert b.read_text() == before


def test_cited_still_reports_a_relation_the_prose_never_mentions(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, CITED)
    note(root, 1)
    note(root, 3)
    note(root, 2, "Only LIT-3 comes up here.", cites=["LIT-001", "LIT-003"])
    rows = annotations.survey().unexplained
    assert len(rows) == 1 and "never cites LIT-001" in rows[0]


def test_cited_accepts_a_statement_with_a_reason(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, CITED)
    note(root, 1)
    note(root, 2, "<!-- ref::cites-file: LIT-1 — the method section is its -->",
         cites=["LIT-001"])
    assert annotations.survey().unexplained == []
