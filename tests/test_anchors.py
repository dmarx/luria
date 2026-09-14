# tests/test_anchors.py
"""An anchor a fragment link can actually reach.

The generator emitted `<a name="dp-3"></a>`. That resolves in the repository
and on GitHub, because a real navigation falls back to `a[name]` when no
element carries the `id`. It does not resolve on a Quartz site: Quartz is a
single-page app, and its router scrolls with

    document.getElementById(decodeURIComponent(url.hash.substring(1)))

which finds an `id` and nothing else (quartz v4.5.2,
`components/scripts/spa.inline.ts`). So every citation of a principle and
every devlog entry link landed at the top of the page it named, on the one
surface those views are published to — and worked everywhere a contributor
would look for the bug.

`id` satisfies both. These are the tests for that, and for the check that
keeps a hand-written anchor from reintroducing it (ADR-099).
"""

# inactive-ok-file: ADR-100 — Proposed. Every mention names it as
# the decision this file implements or is written against; the citation
# is to the reasoning, not a claim the decision is settled.

# inactive-ok-file: ADR-099 — Proposed. Every mention names it as the
# decision this file implements or is written against; the citation is to
# the reasoning, not a claim the decision is settled.

from __future__ import annotations

from _config import merged

import re
from pathlib import Path

from luria import adr_index, config, journal, lint

ANCHOR_RE = re.compile(r'<a\s+([^>]*)></a>')


def attrs(html: str) -> list[str]:
    return [m.group(1) for m in ANCHOR_RE.finditer(html)]


def test_a_journal_book_anchors_its_entries_by_id(project, monkeypatch):
    """55 links in one book of this project's own devlog, every one of them
    landing at the top of the page on the published site."""
    root = _journal_project(project, monkeypatch)
    j = config.current().journals["devlog"]
    key, filed = next(iter(journal.books(j).items()))
    book = journal.render_book(j, key, filed)
    assert '<a id="20260901120000"></a>' in book
    assert "<a name=" not in book


def test_an_assembled_documents_anchors_are_ids(project, monkeypatch):
    """The same fix on the other emitter: a `render = "document"` scheme
    gives each source an anchor in the page it assembles into, and a citation
    with `cite = "view"` points at it."""
    root = _document_project(project, monkeypatch)
    scheme = config.current().schemes["DP"]
    page = adr_index.render_document(scheme, adr_index.load_scheme(scheme))
    assert '<a id="dp-1"></a>' in page
    assert "<a name=" not in page


def test_an_anchor_reachable_only_by_name_is_a_finding(project, monkeypatch):
    """A hand-written `<a name=>` in prose somebody links to. The generator
    cannot be the only thing that knows this rule, or the next hand-written
    anchor puts the bug back."""
    root = _linked_pair(project, monkeypatch, '<a name="here"></a>')
    errors: list[str] = []
    lint.check_anchors(errors)
    assert any("here" in e and "luria link --fix" in e for e in errors), errors


def test_an_anchor_that_is_an_id_is_silent(project, monkeypatch):
    root = _linked_pair(project, monkeypatch, '<a id="here"></a>')
    errors: list[str] = []
    lint.check_anchors(errors)
    assert errors == [], errors


def test_a_fragment_naming_a_heading_is_silent(project, monkeypatch):
    """A heading gets an `id` from every renderer there is. Only an explicit
    anchor can be addressable in one place and not another."""
    root = _linked_pair(project, monkeypatch, "## Here", frag="here")
    errors: list[str] = []
    lint.check_anchors(errors)
    assert errors == [], errors


def test_the_fixer_rewrites_the_anchor_it_named(project, monkeypatch):
    """`--fix` repairs the TARGET, because that is where the defect is: the
    link is spelled correctly and the thing it names cannot be found."""
    root = _linked_pair(project, monkeypatch, '<a name="here"></a>')
    from luria import link_refs
    assert link_refs.fix_anchors(fix=True)
    assert '<a id="here"></a>' in (root / "docs" / "target.md").read_text()
    errors: list[str] = []
    lint.check_anchors(errors)
    assert errors == [], errors


