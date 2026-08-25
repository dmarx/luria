"""The README's two counts, derived from the record (ADR-018).

A badge is a claim on the front page of the repository, which is the last place
a wrong number should be able to sit unnoticed. These cover the two things that
make it trustworthy: the counts come from frontmatter rather than from a human,
and a stale region is a lint failure rather than a quiet disagreement.
"""
import sys
from pathlib import Path

from _scheme import decision

from luria import badges, config

REPO = Path(__file__).resolve().parents[1]

TWO_SCHEMES = (
    '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
    '[luria.schemes.ADR]\ndir = "docs/decisions"\n'
    '[luria.schemes.VP]\ndir = "docs/values"\n'
    'render = "document"\noutput = "docs/values.md"\n'
)


def principle(root: Path, number: int, status: str, title: str = "A value") -> Path:
    path = root / "docs" / "values" / f"VP-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstatus: {status}\ntitle: {title!r}\ntags:\n- record\n"
                    f"date: '2026-01-01'\n---\n\n# VP-{number:03d}: {title}\n")
    return path


def with_schemes(project) -> None:
    (project / "luria.toml").write_text(TWO_SCHEMES)
    config.reset()


# ── The counts ───────────────────────────────────────────────────────────


def test_a_settled_record_counts_zero(project):
    with_schemes(project)
    decision(project, 1, "Active")
    assert badges.counts() == (0, 0)


def test_proposed_and_deferred_both_need_a_decision(project):
    """Two statuses, one question: "we haven't decided" and "we decided not to
    decide yet" are both open (ADR-003)."""
    with_schemes(project)
    decision(project, 1, "Proposed")
    decision(project, 2, "Deferred")
    decision(project, 3, "Active")
    assert badges.counts()[0] == 2


def test_every_scheme_is_counted(project):
    """"All reachable schemes" is the point: a `Proposed` principle is an open
    question exactly as a decision is."""
    with_schemes(project)
    decision(project, 1, "Proposed")
    principle(project, 2, "Deferred")
    assert badges.counts()[0] == 2


def test_a_retired_document_counts_only_while_cited(project):
    """The number is *cited* but retired. A superseded decision nothing points
    at is history, not a problem."""
    with_schemes(project)
    decision(project, 1, "Superseded")
    decision(project, 2, "Active")
    assert badges.counts()[1] == 0

    (project / "docs" / "notes.md").write_text("per ADR-001 we do this\n")
    assert badges.counts()[1] == 1


def test_an_acknowledged_citation_does_not_count(project):
    """Citing a retired decision is often right, and the whole point of the
    acknowledgement is that the considered ones stop being noise (ADR-035)."""
    with_schemes(project)
    decision(project, 1, "Superseded")
    (project / "docs" / "notes.md").write_text(
        "<!-- inactive-ok: ADR-001 — deliberate -->\nper ADR-001 we do this\n")
    assert badges.counts()[1] == 0


# ── Rendering and staleness ──────────────────────────────────────────────


def test_zero_is_green_and_nonzero_is_amber(project):
    """Neither number is a failure, so neither goes red — "look at this", not
    "you broke it"."""
    assert badges.GOOD in badges.badge("needs decision", 0, "x.md")
    assert badges.ATTENTION in badges.badge("needs decision", 3, "x.md")


def test_rewrite_replaces_only_the_region(project):
    with_schemes(project)
    decision(project, 1, "Active")
    text = f"# Title\n\n{badges.OPEN}\nstale junk\n{badges.CLOSE}\n\nProse.\n"
    out = badges.rewrite(text)
    assert out.startswith("# Title") and out.endswith("Prose.\n")
    assert "stale junk" not in out and "needs%20decision-0" in out


def test_a_project_without_a_region_is_left_alone(project):
    """Not everyone wants badges, and a tool that edits a README nobody asked
    it to edit is a tool people stop running."""
    with_schemes(project)
    decision(project, 1, "Active")
    assert badges.rewrite("# Title\n\nNo region here.\n") == \
        "# Title\n\nNo region here.\n"


def test_rewriting_twice_changes_nothing(project):
    """Idempotence is what makes the staleness check meaningful — otherwise
    every run would report the previous run's output as stale."""
    with_schemes(project)
    decision(project, 1, "Proposed")
    once = badges.rewrite(f"{badges.OPEN}\n{badges.CLOSE}\n")
    assert badges.rewrite(once) == once
