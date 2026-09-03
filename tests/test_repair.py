"""`luria repair` — the source repairs, apart from the views (ADR-tmphzwg9).

A repair is committed on the branch that authored the source; a view on the
default branch only. The split rests on two properties: `luria repair` writes
every mechanical repair the lint would otherwise report, and `luria index`
writes none of them — so each commit point has exactly one writer. And the
generation job runs again on the commit it pushed, so a second `luria repair`
must find nothing to do.
"""
from pathlib import Path

from _scheme import decision

from luria import adr_index, lint, repair
from luria.config import current

from tests.test_lint import entry, journal_project


def test_repair_populates_a_missing_created(project):
    root = journal_project(project)
    path = entry(root, "2026/08/03/211926", created=None)
    assert repair.apply() == [path]
    assert "created: '2026-08-03T21:19:26'" in path.read_text()


def test_repair_links_a_bare_reference(project):
    decision(project, 1, "Active")
    path = decision(project, 2, "Active",
                    summary="Follows ADR-001 in every respect.")
    written = repair.apply()
    assert path in written
    assert "[ADR-001](ADR-001.md)" in path.read_text()


def test_repair_is_idempotent(project):
    """The job that pushes a repair runs again on what it pushed."""
    root = journal_project(project)
    entry(root, "2026/08/03/211926", created=None)
    assert repair.apply()
    assert repair.apply() == []


def test_repair_clears_what_the_lint_reported(project):
    """The lint names `luria repair` as the remedy; the remedy has to work."""
    root = journal_project(project)
    entry(root, "2026/08/03/211926", created=None)
    before: list[str] = []
    lint.check_journals(before)
    assert any("`luria repair` populates it from the path" in e for e in before)
    repair.apply()
    after: list[str] = []
    lint.check_journals(after)
    assert after == []


def test_index_writes_no_source(project):
    """`luria index` is views only: a source it used to repair is left as
    filed, for `luria repair` and the commit point that belongs to."""
    root = journal_project(project)
    path = entry(root, "2026/08/03/211926", created=None)
    before = path.read_text()
    adr_index.run()
    assert path.read_text() == before
    assert (current().root / "docs" / "devlog").exists(), "the views rendered"
