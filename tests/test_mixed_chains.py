# tests/test_mixed_chains.py
"""A chain over several schemes.

The case that motivated it: a record's objection threads run claim →
argument → claim. An objection to an inference undercuts the argument, not
its conclusion, and an argument nobody objects to yet is still a verdict
the thread should hold. With one scheme per chain the argument could only
be what a step went *through*, never a step, so a bare argument had no
place on the page at all. Listing both schemes lets a field or a pattern
land on either.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged
from luria import chains, config, invariants

BASE = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics: {logic: about logic, ethics: about ethics}
  roles: {thesis: asserted, counter: an objection}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    fields:
      topic: {vocabulary: topics}
      role: {vocabulary: roles}
    references:
      objects_to: {scheme: CLAIM, many: true, required: false}
      undercuts: {scheme: INF, many: true, required: false}
  INF:
    dir: record/inferences.d
    output: docs/inferences
    fields:
      topic: {vocabulary: topics}
    references:
      concludes: {scheme: CLAIM, required: false}
chains:
  dialectic:
    scheme: [CLAIM, INF]
    relation: [objects_to, undercuts, concludes]
    output: docs/dialectic.md
    title: Objections and replies
    facet_by: [role, status]
"""


def project(tmp_path: Path, monkeypatch, *extra) -> Path:
    (tmp_path / "luria.yaml").write_text(merged(BASE, *extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def refused(tmp_path: Path, monkeypatch, *extra) -> str:
    project(tmp_path, monkeypatch, *extra)
    with pytest.raises(ValueError) as caught:
        config.current()
    return str(caught.value)


def doc(root: Path, scheme: str, number: int, title: str,
        status: str = "Active", **fields) -> None:
    code = f"{scheme}-{number:03d}"
    folder = {"CLAIM": "claims.d", "INF": "inferences.d"}[scheme]
    front = ["---", f"status: {status}", f"title: {title!r}",
             "date: '2026-01-01'"]
    for key, value in fields.items():
        if isinstance(value, (list, tuple)):
            front.append(f"{key}:")
            front += [f"- {v}" for v in value]
        else:
            front.append(f"{key}: {value}")
    front += ["---", "", f"# {code}: {title}", "", "Body."]
    path = root / "record" / folder / f"{code}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(front) + "\n")


def thread(root: Path) -> None:
    """C1 is a thesis; I1 argues for it; C2 undercuts I1; C3 objects to C2."""
    doc(root, "CLAIM", 1, "The thesis", role="thesis")
    doc(root, "INF", 1, "By analogy", status="Proposed", concludes="CLAIM-001")
    doc(root, "CLAIM", 2, "Same structure, not the same mechanism",
        role="counter", undercuts=["INF-001"])
    doc(root, "CLAIM", 3, "The mechanism is shared", role="thesis",
        objects_to=["CLAIM-002"])


def test_a_chain_may_list_several_schemes(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    chain = config.current().chains["dialectic"]
    assert chain.schemes == ("CLAIM", "INF")
    assert chain.scheme == "CLAIM"


def test_one_scheme_is_a_list_of_one(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"chains": {"dialectic": {
        "scheme": "CLAIM", "relation": "objects_to"}}})
    assert config.current().chains["dialectic"].schemes == ("CLAIM",)


def test_a_step_may_be_a_document_of_another_listed_scheme(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    thread(root)
    (line,) = chains.walk()
    assert [d.code for d in line.spine] == ["CLAIM-001", "INF-001",
                                            "CLAIM-002", "CLAIM-003"]
    assert line.under == {"INF-001": "CLAIM-001", "CLAIM-002": "INF-001",
                          "CLAIM-003": "CLAIM-002"}


def test_the_page_links_each_step_into_its_own_scheme(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    thread(root)
    page = chains.outputs()[root / "docs/dialectic.md"]
    assert ("  - [INF-001](../record/inferences.d/INF-001.md) — By analogy "
            "*(Proposed)*\n" in page)
    assert ("    - [CLAIM-002](../record/claims.d/CLAIM-002.md) — Same "
            "structure, not the same mechanism *(counter, Active)*\n" in page)
    assert "on CLAIM and INF documents" in page


def test_a_mixed_pattern_draws_a_step_between_schemes(tmp_path, monkeypatch):
    """A pattern whose two ends are different schemes, which is the point:
    only arguments not in force join the thread."""
    root = project(tmp_path, monkeypatch, {
        "patterns": {"contested": {"match": (
            "(i:INF)-[:concludes]->(c:CLAIM) "
            "WHERE NOT (i {status: 'Active'})")}},
        "chains": {"dialectic": {"relation": ["objects_to", "contested"]}}})
    doc(root, "CLAIM", 1, "The thesis", role="thesis")
    doc(root, "INF", 1, "A doubted step", status="Rejected",
        concludes="CLAIM-001")
    doc(root, "INF", 2, "A sound step", concludes="CLAIM-001")
    (line,) = chains.walk()
    assert [d.code for d in line.spine] == ["CLAIM-001", "INF-001"]


def test_a_pattern_end_outside_the_listed_schemes_is_refused(
        tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {
        "patterns": {"contested": "(i:INF)-[:concludes]->(c:CLAIM)"},
        "chains": {"dialectic": {"scheme": "CLAIM",
                                 "relation": "contested"}}})
    assert ("pattern 'contested', which runs from INF to CLAIM" in msg)
    assert "list INF in its `scheme`" in msg


def test_a_field_into_an_unlisted_scheme_is_refused(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"chains": {"dialectic": {
        "scheme": "CLAIM", "relation": ["objects_to", "undercuts"]}}})
    assert "`relation` names 'undercuts', which can point at INF" in msg
    assert "list INF in its `scheme`" in msg


def test_an_undeclared_scheme_in_the_list_is_refused(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"chains": {"dialectic": {
        "scheme": ["CLAIM", "NOPE"]}}})
    assert "scheme 'NOPE' is not declared" in msg


def test_a_facet_one_listed_scheme_holds_is_enough(tmp_path, monkeypatch):
    """`role` is a CLAIM field. An argument has no voice, and its step shows
    its status alone rather than the chain being refused."""
    project(tmp_path, monkeypatch)
    assert config.current().chains["dialectic"].facet_by == ("role", "status")


def test_a_facet_no_listed_scheme_holds_is_refused(tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"chains": {"dialectic": {
        "facet_by": ["weight"]}}})
    assert "`facet_by` names 'weight', which neither CLAIM nor INF declares" \
        in msg


def test_a_field_one_listed_scheme_declares_is_walked(tmp_path, monkeypatch):
    """`concludes` is INF's; CLAIM does not declare it, and that is not a
    finding when INF is listed."""
    project(tmp_path, monkeypatch)
    assert "concludes" in config.current().chains["dialectic"].relation


def test_an_invariant_must_be_held_by_every_listed_scheme(
        tmp_path, monkeypatch):
    msg = refused(tmp_path, monkeypatch, {"chains": {"dialectic": {
        "invariant": "role"}}})
    assert "`invariant` names 'role', which INF does not declare" in msg


def test_a_mixed_chain_invariant_covers_cross_scheme_steps(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, {"chains": {"dialectic": {
        "invariant": "topic"}}})
    doc(root, "CLAIM", 1, "Thesis", topic="logic")
    doc(root, "INF", 1, "Step", topic="ethics", concludes="CLAIM-001")
    (hit,) = invariants.edges(config.current().chains["dialectic"])
    assert hit.codes == ("CLAIM-001", "INF-001")
