"""`luria repair` trims an `inactive-ok` code whose document is now in force.

An `inactive-ok:` claims that a code it names is retired. When that document
goes Active the claim is false and the code excuses nothing — `luria ack`
refuses to write one over a document in force for exactly that reason, and
the lint reports it. Removing the code is the one correct answer, so it is a
repair: the reason stays, the other codes stay, and a directive is deleted
only when it names nothing else.

The case that asked for it: Nucleation promoted 53 readings in one pass and
cleared the fallout with a throwaway script — 47 directive lines in 46 files.

What it never does is judge. A retired code that nothing in scope cites any
more may want the directive moved rather than deleted, and `unresolved-ok`,
`mention-ok`, `target-ok` and `url-ok` claim other things entirely.
"""
# unresolved-ok-file: ADR-777 — a fixture code that names no document on purpose
from pathlib import Path

from _config import merged
from _scheme import decision

from luria import ack, lint, ref_status, repair
from luria.config import current


def page(project, body: str, name: str = "docs/notes.md") -> Path:
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


def stale() -> list[str]:
    ref_status.forget_scan()
    return ref_status.stale_annotations()


# ── What it removes ──────────────────────────────────────────────────────


def test_an_active_code_leaves_the_directive_and_the_reason_stays(project):
    decision(project, 1, "Active")
    decision(project, 2, "Proposed")
    path = page(project,
                "<!-- inactive-ok-file: ADR-001 ADR-002 — Proposed; named, "
                "not leaned on -->\n\nSee `ADR-001` and `ADR-002`.\n")
    assert path in repair.apply()
    assert path.read_text().splitlines()[0] == \
        "<!-- inactive-ok-file: ADR-002 — Proposed; named, not leaned on -->"


def test_a_directive_left_naming_nothing_is_deleted(project):
    decision(project, 1, "Active")
    path = page(project,
                "# Notes\n\n<!-- inactive-ok: ADR-001 — Proposed for now -->\n"
                "Leaning on `ADR-001`.\n")
    repair.apply()
    assert path.read_text() == "# Notes\n\nLeaning on `ADR-001`.\n"


def test_a_used_directive_still_loses_its_active_code(project):
    """The annotation as a whole still answers for ADR-002, so it was never
    "no longer applies" — but ADR-001 in it vouches for a retirement that is
    over. The lint names it, so the repair and the report agree on what
    counts."""
    decision(project, 1, "Active")
    decision(project, 2, "Superseded")
    path = page(project,
                "<!-- inactive-ok: ADR-001 ADR-002 — both retired -->\n"
                "`ADR-001` and `ADR-002`.\n")
    assert any("ADR-001" in s and "Active now" in s for s in stale())
    repair.apply()
    assert path.read_text().startswith(
        "<!-- inactive-ok: ADR-002 — both retired -->\n")
    assert stale() == []


def test_comma_separated_codes_keep_their_commas(project):
    decision(project, 1, "Proposed")
    decision(project, 2, "Active")
    decision(project, 3, "Proposed")
    path = page(project,
                "<!-- inactive-ok-file: ADR-001, ADR-002, ADR-003 — open -->\n"
                "`ADR-001 ADR-002 ADR-003`\n")
    repair.apply()
    assert path.read_text().splitlines()[0] == \
        "<!-- inactive-ok-file: ADR-001, ADR-003 — open -->"


def test_an_expiry_is_not_a_code_and_stays(project):
    decision(project, 1, "Active")
    decision(project, 2, "Proposed")
    path = page(project,
                "<!-- inactive-ok: ADR-001 ADR-002 until 2099-01-01 — open -->\n"
                "`ADR-001 ADR-002`\n")
    repair.apply()
    assert path.read_text().splitlines()[0] == \
        "<!-- inactive-ok: ADR-002 until 2099-01-01 — open -->"


def test_only_the_directive_comment_goes_when_it_shares_a_line(project):
    decision(project, 1, "Active")
    path = page(project,
                "<!-- inactive-ok-block: ADR-001 --><!-- unexempt-block: "
                "codeblock -->\n```\nper `ADR-001`\n```\n")
    repair.apply()
    assert path.read_text().splitlines()[0] == \
        "<!-- unexempt-block: codeblock -->"


def test_a_python_comment(project):
    (project / "luria.yaml").write_text(
        merged((project / "luria.yaml").read_text(),
               {"code": {"globs": ["*.py"]}}))
    from luria import config
    config.reset()
    decision(project, 1, "Active")
    path = page(project,
                "def f():\n    # inactive-ok: ADR-001 — what shipped\n"
                "    return 'ADR-001'  # inactive-ok: ADR-001 — again\n",
                name="m.py")
    repair.apply()
    assert path.read_text() == "def f():\n    return 'ADR-001'\n"


def test_a_frontmatter_comment(project):
    decision(project, 1, "Active")
    decision(project, 2, "Proposed")
    path = page(project,
                "---\n# inactive-ok: ADR-001 ADR-002 — retired successors\n"
                "superseded_by: [ADR-001, ADR-002]\n---\n\nBody.\n")
    repair.apply()
    assert path.read_text().splitlines()[1] == \
        "# inactive-ok: ADR-002 — retired successors"


# ── What it leaves ───────────────────────────────────────────────────────


def test_a_retired_code_nothing_cites_is_left_for_a_person(project):
    """Stale, but not mechanically: the citation may have moved a line, and
    the fix is then to move the directive. That is a judgement."""
    decision(project, 1, "Superseded")
    body = "<!-- inactive-ok: ADR-001 — the old way -->\nnothing here\n\n`ADR-001`\n"
    path = page(project, body)
    repair.apply()
    assert path.read_text() == body
    assert any("nothing in scope cites ADR-001" in s for s in stale())


def test_other_acknowledgements_are_never_touched(project):
    decision(project, 1, "Active")
    body = ("<!-- mention-ok: ADR-001 — the spelling is the point -->\n"
            "`ADR-001`\n"
            "<!-- unresolved-ok: ADR-001 ADR-777 — fixture -->\n"
            "`ADR-777`\n"
            "<!-- target-ok: ADR-001.md — gone -->\n"
            "<!-- url-ok: ADR-001 — hand-picked -->\n")
    path = page(project, body)
    repair.apply()
    assert path.read_text() == body


def test_a_malformed_directive_is_left_for_a_person(project):
    """Its problem is already the finding, and what it should have said is a
    judgement the repair cannot make."""
    decision(project, 1, "Active")
    body = "<!-- inactive-ok: ADR-001 ADR-777 — typo somewhere -->\n`ADR-001`\n"
    path = page(project, body)
    repair.apply()
    assert path.read_text() == body


def test_it_is_idempotent_and_clears_the_finding(project):
    decision(project, 1, "Active")
    decision(project, 2, "Superseded")
    page(project, "<!-- inactive-ok-file: ADR-001 ADR-002 — retired -->\n"
                  "`ADR-001 ADR-002`\n")
    page(project, "<!-- inactive-ok: ADR-001 — retired -->\n`ADR-001`\n",
         name="docs/other.md")
    assert len(stale()) == 2
    assert repair.apply()
    assert repair.apply() == []
    assert stale() == []


def test_the_repair_says_what_it_trimmed(project, capsys):
    decision(project, 1, "Active")
    page(project, "<!-- inactive-ok: ADR-001 — retired -->\n`ADR-001`\n")
    repair.apply()
    out = capsys.readouterr().out
    assert "docs/notes.md" in out and "ADR-001" in out
