# tests/test_reference_schemes.py
"""A reference whose codes may come from any of several schemes (#160).

`scheme` named exactly one family, so a relation with two legitimate target
families could not be declared. The workarounds were a field per target —
the type system's job moved into the field name, and every reader of the
graph left to union the edges — or a loose `requires` field that checks
nothing (ADR-060).

`scheme` now takes a list as well. A single string is a list of one, so no
existing config changes; every check that compared a code's scheme against
the declared one tests membership instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from _config import merged

from luria import config, contract, edges, lint, relations

BASE = """
issue_url: https://example.test/issues/{n}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    references:
      rests_on:
        scheme: [LIT, CASE]
        required: false
        many: true
        converse: supports
  LIT:
    dir: record/literature.d
    output: docs/literature
    references:
      supports:
        scheme: CLAIM
        required: false
        many: true
        converse: rests_on
  CASE:
    dir: record/cases.d
    output: docs/cases
    references:
      supports:
        scheme: CLAIM
        required: false
        many: true
        converse: rests_on
  NOTE:
    dir: record/notes.d
    output: docs/notes
"""

DIRS = {"CLAIM": "claims.d", "LIT": "literature.d", "CASE": "cases.d",
        "NOTE": "notes.d"}


def project(tmp_path, monkeypatch, *extra: str | dict) -> Path:
    for d in DIRS.values():
        (tmp_path / "record" / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "luria.yaml").write_text(merged(BASE, *extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, prefix: str, n: int, front: str = "", body: str = "") -> Path:
    path = root / "record" / DIRS[prefix] / f"{prefix}-{n:03d}.md"
    path.write_text(
        f"---\nstatus: Active\ntitle: '{prefix} {n}'\ntags:\n- record\n"
        f"date: '2026-01-01'\n{front}---\n\n# {prefix}-{n:03d}: {prefix} {n}\n\n"
        f"{body or 'Body.'}\n")
    return path


def without(path: str) -> dict:
    """BASE with one dotted key removed."""
    raw = yaml.safe_load(BASE)
    *parents, last = path.split(".")
    node = raw
    for key in parents:
        node = node[key]
    node.pop(last)
    return raw


def contract_errors() -> list[str]:
    errors: list[str] = []
    lint.check_contracts(errors)
    return errors


# ── declaring it ──────────────────────────────────────────────────────────

def test_a_list_declares_every_scheme_it_names(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    ref = next(r for r in config.current().schemes["CLAIM"].references
               if r.field == "rests_on")
    assert ref.scheme == ("LIT", "CASE")


def test_a_string_is_a_list_of_one(tmp_path, monkeypatch):
    """No existing config changes meaning."""
    project(tmp_path, monkeypatch)
    ref = next(r for r in config.current().schemes["LIT"].references
               if r.field == "supports")
    assert ref.scheme == ("CLAIM",)


def test_every_scheme_in_the_list_must_be_declared(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"schemes": {"CLAIM": {"references": {
        "rests_on": {"scheme": ["LIT", "CAES"]}}}}})
    with pytest.raises(ValueError, match="names scheme 'CAES', which is not"):
        config.current()


@pytest.mark.parametrize("value, message", [
    ([], "needs a `scheme`"),
    (["LIT", "LIT"], "names LIT twice"),
])
def test_an_empty_or_repeated_list_is_refused(tmp_path, monkeypatch, value,
                                              message):
    project(tmp_path, monkeypatch, {"schemes": {"CLAIM": {"references": {
        "rests_on": {"scheme": value, "converse": ""}}}}})
    with pytest.raises(ValueError, match=message):
        config.current()


# ── checking it ───────────────────────────────────────────────────────────

def test_a_code_from_any_named_scheme_passes(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT", 1, "supports:\n- CLAIM-001\n")
    doc(root, "CASE", 1, "supports:\n- CLAIM-001\n")
    doc(root, "CLAIM", 1, "rests_on:\n- LIT-001\n- CASE-001\n")
    assert contract_errors() == []


def test_a_code_from_another_scheme_names_every_one_it_could_be(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "NOTE", 1)
    doc(root, "CLAIM", 1, "rests_on:\n- NOTE-001\n")
    errors = contract_errors()
    assert any("`rests_on: NOTE-001` is not a LIT or CASE code" in e
               and "names a LIT or CASE document" in e for e in errors), errors


def test_a_code_is_resolved_in_its_own_scheme(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM", 1, "rests_on:\n- CASE-009\n")
    errors = contract_errors()
    assert any("`rests_on: CASE-009` resolves to no CASE document" in e
               for e in errors), errors


def test_the_contract_describes_the_union(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    lines = contract.describe(contract.for_scheme(
        config.current().schemes["CLAIM"]))
    assert any("`rests_on` — optional, one or more `LIT` or `CASE` codes"
               in line for line in lines), lines


# ── the graph ─────────────────────────────────────────────────────────────

def test_each_code_is_an_edge_whichever_scheme_it_names(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT", 1)
    doc(root, "CASE", 1)
    doc(root, "CLAIM", 1, "rests_on:\n- LIT-001\n- CASE-001\n")
    from luria.adr_index import load_scheme
    claim = next(iter(load_scheme(config.current().schemes["CLAIM"])))
    assert {(e.relation, e.target) for e in edges.outbound(claim)} == {
        ("rests_on", "LIT-001"), ("rests_on", "CASE-001")}
    assert relations.edges("CLAIM", "rests_on") == {
        "CLAIM-001": {"LIT-001", "CASE-001"}}


def test_a_converse_pair_is_declared_once_per_target_scheme(
        tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    pairs = relations.pairs()
    assert ("CLAIM", "rests_on", "supports", "LIT") in pairs
    assert ("CLAIM", "rests_on", "supports", "CASE") in pairs
    assert ("LIT", "supports", "rests_on", "CLAIM") in pairs
    assert ("CASE", "supports", "rests_on", "CLAIM") in pairs


def test_the_fixer_writes_the_converse_on_each_target(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    lit = doc(root, "LIT", 1)
    case = doc(root, "CASE", 1)
    doc(root, "CLAIM", 1, "rests_on:\n- LIT-001\n- CASE-001\n")
    relations.complete(fix=True)
    assert "supports:\n- CLAIM-001" in lit.read_text()
    assert "supports:\n- CLAIM-001" in case.read_text()


def test_the_fixer_completes_from_either_target_back(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CASE", 1, "supports:\n- CLAIM-001\n")
    claim = doc(root, "CLAIM", 1)
    relations.complete(fix=True)
    assert "rests_on:\n- CASE-001" in claim.read_text()


def test_the_far_side_sees_the_edge_before_the_fixer_runs(tmp_path,
                                                          monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT", 1)
    doc(root, "CASE", 2, "supports:\n- CLAIM-001\n")
    doc(root, "CLAIM", 1, "rests_on:\n- LIT-001\n")
    assert relations.edges("CLAIM", "rests_on") == {
        "CLAIM-001": {"LIT-001", "CASE-002"}}


def test_the_converse_must_exist_on_every_target(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(yaml.safe_dump(
        without("schemes.CASE.references")))
    config.reset()
    with pytest.raises(ValueError, match="'supports' is not a reference CASE"):
        config.current()


def test_a_multi_scheme_converse_must_include_the_declaring_scheme(
        tmp_path, monkeypatch):
    """The far field may itself name several schemes, but one of them has
    to be the scheme the pair started from."""
    project(tmp_path, monkeypatch, {"schemes": {"CASE": {"references": {
        "supports": {"scheme": ["LIT", "NOTE"]}}}}})
    with pytest.raises(ValueError, match="points back at CLAIM"):
        config.current()


def test_a_multi_scheme_converse_is_accepted(tmp_path, monkeypatch):
    """Both ends may name several schemes; every scheme either names holds
    the far field, by the one name the relation has."""
    project(tmp_path, monkeypatch, {"schemes": {
        "CASE": {"references": {"supports": {"scheme": ["CLAIM", "NOTE"]}}},
        "NOTE": {"references": {"rests_on": {
            "scheme": "CASE", "required": False, "many": True,
            "converse": "supports"}}}}})
    pairs = relations.pairs()
    assert ("CASE", "supports", "rests_on", "CLAIM") in pairs
    assert ("CASE", "supports", "rests_on", "NOTE") in pairs


def test_every_scheme_a_converse_names_must_hold_the_far_field(
        tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"schemes": {"CASE": {"references": {
        "supports": {"scheme": ["CLAIM", "NOTE"]}}}}})
    with pytest.raises(ValueError, match="'rests_on' is not a reference NOTE"):
        config.current()


# ── what may not cross ────────────────────────────────────────────────────

def test_a_chain_refuses_a_relation_that_can_leave_its_scheme(
        tmp_path, monkeypatch):
    """Naming the chain's own scheme among others does not make the
    relation a sequence within it."""
    project(tmp_path, monkeypatch, {
        "schemes": {"CLAIM": {"references": {"builds_on": {
            "scheme": ["CLAIM", "LIT"], "required": False, "many": True}}}},
        "chains": {"line": {"scheme": "CLAIM", "relation": "builds_on",
                            "output": "docs/lines.md"}}})
    with pytest.raises(ValueError, match="rather than CLAIM alone"):
        config.current()


def test_an_invariant_must_be_nameable_on_every_target(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {
        "schemes": {
            "CLAIM": {"references": {"rests_on": {"invariant": "topic"}},
                      "requires": ["topic"]},
            "LIT": {"requires": ["topic"]}}})
    with pytest.raises(ValueError, match="which CASE does not declare"):
        config.current()


# ── the other places a relation is written ────────────────────────────────

def test_relate_accepts_a_target_from_any_named_scheme(tmp_path, monkeypatch):
    from luria import relate
    root = project(tmp_path, monkeypatch)
    doc(root, "CASE", 1)
    claim = doc(root, "CLAIM", 1)
    relate.relate("CLAIM-001", "rests_on", "CASE-001")
    assert "CASE-001" in claim.read_text()


def test_relate_refuses_a_target_outside_the_union(tmp_path, monkeypatch):
    from luria import relate
    root = project(tmp_path, monkeypatch)
    doc(root, "NOTE", 1)
    doc(root, "CLAIM", 1)
    with pytest.raises(SystemExit, match="names a LIT or CASE document"):
        relate.relate("CLAIM-001", "rests_on", "NOTE-001")


def test_a_statement_may_name_any_scheme_in_the_union(tmp_path, monkeypatch):
    from luria import annotations
    root = project(tmp_path, monkeypatch)
    doc(root, "CASE", 1)
    doc(root, "NOTE", 1)
    doc(root, "CLAIM", 1, body="See CASE-001 <!-- ref::rests_on: CASE-001 -->"
                               " and NOTE-001 <!-- ref::rests_on: NOTE-001 -->")
    bad = annotations.survey().bad
    assert len(bad) == 1, bad
    assert "holds LIT or CASE codes, and NOTE-001 is not one" in bad[0]


def test_a_grouped_reference_has_a_page_per_target_in_every_scheme(
        tmp_path, monkeypatch):
    from luria import adr_index as builder
    root = project(tmp_path, monkeypatch, {"schemes": {"CLAIM": {
        "references": {"rests_on": {"group": True}}}}})
    doc(root, "LIT", 1)
    doc(root, "CASE", 1)
    doc(root, "CLAIM", 1, "rests_on:\n- CASE-001\n")
    pages = {p.relative_to(root).as_posix() for p in builder.outputs()}
    assert "docs/claims/rests_on/LIT-001.md" in pages, sorted(pages)
    assert "docs/claims/rests_on/CASE-001.md" in pages, sorted(pages)


# ── a symmetric relation that crosses schemes ─────────────────────────────

PEERS = {"schemes": {
    "CLAIM": {"references": {"peers": {
        "scheme": ["CLAIM", "LIT"], "required": False, "many": True,
        "converse": "peers"}}},
    "LIT": {"references": {"peers": {
        "scheme": "CLAIM", "required": False, "many": True,
        "converse": "peers"}}}}}


def test_a_symmetric_pair_held_on_both_sides_is_not_reported(
        tmp_path, monkeypatch):
    """A relation that is its own converse and crosses schemes names one
    field on each side. Reading both sides into one map keyed by field name
    let the far side's reading overwrite the near side's, so a pair held on
    both sides was reported as held on neither."""
    root = project(tmp_path, monkeypatch, PEERS)
    doc(root, "LIT", 1, "peers:\n- CLAIM-001\n")
    doc(root, "CLAIM", 1, "peers:\n- LIT-001\n")
    assert relations.rows() == []
    assert relations.completions() == []


def test_a_symmetric_pair_is_completed_across_schemes(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, PEERS)
    lit = doc(root, "LIT", 1)
    doc(root, "CLAIM", 1, "peers:\n- LIT-001\n")
    relations.complete(fix=True)
    assert "peers:\n- CLAIM-001" in lit.read_text()
    assert relations.rows() == []


def test_a_single_target_symmetric_crossing_pair_reads_both_sides(
        tmp_path, monkeypatch):
    """The same collision without a list: `compared_against` naming itself
    across two schemes, which was declarable before #160."""
    root = project(tmp_path, monkeypatch, {"schemes": {
        "CASE": {"references": {"compared_against": {
            "scheme": "NOTE", "required": False, "many": True,
            "converse": "compared_against"}}},
        "NOTE": {"references": {"compared_against": {
            "scheme": "CASE", "required": False, "many": True,
            "converse": "compared_against"}}}}})
    doc(root, "NOTE", 1, "compared_against:\n- CASE-001\n")
    doc(root, "CASE", 1, "compared_against:\n- NOTE-001\n")
    assert relations.rows() == []
