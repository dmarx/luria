# tests/test_forbidden_when.py
"""A field forbidden while another field says something (#191).

The mirror of `required_when`: the same condition, the opposite sense. An
`Active` document naming what superseded it claimed to be in force and
replaced at once, and linted clean, because the record could demand a field
in a state but never forbid one.
"""

from __future__ import annotations

import pytest

from luria import config, contract
from test_required_when import project

REL = "record/practices.d/SOTA-001.md"

FORBID = """
schemes:
  SOTA:
    fields:
      promote_when:
        forbidden_when:
          status:
          - Active
"""


def check(meta: dict, known: dict | None = None) -> list[str]:
    scheme = config.current().schemes["SOTA"]
    meta = {"title": "A practice", "tags": ["record"], **meta}
    return contract.violations(contract.for_scheme(scheme), REL, meta,
                               known or {})


def test_the_field_in_a_forbidden_state_is_a_violation(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, FORBID)
    out = check({"status": "Active", "promote_when": "a replication"})
    assert len(out) == 1, out
    assert "promote_when" in out[0] and "`status: Active`" in out[0]


def test_the_finding_cites_the_declaration(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, FORBID)
    out = check({"status": "Active", "promote_when": "x"})
    assert "schemes.SOTA.fields.promote_when" in out[0], out


def test_the_field_outside_that_state_is_clean(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, FORBID)
    assert check({"status": "Proposed", "promote_when": "x"}) == []


def test_absent_in_the_forbidden_state_is_clean(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, FORBID)
    assert check({"status": "Active"}) == []


def test_a_status_note_does_not_defeat_the_condition(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, FORBID)
    out = check({"status": "Active — for now", "promote_when": "x"})
    assert any("promote_when" in o for o in out), out


def test_it_works_on_a_reference(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, """
            schemes:
              SOTA:
                references:
                  blocked_by:
                    scheme: LIT
                    required: false
                    forbidden_when:
                      status:
                      - Active
            """)
    out = check({"status": "Active", "blocked_by": "LIT-001"},
                {"LIT": {"LIT-001"}})
    assert len(out) == 1 and "blocked_by" in out[0], out


def test_it_works_on_a_vocabulary_field(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, """
            vocabularies:
              stages:
                early: {}
                late: {}
            schemes:
              SOTA:
                fields:
                  stage:
                    vocabulary: stages
                    forbidden_when:
                      status:
                      - Active
            """)
    out = check({"status": "Active", "stage": "early"})
    assert len(out) == 1 and "stage" in out[0], out
    assert check({"status": "Proposed", "stage": "early"}) == []


def test_it_composes_with_required_when(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, """
            schemes:
              SOTA:
                fields:
                  promote_when:
                    required_when: {status: [Proposed]}
                    forbidden_when: {status: [Active]}
            """)
    assert len(check({"status": "Proposed"})) == 1
    assert len(check({"status": "Active", "promote_when": "x"})) == 1
    assert check({"status": "Proposed", "promote_when": "x"}) == []
    assert check({"status": "Active"}) == []


# --- Contradictions and misspellings are config errors ---------------------

@pytest.mark.parametrize("spec, said", [
    ("required: true\n        forbidden_when: {status: [Active]}",
     "always required"),
    ("required_when: {status: [Active]}\n"
     "        forbidden_when: {status: [Active, Deferred]}",
     "both required and forbidden"),
    ("forbidden_when: {status: []}", "no values"),
    ("forbidden_when: {status: [Active], stage: [x]}", "one field"),
    ("forbidden_when: {staus: [Active]}", "not a field"),
    ("forbidden_when: {status: [active]}", "not a value"),
])
def test_a_rule_that_cannot_mean_what_it_says_is_refused(
        tmp_path, monkeypatch, spec, said):
    with pytest.raises(ValueError, match=said):
        project(tmp_path, monkeypatch, f"""
schemes:
  SOTA:
    fields:
      promote_when:
        {spec}
""")
        config.current()


def test_a_field_with_a_default_cannot_be_forbidden(tmp_path, monkeypatch):
    """A default is never absent, so the rule would fire on documents that
    never wrote the field."""
    with pytest.raises(ValueError, match="default"):
        project(tmp_path, monkeypatch, """
                vocabularies:
                  worlds:
                    A: {}
                    B: {}
                schemes:
                  SOTA:
                    fields:
                      worlds:
                        vocabulary: worlds
                        default: B
                        forbidden_when: {status: [Active]}
                """)
        config.current()


def test_the_contract_describes_the_rule(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, FORBID)
    lines = contract.describe(contract.for_scheme(
        config.current().schemes["SOTA"]))
    assert any("promote_when" in ln and "forbidden when `status` is `Active`"
               in ln for ln in lines), lines


# --- The built-in: an in-force document names no successor ------------------

def test_an_active_document_naming_a_successor_is_a_violation(
        tmp_path, monkeypatch):
    """#191's exact case, with no config at all."""
    project(tmp_path, monkeypatch, "")
    out = check({"status": "Active", "superseded_by": ["SOTA-002"]},
                {"SOTA": {"SOTA-002"}})
    assert len(out) == 1, out
    assert "superseded_by" in out[0] and "Active" in out[0]


def test_the_built_in_uses_the_schemes_own_active_word(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, """
            vocabularies:
              standing:
                Adopted: {}
                Proposed: {}
                Superseded: {}
            schemes:
              SOTA:
                active: Adopted
                fields:
                  status: {vocabulary: standing}
            """)
    out = check({"status": "Adopted", "superseded_by": ["SOTA-002"]},
                {"SOTA": {"SOTA-002"}})
    assert len(out) == 1 and "Adopted" in out[0], out


def test_other_states_may_name_a_successor(tmp_path, monkeypatch):
    """Only the in-force word is built in; the rest is the record's call."""
    project(tmp_path, monkeypatch, "")
    for status in ("Proposed", "Deferred", "Rejected"):
        assert check({"status": status, "superseded_by": ["SOTA-002"]},
                     {"SOTA": {"SOTA-002"}}) == [], status


def test_the_record_page_states_the_built_in_rule(tmp_path, monkeypatch):
    from luria import record_doc
    project(tmp_path, monkeypatch, "")
    section = record_doc.render().split("## What an entry must carry")[1]
    section = section.split("\n## ")[0]
    assert "forbidden" in section and "Active" in section, section


def test_a_defaulted_condition_field_is_named_by_its_default(
        tmp_path, monkeypatch):
    """The finding says what the rule read. An absent field with a default
    reads as the default, and printing the raw `None` would hide why."""
    project(tmp_path, monkeypatch, """
            vocabularies:
              worlds:
                A: {}
                B: {}
            schemes:
              SOTA:
                fields:
                  worlds:
                    vocabulary: worlds
                    default: B
                  promote_when:
                    forbidden_when: {worlds: [B]}
            """)
    out = check({"status": "Active", "promote_when": "x"})
    assert len(out) == 1 and "`worlds: B`" in out[0], out
