# tests/test_view_match.py
"""`match()` in a view: a path pattern's matches as rows of documents
(ADR-130, phase 2).

<!-- unresolved-ok-block: CLAIM-001 — fixture codes, not this record's -->
"""

from __future__ import annotations

from pathlib import Path

import pytest

from _config import merged
from luria import adr_index, config, views
from test_views import (BASE, CLAIM_1, CLAIM_2, VIEW, body_of, record,
                        render, write)

__all__ = ["record"]    # the fixture, re-exported for pytest


# --- match ------------------------------------------------------------------

CLAIM_3 = """---
status: Active
title: 'Exception is structural'
version: 1
tags:
- beta
date: '2026-01-03'
warrant: interpretive
rests_on:
- CLAIM-001
---

# CLAIM-003: Exception is structural

Body three.
"""


@pytest.fixture
def chain(record):
    """Three claims in a line: 003 rests on 001, which rests on 002."""
    write(record, "record/claims.d/CLAIM-003.md", CLAIM_3)
    adr_index.forget_documents()
    return record


def rows(root: Path, pattern: str, show: str) -> list[str]:
    text = render(root, "{% for r in match(\"" + pattern + "\") %}"
                        + show + "\n{% endfor %}")
    return [line for line in body_of(text).splitlines() if line]


def codes(text: str) -> str:
    """Rendered links back to bare codes, for readable assertions."""
    import re
    return re.sub(r"\[([A-Z]+-\d+)\]\([^)]*\)", r"\1", text)


def test_match_yields_a_row_per_match_keyed_by_node_name(chain):
    found = rows(chain, "(a:CLAIM)-[:rests_on]->(b:CLAIM)",
                 "{{ r.a.code }}>{{ r.b.code }}")
    assert [codes(r) for r in found] == ["CLAIM-001>CLAIM-002",
                                         "CLAIM-003>CLAIM-001"]


def test_a_row_holds_documents(chain):
    found = rows(chain, "(a:CLAIM)-[:rests_on]->(b:CLAIM {status: 'Proposed'})",
                 "{{ r.a.title }} rests on {{ r.b.title }}")
    assert found == ["Constraints bind conduct rests on Authority is separate"]


def test_an_anonymous_node_is_matched_and_not_shown(chain):
    found = rows(chain, "(a:CLAIM)-[:rests_on]->(:CLAIM)-[:rests_on]->(c:CLAIM)",
                 "{{ r | sort | join(',') }}:{{ r.a.code }}>{{ r.c.code }}")
    assert [codes(r) for r in found] == ["a,c:CLAIM-003>CLAIM-002"]


def test_variable_length_and_where_not(chain):
    found = rows(chain, "(a:CLAIM)-[:rests_on*1..]->(b:CLAIM) "
                        "WHERE NOT (b)-[:rests_on]->(:CLAIM)",
                 "{{ r.a.code }}>{{ r.b.code }}")
    assert [codes(r) for r in found] == ["CLAIM-001>CLAIM-002",
                                         "CLAIM-003>CLAIM-002"]


def test_a_single_node_pattern_filters_a_scheme(chain):
    found = rows(chain, "(c:CLAIM {status: 'Active'})", "{{ r.c.code }}")
    assert [codes(r) for r in found] == ["CLAIM-001", "CLAIM-003"]


def test_a_declared_pattern_is_matched_by_name(tmp_path, monkeypatch):
    write(tmp_path, "luria.yaml", merged(BASE, VIEW, """
patterns:
  grounded_in: (a:CLAIM)-[:rests_on]->(b:CLAIM)
"""))
    write(tmp_path, "record/claims.d/CLAIM-001.md", CLAIM_1)
    write(tmp_path, "record/claims.d/CLAIM-002.md", CLAIM_2)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    found = rows(tmp_path, "grounded_in", "{{ r.a.code }}>{{ r.b.code }}")
    assert [codes(r) for r in found] == ["CLAIM-001>CLAIM-002"]


@pytest.mark.parametrize("pattern, says", [
    ("(a:NOPE)", "NOPE is not a declared scheme"),
    ("(a:CLAIM)-[:nope]->(b:CLAIM)", "nope"),
    ("(a:CLAIM", "BOOT.md.j2:1"),
    ("(:CLAIM)", "names no node"),
])
def test_a_pattern_is_checked_as_a_declared_one_is(record, pattern, says):
    with pytest.raises(views.ViewError, match=says):
        rows(record, pattern, "{{ r }}")
