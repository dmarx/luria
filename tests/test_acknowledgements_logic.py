# tests/test_acknowledgements_logic.py
"""`luria/logic/acknowledgements.lp` on hand-built facts: who answers for a
citation, and which annotations answer for nothing."""

from __future__ import annotations

from luria import logic
from luria.facts import Fact


def run(*facts: tuple) -> dict:
    return logic.derive("acknowledgements",
                        found=[Fact(p, args) for p, *rest in facts
                               for args in [tuple(rest)]])


def test_the_kind_that_claims_the_state_wins_over_a_mention():
    out = run(("site", 0, "a.md", 3, "ADR-001"), ("resolves", "ADR-001"),
              ("ann", 0, "a.md", "mention-ok"), ("ann_code", 0, "ADR-001"),
              ("ann_line", 0, 3),
              ("ann", 1, "a.md", "inactive-ok"), ("ann_code", 1, "ADR-001"),
              ("ann_line", 1, 3))
    assert out["excused"] == {(0, 1)}
    assert out["unused"] == {(0,)}


def test_a_document_in_force_is_answered_only_by_a_mention():
    out = run(("site", 0, "a.md", 3, "ADR-001"), ("resolves", "ADR-001"),
              ("active", "ADR-001"),
              ("ann", 0, "a.md", "inactive-ok"), ("ann_code", 0, "ADR-001"),
              ("ann_file", 0))
    assert "excused" not in out
    assert out["unused"] == {(0,)}


def test_the_first_annotation_in_the_file_answers():
    out = run(("site", 0, "a.md", 5, "ADR-404"),
              ("ann", 2, "a.md", "unresolved-ok"), ("ann_code", 2, "ADR-404"),
              ("ann_file", 2),
              ("ann", 7, "a.md", "unresolved-ok"), ("ann_code", 7, "ADR-404"),
              ("ann_line", 7, 5))
    assert out["excused"] == {(0, 2)}


def test_a_malformed_annotation_loses_what_it_would_have_excused():
    out = run(("site", 0, "a.md", 3, "ADR-001"), ("resolves", "ADR-001"),
              ("site", 1, "a.md", 3, "ADR-002"), ("resolves", "ADR-002"),
              ("active", "ADR-002"),
              ("ann", 0, "a.md", "inactive-ok"), ("ann_problem", 0),
              ("ann_code", 0, "ADR-001"), ("ann_code", 0, "ADR-002"),
              ("ann_line", 0, 3))
    # ADR-002 is in force, so losing an excuse for it costs nothing.
    assert out["lost"] == {(0, "ADR-001", 0)}
    assert "unused" not in out
