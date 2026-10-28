# tests/test_reliance.py
"""What rests on an undecided document, and acknowledgements that never
come due.

The case that motivated it (the nucleation record's decision 57): a record of a thousand
undecided documents whose pending report ranked by age and citation count, so
the claims forty others rested on sorted beside stalled ideas — and four
claims leaning on Superseded terms whose `inactive-ok-file` directives
silenced, forever, the question of whether they still held. Each class is
fired once on a fixture with that shape (DP-6).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from _config import merged
from luria import adr_pending, config, lint, reliance, reports

BASE = """
issue_url: https://example.test/issues/{n}
schemes:
  CLAIM:
    dir: record/claims.d
    output: docs/claims
    references:
      rests_on: {scheme: CLAIM, many: true, required: false,
                 converse: supports}
      supports: {scheme: CLAIM, many: true, required: false,
                 converse: rests_on}
      uses: {scheme: TERM, many: true, required: false}
      see_also: {scheme: CLAIM, many: true, required: false}
  TERM:
    dir: record/terms.d
    output: docs/terms
    retires_on: Superseded
    successor: superseded_by
    references:
      superseded_by: {scheme: TERM, many: true, required: false}
"""

RELIANCE = {"reliance": ["rests_on", "uses"]}
FOLDERS = {"CLAIM": "claims.d", "TERM": "terms.d"}


def project(tmp_path: Path, monkeypatch, *extra) -> Path:
    (tmp_path / "luria.yaml").write_text(merged(BASE, *extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, scheme: str, number: int, status: str, body: str = "",
        date: str = "2026-01-01", **fields) -> Path:
    code = f"{scheme}-{number:03d}"
    front = ["---", f"status: {status}", f"title: 'Doc {number}'",
             f"date: '{date}'"]
    for key, value in fields.items():
        front.append(f"{key}:")
        front += [f"- {v}" for v in value]
    front += ["---", "", f"# {code}: Doc {number}", "", body or "Body."]
    path = root / "record" / FOLDERS[scheme] / f"{code}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(front) + "\n")
    return path


def tower(root: Path) -> None:
    """CLAIM-001 (Proposed, newest) has three transitive dependents:
    2 rests on 1, 3 rests on 2, and 4 states on the converse side that 1
    supports it. CLAIM-005 (Proposed, oldest) has none; `see_also` is not a
    dependence field, so CLAIM-006 pointing at it counts for nothing."""
    doc(root, "CLAIM", 1, "Proposed", date="2026-06-01", supports=["CLAIM-004"])
    doc(root, "CLAIM", 2, "Active", rests_on=["CLAIM-001"])
    doc(root, "CLAIM", 3, "Active", rests_on=["CLAIM-002"])
    doc(root, "CLAIM", 4, "Active")
    doc(root, "CLAIM", 5, "Proposed", date="2025-01-01")
    doc(root, "CLAIM", 6, "Active", see_also=["CLAIM-005"])


# ── dependents ─────────────────────────────────────────────────────────────

def test_dependents_are_transitive_distinct_and_read_from_either_side(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    tower(root)
    assert reliance.dependents() == {"CLAIM-001": 3, "CLAIM-002": 1}


def test_a_cycle_does_not_count_a_document_as_its_own_dependent(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    doc(root, "CLAIM", 1, "Proposed", rests_on=["CLAIM-002"])
    doc(root, "CLAIM", 2, "Proposed", rests_on=["CLAIM-001"])
    assert reliance.dependents() == {"CLAIM-001": 1, "CLAIM-002": 1}


def test_unset_reliance_counts_nothing_and_keeps_the_old_order(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    tower(root)
    assert reliance.dependents() == {}
    rows = adr_pending.pending()
    assert [r.code for r in rows] == ["CLAIM-005", "CLAIM-001"]
    assert all(r.dependents is None for r in rows)
    table = adr_pending.table(rows, dt.date(2026, 8, 1), 90)
    assert "relied" not in table[0]
    assert "Relied on" not in reports.pending_decisions()


# ── the pending report ─────────────────────────────────────────────────────

def test_the_pending_report_ranks_by_dependents(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    tower(root)
    rows = adr_pending.pending()
    assert [(r.code, r.dependents) for r in rows] == [("CLAIM-001", 3),
                                                      ("CLAIM-005", 0)]
    table = adr_pending.table(rows, dt.date(2026, 8, 1), 90)
    assert "relied" in table[0]
    assert "CLAIM-001       3" in table[1]
    assert "most relied on CLAIM-001 (3 dependent(s))" in adr_pending.headline(
        rows, dt.date(2026, 8, 1), 90)
    page = reports.pending_decisions()
    assert "| Relied on |" in page
    assert "CLAIM-001.md) | 3 |" in page
    assert "`rests_on`, `uses`" in page


def test_age_breaks_a_tie_in_dependents(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    doc(root, "CLAIM", 1, "Proposed", date="2026-06-01")
    doc(root, "CLAIM", 2, "Proposed", date="2026-01-01")
    doc(root, "CLAIM", 3, "Active", rests_on=["CLAIM-001", "CLAIM-002"])
    assert [r.code for r in adr_pending.pending()] == ["CLAIM-002", "CLAIM-001"]


# ── load-bearing ───────────────────────────────────────────────────────────

def test_load_bearing_names_undecided_documents_past_the_threshold(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE, {"load_bearing": 2})
    tower(root)
    _, headline, rows = next(s for s in lint.status_sections()
                             if s[0] == "load-bearing")
    assert rows == ["record/claims.d/CLAIM-001.md: CLAIM-001 (Proposed) has 3 "
                    "transitive dependent(s) — at least 2, so decide it or "
                    "say what holds it back"]
    assert "at least 2 transitive dependents" in headline


def test_load_bearing_skips_decided_documents(tmp_path, monkeypatch):
    """CLAIM-002 has a dependent, but it is Active: decided, not pending."""
    root = project(tmp_path, monkeypatch, RELIANCE, {"load_bearing": 1})
    tower(root)
    assert [r.split(":")[1].strip().split()[0]
            for r in reliance.load_bearing_rows()] == ["CLAIM-001"]


def test_load_bearing_is_gateable(tmp_path, monkeypatch, capsys):
    root = project(tmp_path, monkeypatch, RELIANCE,
                   {"load_bearing": 3, "lint": {"fail_on": ["load-bearing"]}})
    tower(root)
    errors: list[str] = []
    lint.report_warnings(errors)
    assert any("failing: `fail_on` names 'load-bearing'" in e for e in errors)


def test_unset_load_bearing_never_fires(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    tower(root)
    assert "load-bearing" not in {n for n, _, _ in lint.status_sections()}


# ── configuration ──────────────────────────────────────────────────────────

def test_reliance_names_declared_reference_fields(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"reliance": ["rests_on", "presupposes"]})
    with pytest.raises(ValueError, match="presupposes is no reference field"):
        config.current()


def test_load_bearing_without_reliance_is_refused(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, {"load_bearing": 5})
    with pytest.raises(ValueError, match="`reliance` names no field"):
        config.current()


@pytest.mark.parametrize("value", [0, -1, "five", True])
def test_load_bearing_is_a_positive_count(tmp_path, monkeypatch, value):
    project(tmp_path, monkeypatch, RELIANCE, {"load_bearing": value})
    with pytest.raises(ValueError, match="positive whole number"):
        config.current()


# ── unbounded acknowledgements ─────────────────────────────────────────────

ACK_FILE = "<!-- inactive-ok-file: TERM-001 — the definition current then -->"


def retired_term(root: Path, ack: str) -> Path:
    doc(root, "TERM", 1, "Superseded", superseded_by=["TERM-002"])
    doc(root, "TERM", 2, "Active")
    return doc(root, "CLAIM", 1, "Active", ack + "\n\nBody.",
               uses=["TERM-001"])


def unbounded() -> list[str]:
    return next((rows for name, _, rows in lint.status_sections()
                 if name == "unbounded-acknowledgements"), [])


def test_an_acknowledged_retired_premise_without_until_is_named(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    retired_term(root, ACK_FILE)
    rows = unbounded()
    assert len(rows) == 1, rows
    assert rows[0].startswith("record/claims.d/CLAIM-001.md:")
    assert ("`inactive-ok-file: TERM-001` excuses a Superseded document "
            "CLAIM-001 depends on (`uses`)" in rows[0])


def test_an_until_bounds_it(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, RELIANCE)
    retired_term(root, "<!-- inactive-ok-file: TERM-001 until 2999-01-01 — "
                       "revisit against TERM-002 -->")
    assert unbounded() == []


def test_a_field_outside_reliance_is_not_a_dependence(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, {"reliance": ["rests_on"]})
    retired_term(root, ACK_FILE)
    assert unbounded() == []


def test_without_reliance_the_class_never_fires(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    retired_term(root, ACK_FILE)
    assert unbounded() == []


def test_an_undecided_premise_is_the_pending_reports_business(
        tmp_path, monkeypatch):
    """`Proposed` is out of force but not retired; acknowledging it is not
    leaning on something gone."""
    root = project(tmp_path, monkeypatch, RELIANCE)
    doc(root, "CLAIM", 2, "Proposed")
    doc(root, "CLAIM", 1, "Active",
        "<!-- inactive-ok-file: CLAIM-002 — a draft we lean on -->\n",
        rests_on=["CLAIM-002"])
    assert unbounded() == []
