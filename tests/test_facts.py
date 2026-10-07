# tests/test_facts.py
"""The record as facts, and the clingo core that reasons over them."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from _config import merged

from luria import config, logic
from luria.facts import Fact, facts, program

CONFIG = """
issue_url: https://example.test/issues/{n}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    references:
      rests_on:
        scheme: [CLAIM, LIT]
        label: Rests on
        required: false
        many: true
        converse: supports
      supports:
        scheme: CLAIM
        required: false
        many: true
        converse: rests_on
  LIT:
    dir: record/literature.d
    output: docs/literature
    references:
      supports:
        scheme: CLAIM
        required: false
        many: true
        converse: rests_on
chains:
  argument:
    scheme: CLAIM
    relation: supports
    output: docs/argument.md
"""


def project(tmp_path, monkeypatch) -> Path:
    for d in ("claims.d", "literature.d"):
        (tmp_path / "record" / d).mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "luria.yaml").write_text(merged(CONFIG))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, code: str, front: str = "") -> None:
    d = "claims.d" if code.startswith("CLAIM") else "literature.d"
    (root / "record" / d / f"{code}.md").write_text(
        f"---\nstatus: Active\ntitle: '{code}'\ntags:\n- record\n"
        f"date: '2026-01-01'\n{front}---\n\n# {code}: {code}\n\nBody.\n")


def by(found: list[Fact], predicate: str) -> set[tuple]:
    return {f.args for f in found if f.predicate == predicate}


# ── the schema ────────────────────────────────────────────────────────────

def test_the_schema_is_facts(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    found = facts()
    assert {("CLAIM",), ("LIT",)} <= by(found, "scheme")
    assert ("CLAIM", "Active") in by(found, "active")
    assert by(found, "ref_target") >= {("CLAIM", "rests_on", "CLAIM"),
                                       ("CLAIM", "rests_on", "LIT")}
    assert ("CLAIM", "rests_on", "supports") in by(found, "ref_converse")
    assert ("CLAIM", "rests_on", "Rests on") in by(found, "ref_label")
    assert ("CLAIM", "rests_on") in by(found, "ref_many")
    assert ("argument", "CLAIM") in by(found, "chain")
    assert ("argument", "supports", 0) in by(found, "chain_relation")


# ── the documents ─────────────────────────────────────────────────────────

def test_documents_and_their_values_are_facts(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT-001")
    doc(root, "CLAIM-001", "rests_on:\n- LIT-001\n- CLAIM-009\n")
    found = facts()
    assert ("CLAIM-001", "CLAIM") in by(found, "doc")
    assert ("CLAIM-001", "Active") in by(found, "status")
    assert ("CLAIM-001", "tags", 0, "record") in by(found, "value")
    # A code that lands nowhere is still a fact: whether it lands is the
    # rules' business.
    assert {("CLAIM-001", "rests_on", "LIT-001"),
            ("CLAIM-001", "rests_on", "CLAIM-009")} <= by(found, "ref_value")
    # The typed graph is `edges.graph`'s, which keeps a code of a declared
    # scheme whether or not it resolves; `doc/2` says which do.
    assert ("CLAIM-001", "rests_on", "LIT-001") in by(found, "edge")
    assert ("CLAIM-009", "CLAIM") not in by(found, "doc")


def test_a_temporary_document_is_a_fact(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM-tmpab12c")
    assert ("CLAIM-tmpab12c", "CLAIM") in by(facts(), "doc")


def test_strings_survive_the_text_form(tmp_path, monkeypatch):
    """Quotes, backslashes and newlines are escaped, not lost."""
    tricky = Fact("value", ("X-1", "summary", 0, 'a "quoted"\\path\nline'))
    out = logic.solve(["#show value/4."], [tricky])
    assert out["value"] == {tricky.args}


def test_the_facts_are_sorted_and_unique(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT-001")
    found = facts()
    assert found == sorted(set(found))


def test_luria_facts_prints_a_program_clingo_reads(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT-001")
    doc(root, "CLAIM-001", "rests_on:\n- LIT-001\n")
    out = subprocess.run([sys.executable, "-m", "luria.cli", "facts", "doc",
                          "edge"], cwd=root, capture_output=True, text=True,
                         check=True).stdout
    assert 'doc("CLAIM-001","CLAIM").' in out.replace(", ", ",")
    assert all(line.startswith(("doc(", "edge(")) for line in out.splitlines())
    reread = logic.solve([out, "#show doc/2. #show edge/3."], [])
    assert ("CLAIM-001", "rests_on", "LIT-001") in reread["edge"]


# ── the engine ────────────────────────────────────────────────────────────

def test_rules_derive_over_the_record(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "CLAIM-001")
    doc(root, "CLAIM-002", "rests_on:\n- CLAIM-001\n")
    doc(root, "CLAIM-003", "rests_on:\n- CLAIM-002\n")
    out = logic.solve(["""
        depends(C, P) :- edge(C, "rests_on", P).
        depends(C, P) :- depends(C, Q), edge(Q, "rests_on", P).
        #show depends/2.
    """], facts())
    assert ("CLAIM-003", "CLAIM-001") in out["depends"]


def test_a_program_with_several_answers_is_refused():
    with pytest.raises(logic.LogicError, match="exactly one answer set"):
        logic.solve(["{ a; b }. #show a/0. #show b/0."], [])


def test_a_program_with_no_answer_is_refused():
    with pytest.raises(logic.LogicError, match="has none"):
        logic.solve([":- not a. #show a/0."], [])


# ── the ported programs ───────────────────────────────────────────────────

def test_a_relation_is_held_from_either_side(tmp_path, monkeypatch):
    """`relations.lp` unions a field with its converse, so a one-sided
    declaration reads the same as a completed one."""
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT-001", "supports:\n- CLAIM-001\n")
    doc(root, "CLAIM-001")
    held = logic.derive("relations")["held"]
    assert ("LIT", "supports", "LIT-001", "CLAIM-001") in held
    assert ("CLAIM", "rests_on", "CLAIM-001", "LIT-001") in held


def test_a_value_is_held_as_a_set_member(tmp_path, monkeypatch):
    """`holds/3` is `members`: a scalar is a set of one, stripped."""
    root = project(tmp_path, monkeypatch)
    doc(root, "LIT-001", "area: ' runtime '\n")
    assert ("LIT-001", "area", "runtime") in by(facts(), "holds")
    assert ("LIT-001", "tags", "record") in by(facts(), "holds")
