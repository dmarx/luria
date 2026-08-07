"""The status reports, rendered as committed views
([ADR-007](../record/decisions.d/ADR-007.md), #35).

These are the only place the status warnings are read in full, and nothing
consumes them programmatically — so what is worth pinning is that the numbers
in them agree with the checks they come from, and with each other. Two counts
that disagree without saying why is the bug that prompted them.

Since #35 they are views `luria index` commits, which adds two properties: a
report must be a **pure function of the record** (anything clock-derived goes
stale at midnight and fails the staleness check with no record change behind
it), and everything it names must be a **link** (the reader arrived from a
badge, not from a grep prompt).
"""
import datetime as dt
from pathlib import Path

from _scheme import decision

from luria import adr_pending, ref_status, reports

REPO = Path(__file__).resolve().parents[1]


def test_writes_both_reports(tmp_path):
    written = reports.write(tmp_path)
    assert [p.name for p in written] == ["pending-decisions.md",
                                         "reference-status.md"]
    assert all(p.read_text().startswith("# ") for p in written)


def test_generated_stamp_says_not_to_edit(tmp_path):
    for path in reports.write(tmp_path):
        assert "built, not edited" in path.read_text()


def test_reports_carry_no_clock(tmp_path):
    """A committed view regenerates identically tomorrow, or the staleness
    check fails every midnight (#35). Today's date appearing anywhere in the
    output is the failure mode this pins."""
    for path in reports.write(tmp_path):
        assert dt.date.today().isoformat() not in path.read_text()


def test_reference_report_links_every_site(project):
    """The console summary caps at five sites per document; the report is
    where the rest lives, so it must not cap — and each site is a link to the
    citing file (#35)."""
    decision(project, 12, "Superseded")
    (project / "notes.md").write_text(
        "\n".join(f"line {n} cites ADR-012" for n in range(1, 9)) + "\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()

    text = reports.reference_status()
    docs = ref_status.load_docs()
    for _, loud, _ in ref_status.flagged(ref_status.scan(docs=docs), docs):
        assert len(loud) == 8
        for site in loud:
            assert f"[`{site}`](../../notes.md)" in text


def test_reference_report_links_the_flagged_document(project):
    decision(project, 12, "Superseded")
    (project / "notes.md").write_text("cites ADR-012\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()

    text = reports.reference_status()
    from luria.config import current
    import os.path
    rel = os.path.relpath(current().schemes["ADR"].dir / "ADR-012.md",
                          current().reports)
    assert f"## [ADR-012]({rel}) — Superseded" in text


def test_reference_report_counts_match_the_scan():
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    rows = ref_status.flagged(result, docs)
    text = reports.reference_status()
    assert f"**{len(rows)} retired document(s) cited without acknowledgement.**" in text
    assert f"{ref_status.acknowledged_count(result, docs)} reference(s) carry" in text


def test_pending_report_links_every_row_to_its_decision(project):
    decision(project, 2, "Proposed")
    text = reports.pending_decisions()
    for r in adr_pending.pending():
        from luria.config import current
        assert f"[ADR-{r.number:03d}](../../{current().rel(r.path)})" in text


def test_pending_report_states_age_as_a_date(project):
    """"Open since 2026-01-01" is a fact about the record; "N days" is a fact
    about today, and a committed view can't carry one (#35)."""
    decision(project, 2, "Proposed")
    text = reports.pending_decisions()
    assert "| 2026-01-01 | Proposed |" in text
    assert "days" not in text


def test_the_two_reports_explain_why_their_counts_differ():
    """The bug that prompted the reports: one said 8 and the other 9, with
    nothing explaining that they measure different things."""
    text = reports.pending_decisions()
    assert "is not an off-by-one" in text
    assert "nothing cites it, or every citation carries an" in text


def test_outputs_land_in_the_configured_reports_dir():
    from luria.config import current
    assert set(reports.outputs()) == {
        current().reports / "reference-status.md",
        current().reports / "pending-decisions.md",
    }


def test_reports_are_deterministic():
    a = reports.reference_status(), reports.pending_decisions()
    b = reports.reference_status(), reports.pending_decisions()
    assert a == b
