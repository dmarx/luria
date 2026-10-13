# tests/test_pattern_chains.py
"""A chain walking a named path pattern (#371).

The case that motivated it: an argument runs claim → inference → claim, the
inference is its own document, and a chain over fields stops at it. A
pattern relates the two claims through the inference, and the chain draws
the line the record states.
"""
from __future__ import annotations

from pathlib import Path

from _config import merged
from luria import chains, config, invariants

BASE = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics: {logic: about logic, ethics: about ethics}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    fields:
      topic: {vocabulary: topics}
    references:
      premise_of: {scheme: INF, many: true, required: false, converse: premises}
  INF:
    dir: record/inferences.d
    output: docs/inferences
    references:
      premises: {scheme: CLAIM, many: true, required: false, converse: premise_of}
      concludes: {scheme: CLAIM, required: false}
patterns:
  follows_from: (b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)
chains:
  argument:
    scheme: CLAIM
    relation: follows_from
    output: docs/arguments.md
    title: Lines of argument
"""


def project(tmp_path: Path, monkeypatch, *extra) -> Path:
    (tmp_path / "luria.yaml").write_text(merged(BASE, *extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, scheme: str, number: int, title: str, **fields) -> None:
    code = f"{scheme}-{number:03d}"
    folder = {"CLAIM": "claims.d", "INF": "inferences.d"}[scheme]
    front = ["---", "status: Active", f"title: {title!r}", "date: '2026-01-01'"]
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


def argument(root: Path) -> None:
    """C1 and C2 are premises of I1, which concludes C3; C3 is a premise of
    I2, which concludes nothing yet — a partial match, which is no step."""
    doc(root, "CLAIM", 1, "First premise", premise_of=["INF-001"])
    doc(root, "CLAIM", 2, "Second premise", premise_of=["INF-001"])
    doc(root, "CLAIM", 3, "The conclusion", premise_of=["INF-002"])
    doc(root, "INF", 1, "Modus ponens", concludes="CLAIM-003")
    doc(root, "INF", 2, "An unfinished step")


def test_the_line_runs_through_the_inference(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    argument(root)
    (line,) = chains.walk()
    assert [d.code for d in line.spine] == ["CLAIM-001", "CLAIM-003",
                                            "CLAIM-002"]
    assert line.under == {"CLAIM-003": "CLAIM-001"}
    assert line.also == {"CLAIM-003": ["CLAIM-002"]}


def test_the_page_names_what_each_step_went_through(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    argument(root)
    page = chains.outputs()[root / "docs/arguments.md"]
    assert ("  - [CLAIM-003](../record/claims.d/CLAIM-003.md) — The conclusion "
            "*(Active)* — through [INF-001](../record/inferences.d/INF-001.md)"
            " — also follows from CLAIM-002\n" in page)
    assert ("walked from `follows_from` "
            "(`(b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)`)"
            in page)


def test_a_path_that_stops_partway_draws_no_step_and_no_section(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    argument(root)
    page = chains.outputs()[root / "docs/arguments.md"]
    assert "INF-002" not in page
    assert "## Open" not in page


def test_a_converse_side_statement_draws_the_same_line(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM", 1, "Premise")
    doc(root, "CLAIM", 2, "Conclusion")
    doc(root, "INF", 1, "Step", premises=["CLAIM-001"], concludes="CLAIM-002")
    (line,) = chains.walk()
    assert line.under == {"CLAIM-002": "CLAIM-001"}


def test_a_pattern_cycle_is_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM", 1, "A", premise_of=["INF-001"])
    doc(root, "CLAIM", 2, "B", premise_of=["INF-002"])
    doc(root, "INF", 1, "A so B", concludes="CLAIM-002")
    doc(root, "INF", 2, "B so A", concludes="CLAIM-001")
    (row,) = chains.rows()
    assert "CLAIM-001 and CLAIM-002 each come before the other" in row
    assert "`follows_from`" in row


def test_a_chain_invariant_covers_pattern_steps(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, {"chains": {"argument": {
        "invariant": "topic"}}})
    doc(root, "CLAIM", 1, "Premise", topic="logic", premise_of=["INF-001"])
    doc(root, "CLAIM", 2, "Conclusion", topic="ethics")
    doc(root, "INF", 1, "Step", concludes="CLAIM-002")
    (hit,) = invariants.edges(config.current().chains["argument"])
    assert hit.codes == ("CLAIM-001", "CLAIM-002")


def test_fields_and_patterns_share_one_spine(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, {
        "schemes": {"CLAIM": {"references": {
            "refines": {"scheme": "CLAIM", "many": True, "required": False}}}},
        "chains": {"argument": {"relation": ["follows_from", "refines"]}}})
    doc(root, "CLAIM", 1, "Premise", premise_of=["INF-001"])
    doc(root, "CLAIM", 2, "Conclusion")
    doc(root, "CLAIM", 3, "Refined conclusion", refines=["CLAIM-002"])
    doc(root, "INF", 1, "Step", concludes="CLAIM-002")
    (line,) = chains.walk()
    assert line.under == {"CLAIM-002": "CLAIM-001", "CLAIM-003": "CLAIM-002"}
    page = chains.outputs()[root / "docs/arguments.md"]
    assert "Refined conclusion *(Active)*\n" in page