def test_a_stale_committed_view_is_not_a_finding(project, monkeypatch):
    """The regression CI found. A branch carries the DEFAULT branch's copies
    of every view and deliberately does not update them (ADR-018), so a
    check that read them failed every pull request touching an anchor and
    named a repair the author was not allowed to make. The question is about
    this source tree: what will the views it renders contain?"""
    root = _journal_project(project, monkeypatch)
    book = root / "docs" / "devlog" / "2026-09.md"
    book.parent.mkdir(parents=True, exist_ok=True)
    book.write_text('# Book\n\n<a name="20260901120000"></a>\n\n## An entry\n')
    (book.parent / "README.md").write_text(
        "# Development log\n\n- [An entry](2026-09.md#20260901120000)\n")
    config.reset()
    errors: list[str] = []
    lint.check_anchors(errors)
    assert errors == [], errors


def test_an_anchor_that_reaches_a_view_through_a_stub_is_a_finding(
        project, monkeypatch):
    """A stub is the hand-written part of a generated page, so an anchor
    written there lands in a view the same way the generator's does — and is
    the one case where a person, not the generator, owns the repair. The
    finding names the stub, which is the file they can edit."""
    root = project
    scheme = config.current().schemes["ADR"]
    scheme.dir.mkdir(parents=True, exist_ok=True)
    scheme.stub.write_text(
        "# Decisions\n\n"
        '<a name="why"></a>\n\nWhy these exist.\n\n'
        "See [the reason](README.md#why).\n\n{categories}\n\n{table}\n")
    config.reset()
    errors: list[str] = []
    lint.check_anchors(errors)
    assert len(errors) == 1, errors
    assert "README.stub" in errors[0] and "#why" in errors[0]

    from luria import link_refs
    assert link_refs.fix_anchors(fix=True) == 1
    assert '<a id="why"></a>' in scheme.stub.read_text()
    errors = []
    lint.check_anchors(errors)
    assert errors == [], errors


# --- fixtures -------------------------------------------------------------

def _extend(root: Path, extra: dict) -> None:
    path = root / "luria.yaml"
    path.write_text(merged(path.read_text(), extra))
    config.reset()


def _journal_project(root: Path, monkeypatch) -> Path:
    _extend(root, {"journals": {"devlog": {
        "dir": "record/devlog.d", "output": "docs/devlog",
        "granularity": "month", "title": "Development log"}}})
    d = root / "record" / "devlog.d" / "2026" / "09" / "01"
    d.mkdir(parents=True)
    (d / "120000.md").write_text(
        "---\ncreated: '2026-09-01 12:00:00'\ntitle: 'An entry'\n---\n\nBody.\n")
    config.reset()
    return root


def _document_project(root: Path, monkeypatch) -> Path:
    _extend(root, {"schemes": {"DP": {
        "dir": "record/principles.d", "output": "docs/design-principles.md",
        "render": "document"}}})
    d = root / "record" / "principles.d"
    d.mkdir(parents=True, exist_ok=True)
    (d / "DP-001.md").write_text(
        "---\nstatus: Active\ntitle: 'A principle'\nversion: 1\n"
        "date: '2026-01-01'\n---\n\n# DP-001: A principle\n\nBody.\n")
    config.reset()
    return root


def _linked_pair(root: Path, monkeypatch, anchor: str, frag: str = "here") -> Path:
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "target.md").write_text(f"# Target\n\n{anchor}\n\nBody.\n")
    (root / "docs" / "source.md").write_text(
        f"# Source\n\nSee [the thing](target.md#{frag}).\n")
    (root / "docs" / "README.md").write_text(
        "# Docs\n\n- [Target](target.md)\n- [Source](source.md)\n")
    config.reset()
    return root


