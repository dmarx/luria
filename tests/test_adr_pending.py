"""Undecided decisions, aged
([ADR-035](../record/decisions.d/ADR-035.md)).

Age is the whole point of this report, so the clock is injected: `--as-of` (and
the `today` argument these tests pass) keeps it from being a test that fails on
a Tuesday in November.
"""
import datetime as dt
import sys
from pathlib import Path

from _scheme import decision

from luria import adr_pending as pending

TODAY = dt.date(2026, 8, 3)


def row(number=1, status="Proposed", title="t", date=dt.date(2026, 1, 1),
        cites=0, unacknowledged=None):
    return pending.Pending(f"ADR-{number:03d}", number, status, title, date, cites,
                           cites if unacknowledged is None else unacknowledged,
                           Path(f"ADR-{number:03d}.md"))


def test_only_open_statuses_are_pending(project):
    """`Proposed` and `Deferred` are the two "not decided" states. `Rejected`
    and `Superseded` are decisions — they belong to the reference report."""
    for n, status in ((1, "Active"), (2, "Proposed"), (3, "Deferred"),
                      (4, "Rejected"), (5, "Superseded")):
        decision(project, n, status)
    assert {r.number for r in pending.pending()} == {2, 3}
    assert set(pending.UNDECIDED) == {"Proposed", "Deferred"}


def test_oldest_first_and_undated_last():
    rows = [row(1, date=dt.date(2026, 7, 1)), row(2, date=None),
            row(3, date=dt.date(2026, 1, 1))]
    ordered = sorted(rows, key=lambda r: (r.date is None, r.date, -r.cites))
    assert [r.number for r in ordered] == [3, 1, 2]


def test_age_and_staleness():
    r = row(date=dt.date(2026, 5, 5))
    assert r.age(TODAY) == 90
    assert r.is_stale(TODAY, 90) and not r.is_stale(TODAY, 91)


def test_undated_decision_is_reported_not_dropped():
    """A decision with no `date:` can't be aged — which is itself a finding, so
    it is listed with `?` rather than quietly skipped."""
    r = row(date=None)
    assert r.age(TODAY) is None and not r.is_stale(TODAY, 1)
    assert "?" in " ".join(pending.table([r], TODAY, 90))
    assert "1 undated" in pending.headline([r], TODAY, 90)


def test_headline_counts_are_real():
    rows = [row(1, date=dt.date(2025, 1, 1)), row(2, date=dt.date(2026, 8, 1))]
    line = pending.headline(rows, TODAY, 90)
    assert "2 undecided document(s)" in line
    assert f"oldest {(TODAY - dt.date(2025, 1, 1)).days} days" in line
    assert "1 over 90 days" in line


def test_empty_corpus_says_so():
    assert pending.headline([], TODAY, 90).endswith("every document is decided")
    assert pending.table([], TODAY, 90) == []


def test_citation_counts_come_from_the_reference_scan(project):
    """The second axis: an old proposal nothing cites is a stalled idea; one the
    codebase cites everywhere is a decision already made in code."""
    decision(project, 2, "Proposed")
    (project / "notes.md").write_text("we follow ADR-002 here\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()
    r, = pending.pending()
    assert r.cites == 1 and r.unacknowledged == 1


def test_headline_reconciles_with_the_reference_report(project):
    """Side by side the two counts read as an off-by-one. They are not: the
    reference report lists only decisions with an *unacknowledged* citation."""
    from luria import ref_status
    decision(project, 2, "Deferred")
    decision(project, 3, "Deferred")
    (project / "notes.md").write_text(
        "ADR-002 <!-- inactive-ok: ADR-002 — deliberate -->\nand ADR-003\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()

    rows = pending.pending()
    docs = ref_status.load_docs()
    flagged = ref_status.flagged(ref_status.scan(docs=docs), docs)
    loud = sum(1 for r in rows if r.unacknowledged)
    assert len(rows) == 2 and loud == len(flagged) == 1
    assert "1 with unacknowledged references" in pending.headline(rows, TODAY, 90)


def test_report_never_fails_the_build():
    assert pending.run(as_of=TODAY.isoformat()) is None


def test_every_scheme_is_covered(project):
    """A `Proposed` principle is an open question exactly as a decision is, and
    a report covering one scheme goes blind the day a second is configured
    (ADR-018)."""
    from _scheme import decision
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "docs/decisions"\n'
        '[luria.schemes.VP]\ndir = "docs/principles"\n'
        'render = "document"\noutput = "docs/values.md"\n')
    from luria import config
    config.reset()
    decision(project, 1, "Proposed", "An open decision")
    principles = project / "docs" / "principles"
    principles.mkdir(parents=True, exist_ok=True)
    (principles / "VP-002.md").write_text(
        "---\nstatus: Deferred\ntitle: 'An open value'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# VP-002: An open value\n")

    assert {r.code for r in pending.pending()} == {"ADR-001", "VP-002"}
