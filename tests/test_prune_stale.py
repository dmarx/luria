"""`luria repair --prune_stale` removes acknowledgements that excuse nothing (#385).

The default repair trims only a code whose document went Active
(`test_settled_acknowledgements.py`), and leaves a directive that nothing in
scope cites, because the citation may have moved and where the directive
belongs is a judgement. The flag is the owner opting in to that judgement.
Removal is still provably a no-op on the findings: an acknowledgement that
answers for no site suppresses nothing, so its absence surfaces nothing. The
repair re-scans after writing and puts the files back if that ever fails to
hold.

The case that asked for it: Nucleation's lint listed 282 such directives in
267 files, and 69 more after luria 1.7.0's settled-code trim. A further 275
in-use directives also named codes that answered for no site.
"""
# unresolved-ok-file: ADR-777 ADR-778 — fixture codes that name no document on purpose
from pathlib import Path

import pytest

from _scheme import decision

from luria import prune, ref_status, repair


def page(project, body: str, name: str = "docs/notes.md") -> Path:
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


def stale() -> list[str]:
    ref_status.forget_scan()
    return ref_status.stale_annotations()


# ── Off by default ───────────────────────────────────────────────────────


def test_the_default_repair_leaves_an_uncited_directive(project):
    decision(project, 1, "Superseded")
    body = "<!-- inactive-ok-file: ADR-001 — the old way -->\n\nNothing.\n"
    path = page(project, body)
    repair.apply()
    assert path.read_text() == body


# ── What it removes ──────────────────────────────────────────────────────


def test_a_directive_nothing_cites_is_deleted(project):
    decision(project, 1, "Superseded")
    path = page(project, "# Notes\n\n<!-- inactive-ok-file: ADR-001 — the old "
                         "way -->\n\nNothing cites it.\n")
    assert any("nothing in scope cites ADR-001" in s for s in stale())
    assert path in repair.apply(prune_stale=True)
    assert path.read_text() == "# Notes\n\n\nNothing cites it.\n"
    assert stale() == []


def test_a_line_directive_whose_citation_moved_is_deleted(project):
    """The citation is loud either way; deleting the directive changes no
    finding, and moving it is a person's call the lint will prompt."""
    decision(project, 1, "Superseded")
    path = page(project, "<!-- inactive-ok: ADR-001 — the old way -->\n"
                         "nothing here\n\n`ADR-001`\n")
    before = ref_status.summary_lines()
    repair.apply(prune_stale=True)
    assert path.read_text() == "nothing here\n\n`ADR-001`\n"
    ref_status.forget_scan()
    assert ref_status.summary_lines() == before


def test_an_idle_code_leaves_a_directive_still_in_use(project):
    decision(project, 1, "Superseded")
    decision(project, 2, "Superseded")
    path = page(project, "<!-- inactive-ok-file: ADR-001 ADR-002 — retired -->\n"
                         "`ADR-002`\n")
    repair.apply(prune_stale=True)
    assert path.read_text().splitlines()[0] == \
        "<!-- inactive-ok-file: ADR-002 — retired -->"


def test_an_unresolved_ok_nothing_cites_is_deleted(project):
    path = page(project, "<!-- unresolved-ok-file: ADR-777 ADR-778 — fixtures "
                         "-->\n`ADR-778`\n")
    repair.apply(prune_stale=True)
    assert path.read_text().splitlines()[0] == \
        "<!-- unresolved-ok-file: ADR-778 — fixtures -->"


def test_a_mention_ok_nothing_cites_is_deleted(project):
    decision(project, 1, "Active")
    path = page(project, "<!-- mention-ok-file: ADR-001 — the spelling -->\n"
                         "Nothing.\n")
    repair.apply(prune_stale=True)
    assert path.read_text() == "Nothing.\n"


def test_the_repair_says_what_it_pruned(project, capsys):
    decision(project, 1, "Superseded")
    page(project, "<!-- inactive-ok-file: ADR-001 — the old way -->\nNo.\n")
    repair.apply(prune_stale=True)
    out = capsys.readouterr().out
    assert "docs/notes.md" in out and "ADR-001" in out and "excuses" in out


# ── What it leaves ───────────────────────────────────────────────────────


def test_a_mention_ok_whose_code_is_cited_stays(project):
    """A `mention-ok` answers for the text, whatever the document's state
    (ADR-105). Its site may be excused by another annotation today and need
    the mention tomorrow, so cited at all is enough to keep it."""
    decision(project, 1, "Superseded")
    body = ("<!-- inactive-ok-file: ADR-001 — retired -->\n"
            "<!-- mention-ok-file: ADR-001 — the spelling -->\n`ADR-001`\n")
    path = page(project, body)
    repair.apply(prune_stale=True)
    assert path.read_text() == body


def test_a_malformed_directive_is_left_for_a_person(project):
    decision(project, 1, "Superseded")
    body = "<!-- inactive-ok-file: ADR-001 ADR-777 — typo -->\nNothing.\n"
    path = page(project, body)
    repair.apply(prune_stale=True)
    assert path.read_text() == body


def test_a_directive_in_use_is_left(project):
    decision(project, 1, "Superseded")
    body = "<!-- inactive-ok-file: ADR-001 — retired -->\n`ADR-001`\n"
    path = page(project, body)
    repair.apply(prune_stale=True)
    assert path.read_text() == body


def test_it_is_idempotent(project):
    decision(project, 1, "Superseded")
    decision(project, 2, "Active")
    page(project, "<!-- inactive-ok-file: ADR-001 ADR-002 — old -->\nNo.\n")
    page(project, "<!-- inactive-ok: ADR-001 — old -->\nNo.\n",
         name="docs/other.md")
    assert repair.apply(prune_stale=True)
    assert repair.apply(prune_stale=True) == []
    assert stale() == []


# ── The guard ────────────────────────────────────────────────────────────


def test_the_guard_restores_the_files_when_a_finding_changes(project,
                                                             monkeypatch):
    """Fired once on a sabotaged prune (DP-6): if removing what excused
    nothing ever changed a finding, the argument was wrong, so the files go
    back and the repair says so rather than writing."""
    decision(project, 1, "Superseded")
    body = "<!-- inactive-ok-file: ADR-001 — retired -->\n`ADR-001`\n"
    path = page(project, body)
    # Pretend the directive excused nothing, so the prune removes one that
    # was answering for the citation.
    monkeypatch.setattr(prune, "_idle", lambda ann, excused, cited: ann.codes)
    with pytest.raises(prune.PruneChangedFindings, match="ADR-001"):
        prune.prune_stale()
    assert path.read_text() == body
