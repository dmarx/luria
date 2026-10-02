# tests/test_unrevisited_summary.py
"""A version bump that leaves `summary:` untouched is worth a second look (#326).

`summary:` is what the index shows, so it is the line a reader meets first,
and it is the line an amendment never touches: amending means arguing with
the body, and the summary sits above the `---` with the metadata. In the
record that measured it, one summary in twelve amendments was a true sentence
about a superseded state. A warning with an acknowledgement, not a violation:
the other eleven survived their amendments legitimately.

The previous revision is git's question, so the check compares the working
tree against HEAD. That is when a person can still fix it; once committed,
the check has nothing to compare and says nothing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from luria import config, lint, revisits

DOC = """---
status: Active
title: 'A practice'
version: {version}
tags:
- record
date: '2026-01-01'
{directive}summary: >-
  {summary}
{history}---

# ADR-001: A practice

{body}
"""


def _write(root: Path, version: int = 1, summary: str = "The evidence is "
           "image classifiers only.", body: str = "Body.",
           directive: str = "") -> Path:
    history = "".join(
        f"- version: {v}\n  date: '2026-01-0{v}'\n  note: amended\n"
        for v in range(1, version + 1)) if version > 1 else ""
    path = root / "record/decisions.d/ADR-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DOC.format(
        version=version, summary=summary, body=body,
        directive=f"# {directive}\n" if directive else "",
        history=f"history:\n{history}" if history else ""))
    return path


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   cwd=root, check=True, capture_output=True)


def _committed(project) -> Path:
    path = _write(project)
    _git(project, "init", "-q", ".")
    _git(project, "add", "-A")
    _git(project, "commit", "-qm", "seed")
    config.reset()
    return path


def test_a_bump_with_the_same_summary_is_reported(project):
    _committed(project)
    _write(project, version=2, body="Body. The verdict reverses on text.")
    flagged, stale = revisits.unrevisited_summaries()
    assert len(flagged) == 1, flagged
    assert "ADR-001.md" in flagged[0] and "v2" in flagged[0]
    assert "summary-ok:" in flagged[0]


def test_the_finding_names_the_summary_line(project):
    _committed(project)
    path = _write(project, version=2)
    line = path.read_text().splitlines().index("summary: >-") + 1
    flagged, _ = revisits.unrevisited_summaries()
    assert f"ADR-001.md:{line}:" in flagged[0], flagged


def test_a_bump_that_revisits_the_summary_is_silent(project):
    _committed(project)
    _write(project, version=2, summary="Image classifiers; reverses on text.")
    assert revisits.unrevisited_summaries() == ([], [])


def test_an_edit_without_a_bump_is_silent(project):
    """A typo fix is not an amendment; only a new version claims one."""
    _committed(project)
    _write(project, body="Body, with a typo fixed.")
    assert revisits.unrevisited_summaries() == ([], [])


def test_once_committed_there_is_nothing_to_compare(project):
    _committed(project)
    _write(project, version=2)
    _git(project, "commit", "-qam", "amend")
    assert revisits.unrevisited_summaries() == ([], [])


def test_without_git_the_check_is_silent(project):
    _write(project, version=2)
    config.reset()
    assert revisits.unrevisited_summaries() == ([], [])


def test_an_acknowledgement_naming_the_version_silences_it(project):
    _committed(project)
    _write(project, version=2, directive="summary-ok: v2 — a recap of what "
           "the source measured; the amendment narrowed scope in the body")
    assert revisits.unrevisited_summaries() == ([], [])


def test_an_acknowledgement_for_another_version_is_stale(project):
    """It excused an earlier bump. This one is a new question."""
    _committed(project)
    _write(project, version=2, directive="summary-ok: v1 — an old reason")
    flagged, stale = revisits.unrevisited_summaries()
    assert len(flagged) == 1 and len(stale) == 1, (flagged, stale)
    assert "summary-ok: v1" in stale[0]


def test_a_committed_acknowledgement_is_not_called_stale(project):
    """After the commit the check cannot see the bump at all, so it cannot
    say the acknowledgement excuses nothing — removing it would be churn."""
    _committed(project)
    _write(project, version=2, directive="summary-ok: v2 — kept on purpose")
    _git(project, "commit", "-qam", "amend")
    assert revisits.unrevisited_summaries() == ([], [])


def test_the_lint_reports_it_as_its_own_class(project):
    _committed(project)
    _write(project, version=2)
    classes = [name for name, _, _ in lint.status_sections()]
    assert "unrevisited-summaries" in classes
    assert "unrevisited-summaries" in lint.FAILABLE


def test_a_later_edit_does_not_make_an_acknowledgement_stale(project):
    """A typo fixed after the amendment was committed is not a new bump, so
    the acknowledgement above the summary is not being asked anything."""
    _committed(project)
    _write(project, version=2, directive="summary-ok: v2 — kept on purpose")
    _git(project, "commit", "-qam", "amend")
    _write(project, version=2, body="Body, typo fixed.",
           directive="summary-ok: v2 — kept on purpose")
    assert revisits.unrevisited_summaries() == ([], [])