# --- a fragment that reaches nothing (ADR-100) ------------------------
#
# Checkable only since luria owns a slugger: a heading's anchor is assigned
# by the publisher, and a check that guessed at it would report links that
# work. The generator writes these links now, so the check is also the guard
# on the generator.

def test_a_fragment_that_names_no_heading_and_no_id_is_a_finding(
        project, monkeypatch):
    root = _linked_pair(project, monkeypatch, "## Something else", frag="here")
    errors: list[str] = []
    lint.check_anchors(errors)
    assert len(errors) == 1, errors
    assert "reaches no heading and no `id`" in errors[0]


def test_a_reworded_heading_is_what_this_catches(project, monkeypatch):
    """The fragility the slug switch buys, made loud. A contents list links
    the heading; somebody rewords the heading; the link goes nowhere and
    nothing else in the record would have said so."""
    root = _linked_pair(project, monkeypatch, "## Here", frag="here")
    (root / "docs" / "target.md").write_text("# Target\n\n## Here now\n\nBody.\n")
    config.reset()
    errors: list[str] = []
    lint.check_anchors(errors)
    assert any("#here" in e for e in errors), errors


def test_a_fragment_naming_a_heading_that_is_there_is_silent(
        project, monkeypatch):
    _linked_pair(project, monkeypatch, "## Here", frag="here")
    errors: list[str] = []
    lint.check_anchors(errors)
    assert errors == [], errors


def test_a_link_into_a_file_this_record_does_not_own_is_not_a_finding(
        project, monkeypatch):
    """Reporting every one of those would bury the ones that are ours."""
    root = _linked_pair(project, monkeypatch, "## Here", frag="here")
    (root / "docs" / "source.md").write_text(
        "# Source\n\nSee [elsewhere](../../outside/thing.md#whatever).\n")
    config.reset()
    errors: list[str] = []
    lint.check_anchors(errors)
    assert errors == [], errors


# --- the contents list links what the page offers (ADR-100) -----------

def test_a_books_contents_links_the_heading_not_the_timestamp(
        project, monkeypatch):
    """Both addresses resolve. Only one is the one the page hands a reader —
    Quartz puts its ¶ anchor and its own sidebar TOC on the heading — and a
    contents list pointing somewhere else is two addresses for one entry."""
    root = _journal_project(project, monkeypatch)
    j = config.current().journals["devlog"]
    key, filed = next(iter(journal.books(j).items()))
    book = journal.render_book(j, key, filed)
    assert "](#an-entry)" in book
    assert "](#20260901120000)" not in book
    # The durable anchor stays, unlinked: a citation written by hand needs
    # something that does not move when the title is reworded.
    assert '<a id="20260901120000"></a>' in book


def test_the_journal_index_links_the_same_anchor_as_the_book(
        project, monkeypatch):
    root = _journal_project(project, monkeypatch)
    j = config.current().journals["devlog"]
    grouped = journal.books(j)
    index = journal.render_index(j, grouped)
    key, filed = next(iter(grouped.items()))
    book = journal.render_book(j, key, filed)
    assert f"]({key}.md#an-entry)" in index
    assert "](#an-entry)" in book


def test_an_entry_body_heading_shifts_the_slugs_after_it(
        project, monkeypatch):
    """Why the slug is computed over the whole book rather than off the
    titles: a heading inside one entry's body consumes a slug, and a later
    entry with the same title is `-1`, not the bare one."""
    root = _journal_project(project, monkeypatch)
    d = root / "record" / "devlog.d" / "2026" / "09" / "02"
    d.mkdir(parents=True, exist_ok=True)
    (d / "120000.md").write_text(
        "---\ncreated: '2026-09-02 12:00:00'\ntitle: 'An entry'\n---\n\nBody.\n")
    config.reset()
    j = config.current().journals["devlog"]
    key, filed = next(iter(journal.books(j).items()))
    book = journal.render_book(j, key, filed)
    assert "](#an-entry)" in book and "](#an-entry-1)" in book
