"""The pending-decisions report, grouped by scheme (#230).

`adr_pending.pending()` deliberately spans every scheme — "a report that
covered one scheme would go quietly blind the day a project configured a
second". Collecting them together is right; rendering them in one table is
not. A `Proposed` decision and a `Proposed` practice are open questions for
different readers, and an anthology's report intermixed ADRs and SOTAs.

So this is a rendering change and nothing else. The badge and the lint
headline read `pending()`, never the rendered file, and these tests pin that
the counts they publish do not move.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_pending, badges, config, reports


# The fixture's schemes are deliberately RFC/SPEC/LIT rather than the one this
# record declares for itself. A suite that writes a real decision's code down
# as a specimen is read by the reference scanner as citing it (#231) — and the
# number this test first used names a Superseded decision, so it earned a
# retired-citation warning and would have wanted a fourth `unlinted-file:`
# beside the three that issue is already about. A prefix this record does not
# declare is invisible to the scanner and needs no directive.
#
# The first draft of this comment spelled that code out and re-earned the
# warning, which is the same lesson twice: the mitigation is not writing it.


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


STATUSES = ("Active:\n  blurb: in force\nProposed:\n  blurb: not yet\n"
            "Deferred:\n  blurb: parked\nSuperseded:\n  blurb: replaced\n"
            "Rejected:\n  blurb: declined\n")


def project(tmp_path, monkeypatch, schemes=("RFC", "SPEC")) -> Path:
    """A record with one or two schemes, declared in the order given."""
    tables = "\n".join(f"""
[luria.schemes.{p}]
dir = "record/{p.lower()}.d"
output = "docs/{p.lower()}"
""" for p in schemes)
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"
{tables}
""")
    for p in schemes:
        write(tmp_path, f"record/{p.lower()}.d/statuses.yaml", STATUSES)
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def doc(root: Path, prefix: str, number: int, status: str = "Proposed",
        date: str = "2026-01-01") -> Path:
    return write(root, f"record/{prefix.lower()}.d/{prefix}-{number:03d}.md",
                 f"---\nstatus: {status}\ntitle: '{prefix} {number}'\n"
                 f"date: '{date}'\n---\n\n# {prefix}-{number:03d}: {prefix} {number}\n")


# --- the grouping ------------------------------------------------------------

def test_two_schemes_render_as_separate_sections(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "RFC", 1)
    doc(root, "SPEC", 1)
    text = reports.pending_decisions(root / "docs")
    assert "## RFCs" in text
    assert "## SPECs" in text


def test_a_row_sits_under_its_own_scheme(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "RFC", 7)
    doc(root, "SPEC", 9)
    text = reports.pending_decisions(root / "docs")
    adr, sota = text.index("## RFCs"), text.index("## SPECs")
    assert adr < text.index("RFC-007") < sota
    assert sota < text.index("SPEC-009")


def test_section_order_follows_the_config_not_the_alphabet(tmp_path, monkeypatch):
    """`pending()` walks `current().schemes`, which is declaration order. A
    project decides which of its families a reader meets first, the same way
    `tags.yaml` decides the order of topics."""
    root = project(tmp_path, monkeypatch, schemes=("SPEC", "RFC"))
    doc(root, "RFC", 1)
    doc(root, "SPEC", 1)
    text = reports.pending_decisions(root / "docs")
    assert text.index("## SPECs") < text.index("## RFCs")


def test_a_scheme_with_nothing_pending_gets_no_section(tmp_path, monkeypatch):
    """Three declared schemes, two with an open question. The third is not an
    empty heading — a section per declared scheme would report absence as a
    row of nothing."""
    root = project(tmp_path, monkeypatch, schemes=("RFC", "SPEC", "LIT"))
    doc(root, "RFC", 1)
    doc(root, "SPEC", 1)
    doc(root, "LIT", 2, status="Active")
    text = reports.pending_decisions(root / "docs")
    assert "## RFCs" in text and "## SPECs" in text
    assert "## LITs" not in text


def test_one_scheme_stays_flat(tmp_path, monkeypatch):
    """A single-scheme record gains nothing from a heading naming the only
    family it has, and luria's own record is one of those."""
    root = project(tmp_path, monkeypatch, schemes=("RFC",))
    doc(root, "RFC", 1)
    doc(root, "RFC", 2)
    text = reports.pending_decisions(root / "docs")
    assert "## RFCs" not in text
    assert "RFC-001" in text and "RFC-002" in text


def test_rows_stay_oldest_first_within_a_section(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "SPEC", 1, date="2026-03-01")
    doc(root, "SPEC", 2, date="2026-01-01")
    doc(root, "RFC", 1)
    text = reports.pending_decisions(root / "docs")
    assert text.index("SPEC-002") < text.index("SPEC-001")


# --- what must not move ------------------------------------------------------

def test_the_headline_still_counts_every_scheme(tmp_path, monkeypatch):
    """The total is what the badge publishes, and it is a fact about the
    record rather than about any one family."""
    root = project(tmp_path, monkeypatch)
    doc(root, "RFC", 1)
    doc(root, "SPEC", 1)
    doc(root, "SPEC", 2)
    text = reports.pending_decisions(root / "docs")
    assert "**3 document(s) awaiting a decision.**" in text


def test_the_badge_count_is_unchanged_by_the_grouping(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    doc(root, "RFC", 1)
    doc(root, "SPEC", 1)
    assert badges.counts()[0] == len(adr_pending.pending()) == 2


def test_every_code_is_still_a_link(tmp_path, monkeypatch):
    """The reader arrived from a badge, not a grep prompt — the report's own
    standing rule."""
    root = project(tmp_path, monkeypatch)
    doc(root, "RFC", 1)
    doc(root, "SPEC", 1)
    text = reports.pending_decisions(root / "docs")
    assert "[RFC-001](" in text and "[SPEC-001](" in text
