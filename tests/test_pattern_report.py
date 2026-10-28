# tests/test_pattern_report.py
"""A pattern declared `report: true` is a warning class of its own.

The case that motivated it (the nucleation record's decision 57): an Active claim resting on
a Proposed one, and an Open question with an Active answer, were no finding
at all, because a reference checks only that its target is in force and
`Proposed` counts. Each test here fires the class on a fixture that has the
shape, and checks the dials treat it as they treat a built-in class.

The `match:` values are quoted: a property map's `{status: 'Active'}` holds
`: `, which a plain YAML scalar may not, so the unquoted form the request
was written in does not parse.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged
from luria import config, lint, pattern_report, pattern_rules

BASE = """
issue_url: https://example.test/issues/{n}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    references:
      rests_on: {scheme: CLAIM, many: true, required: false}
      answers: {scheme: QUESTION, many: true, required: false}
  QUESTION:
    dir: record/questions.d
    output: docs/questions
patterns:
  inverted_premise:
    match: "(c:CLAIM {status: 'Active'})-[:rests_on]->(p:CLAIM {status: 'Proposed'})"
    report: true
    blurb: An Active claim resting on a Proposed one.
  answered_but_open:
    match: "(q:QUESTION {status: 'Open'})<-[:answers]-(c:CLAIM {status: 'Active'})"
    report: true
  premises: (c:CLAIM)-[:rests_on]->(p:CLAIM)
"""

FOLDERS = {"CLAIM": "claims.d", "QUESTION": "questions.d"}


def project(tmp_path: Path, monkeypatch, *extra) -> Path:
    (tmp_path / "luria.yaml").write_text(merged(BASE, *extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, scheme: str, number: int, status: str, body: str = "",
        **fields) -> Path:
    code = f"{scheme}-{number:03d}"
    front = ["---", f"status: {status}", f"title: 'Doc {number}'",
             "date: '2026-01-01'"]
    for key, value in fields.items():
        front.append(f"{key}:")
        front += [f"- {v}" for v in value]
    front += ["---", "", f"# {code}: Doc {number}", "", body or "Body."]
    path = root / "record" / FOLDERS[scheme] / f"{code}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(front) + "\n")
    return path


def shaped(root: Path) -> None:
    """CLAIM-002 (Active) rests on CLAIM-001 (Proposed); CLAIM-003 (Active)
    rests on CLAIM-002 (Active), which is fine; QUESTION-001 is Open and
    CLAIM-002 answers it."""
    doc(root, "CLAIM", 1, "Proposed")
    doc(root, "CLAIM", 2, "Active", rests_on=["CLAIM-001"],
        answers=["QUESTION-001"])
    doc(root, "CLAIM", 3, "Active", rests_on=["CLAIM-002"])
    doc(root, "QUESTION", 1, "Open")


def sections() -> dict[str, tuple[str, list[str]]]:
    return {n: (h, rows) for n, h, rows in lint.status_sections()}


def test_each_match_is_a_row_of_a_class_named_after_the_pattern(
        tmp_path, monkeypatch):
    """Fired once on the shape it exists for (DP-6)."""
    root = project(tmp_path, monkeypatch)
    shaped(root)
    found = sections()
    headline, rows = found["inverted_premise"]
    assert rows == ["record/claims.d/CLAIM-002.md: CLAIM-002 — with CLAIM-001"]
    assert "An Active claim resting on a Proposed one." in headline
    _, rows = found["answered_but_open"]
    assert rows == [
        "record/questions.d/QUESTION-001.md: QUESTION-001 — with CLAIM-002"]


def test_a_pattern_without_report_is_no_class(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    shaped(root)
    assert "premises" not in sections()
    assert "premises" not in lint.failable()
    assert set(lint.reported_patterns()) == {"inverted_premise",
                                             "answered_but_open"}


def test_a_shape_the_record_lacks_reports_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM", 1, "Active")
    doc(root, "CLAIM", 2, "Active", rests_on=["CLAIM-001"])
    assert "inverted_premise" not in sections()


def test_a_match_with_no_named_node_is_still_a_row(tmp_path, monkeypatch):
    """The row is positional: the first node's document, named or not."""
    root = project(tmp_path, monkeypatch, {"patterns": {"anon": {
        "match": "(:CLAIM {status: 'Active'})-[:rests_on]->(:CLAIM)",
        "report": True}}})
    shaped(root)
    assert sorted(pattern_rules.reported()["anon"]) == [
        ("CLAIM-002", "CLAIM-001"), ("CLAIM-003", "CLAIM-002")]


