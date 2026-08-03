"""The markdown reports that CI uploads
([ADR-007](../docs/decisions/ADR-007.md)).

These are the only place the status warnings are read in full, and nothing
consumes them programmatically — so what is worth pinning is that the numbers in
them agree with the checks they come from, and with each other. Two counts that
disagree without saying why is the bug that prompted them.
"""
import datetime as dt
from pathlib import Path

from _scheme import decision

from luria import adr_pending, ref_status, reports

REPO = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 8, 3)


def test_writes_both_reports(tmp_path):
    written = reports.write(tmp_path, TODAY, 90)
    assert [p.name for p in written] == ["pending-decisions.md",
                                         "reference-status.md"]
    assert all(p.read_text().startswith("# ") for p in written)


def test_generated_stamp_says_not_to_edit(tmp_path):
    for path in reports.write(tmp_path, TODAY, 90):
        assert "built, not edited" in path.read_text()


def test_reference_report_lists_every_site(project):
    """The console summary caps at five sites per document; the artifact is
    where the rest lives, so it must not cap."""
    decision(project, 12, "Superseded")
    (project / "notes.md").write_text(
        "\n".join(f"line {n} cites ADR-012" for n in range(1, 9)) + "\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()

    text = reports.reference_status(TODAY)
    docs = ref_status.load_docs()
    for _, loud, _ in ref_status.flagged(ref_status.scan(docs=docs), docs):
        assert len(loud) == 8
        for site in loud:
            assert f"`{site}`" in text


def test_reference_report_counts_match_the_scan():
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    rows = ref_status.flagged(result, docs)
    text = reports.reference_status(TODAY)
    assert f"**{len(rows)} retired document(s) cited without acknowledgement.**" in text
    assert f"{ref_status.acknowledged_count(result, docs)} reference(s) carry" in text


def test_pending_report_links_every_row_to_its_decision(project):
    decision(project, 2, "Proposed")
    text = reports.pending_decisions(TODAY, 90)
    for r in adr_pending.pending():
        from luria.config import current
        assert f"[ADR-{r.number:03d}](../../{current().rel(r.path)})" in text


def test_the_two_reports_explain_why_their_counts_differ():
    """The bug that prompted the artifacts: one report said 8 and the other 9,
    with nothing explaining that they measure different things."""
    text = reports.pending_decisions(TODAY, 90)
    assert "is not an off-by-one" in text
    assert "nothing cites it, or every citation carries an" in text


def test_reports_are_deterministic_for_a_fixed_clock():
    a = reports.reference_status(TODAY), reports.pending_decisions(TODAY, 90)
    b = reports.reference_status(TODAY), reports.pending_decisions(TODAY, 90)
    assert a == b