def test_the_dials_name_a_pattern_class(tmp_path, monkeypatch, capsys):
    root = project(tmp_path, monkeypatch,
                   {"lint": {"fail_on": ["inverted_premise"],
                             "mute": ["answered_but_open"]}})
    shaped(root)
    errors: list[str] = []
    lint.report_warnings(errors)
    err = capsys.readouterr().err
    assert any("failing: `fail_on` names 'inverted_premise'" in e
               for e in errors), errors
    assert "record/claims.d/CLAIM-002.md: CLAIM-002 — with CLAIM-001" in errors
    assert not any("no warning class" in e for e in errors), errors
    assert "answered_but_open" not in err and not any(
        "QUESTION-001" in e for e in errors)


def test_a_baseline_holds_a_pattern_class_to_a_count(tmp_path, monkeypatch,
                                                      capsys):
    root = project(tmp_path, monkeypatch,
                   {"lint": {"baseline": {"inverted_premise": 1}}})
    shaped(root)
    errors: list[str] = []
    lint.report_warnings(errors)
    assert errors == []
    doc(root, "CLAIM", 4, "Active", rests_on=["CLAIM-001"])
    lint.report_warnings(errors)
    assert any("2 found against a `baseline` of 1" in e for e in errors)


def test_a_pattern_class_is_unknown_to_a_record_that_does_not_declare_it(
        tmp_path, monkeypatch, capsys):
    root = project(tmp_path, monkeypatch, {"lint": {"fail_on": ["premises"]}})
    shaped(root)
    errors: list[str] = []
    lint.report_warnings(errors)
    assert any("`fail_on` names 'premises', which is no warning class" in e
               for e in errors)


def test_the_first_document_acknowledges_its_rows(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   {"lint": {"fail_on": ["inverted_premise"]}})
    shaped(root)
    doc(root, "CLAIM", 2, "Active",
        "<!-- pattern-ok: inverted_premise — resting on the draft on "
        "purpose -->\n\nBody.",
        rests_on=["CLAIM-001"], answers=["QUESTION-001"])
    found = pattern_report.findings()
    assert "inverted_premise" not in found.rows
    assert found.acknowledged == 1 and found.stale == []
    errors: list[str] = []
    lint.report_warnings(errors)
    assert errors == []


def test_an_acknowledgement_that_answers_for_nothing_is_stale(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM", 1, "Active")
    doc(root, "CLAIM", 2, "Active",
        "<!-- pattern-ok: inverted_premise — it was a draft once -->\n\n"
        "<!-- pattern-ok: premises — not a reported pattern -->\n",
        rests_on=["CLAIM-001"])
    stale = pattern_report.findings().stale
    assert any("answers for no match" in s for s in stale), stale
    assert any("names premises, which is no pattern declared `report: true`"
               in s for s in stale), stale
    _, rows = sections()["stale-directives"]
    assert any("pattern-ok" in r for r in rows)


@pytest.mark.parametrize("name", ["broken-chains", "load-bearing",
                                  "expired-directives"])
def test_a_pattern_may_not_take_a_built_in_class_name(tmp_path, monkeypatch,
                                                      name):
    project(tmp_path, monkeypatch, {"patterns": {name: {
        "match": "(c:CLAIM)-[:rests_on]->(p:CLAIM)", "report": True}}})
    with pytest.raises(ValueError, match="already a built-in class"):
        config.current()


def test_a_built_in_name_without_report_is_no_collision(tmp_path, monkeypatch):
    """Only a reported pattern makes a class; a chain-only one names none."""
    project(tmp_path, monkeypatch, {"patterns": {"broken-chains":
                                                 "(c:CLAIM)-[:rests_on]->(p:CLAIM)"}})
    assert "broken-chains" in config.current().patterns


def test_report_must_be_a_boolean(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"patterns": {"x": {
        "match": "(c:CLAIM)-[:rests_on]->(p:CLAIM)", "report": "yes"}}})
    with pytest.raises(ValueError, match="is not true or false"):
        config.current()
