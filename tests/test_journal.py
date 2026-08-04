"""Tests for the journal: dated entries that persist, rendered into books
([ADR-020](../meta/decisions/ADR-020.md)).

The property the whole scheme rests on is that **the path is the timestamp**.
Ordering, book membership and the contents list are all derived from it, so
each of those is checked against a tree built to say something specific rather
than against whatever this repo happens to have filed.
"""
import datetime as dt
from pathlib import Path

import pytest

from luria import journal
from luria.config import Journal, current

REPO = Path(__file__).resolve().parents[1]


def jrnl(tmp_path: Path, granularity: str = "month") -> Journal:
    return Journal("devlog", dir=tmp_path / "devlog.d",
                   output=tmp_path / "docs" / "devlog",
                   granularity=granularity, title="Development log",
                   _root=tmp_path)


def file_entry(j: Journal, stamp: str, title: str, body: str = "Body.",
               tags: list[str] | None = None) -> Path:
    created = dt.datetime.fromisoformat(stamp)
    path = journal.path_for(j, created)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: {title!r}\ncreated: '{created.isoformat()}'\n"
        f"tags: {tags or []}\n---\n\n{body}\n")
    return path


# ── Identity is the timestamp ────────────────────────────────────────────


def test_path_is_derived_from_the_timestamp(tmp_path):
    j = jrnl(tmp_path)
    created = dt.datetime(2026, 8, 3, 21, 19, 26)
    assert journal.path_for(j, created) == j.dir / "2026/08/03/211926.md"


def test_path_and_created_round_trip(tmp_path):
    j = jrnl(tmp_path)
    created = dt.datetime(2026, 1, 9, 4, 5, 6)
    assert journal.created_from_path(journal.path_for(j, created)) == created


@pytest.mark.parametrize("raw,want", [
    ("2026-08-03T21:19:26", dt.datetime(2026, 8, 3, 21, 19, 26)),
    (dt.datetime(2026, 8, 3, 21, 19, 26), dt.datetime(2026, 8, 3, 21, 19, 26)),
    (dt.date(2026, 8, 3), dt.datetime(2026, 8, 3)),
    ("not a date", None),
    (None, None),
])
def test_created_accepts_what_yaml_hands_back(raw, want):
    """Quoting decides whether the YAML parser returns a string, a date or a
    datetime. Making the author remember which one is a trap, not a rule."""
    assert journal.parse_created(raw) == want


def test_new_steps_forward_on_a_collision(tmp_path):
    """Not a probability argument — the filesystem already knows."""
    j = jrnl(tmp_path)
    now = dt.datetime(2026, 8, 3, 21, 19, 26)
    first = journal.new(j, "One", now)
    second = journal.new(j, "Two", now)
    assert first.name == "211926.md"
    assert second.name == "211927.md"


def test_new_writes_frontmatter_the_lint_accepts(tmp_path):
    j = jrnl(tmp_path)
    path = journal.new(j, "A title", dt.datetime(2026, 8, 3, 21, 19, 26))
    entry = journal.read(path)
    assert entry.title == "A title"
    assert journal.path_for(j, entry.created) == path


# ── Ordering ─────────────────────────────────────────────────────────────


def test_entries_sort_by_time_not_by_filesystem_order(tmp_path):
    """The point of the scheme: what the log says happened first is a property
    of the record, not of the order the branches landed."""
    j = jrnl(tmp_path)
    file_entry(j, "2026-09-01T09:00:00", "September")
    file_entry(j, "2026-08-03T21:19:26", "August, later")
    file_entry(j, "2026-08-03T08:00:00", "August, earlier")
    assert [e.title for e in journal.entries(j)] == [
        "August, earlier", "August, later", "September"]


def test_the_template_is_not_an_entry(tmp_path):
    j = jrnl(tmp_path)
    j.dir.mkdir(parents=True)
    (j.dir / "_template.md").write_text("---\ntitle: 'x'\n---\n\nShape.\n")
    file_entry(j, "2026-08-03T21:19:26", "Real")
    assert [e.title for e in journal.entries(j)] == ["Real"]


# ── Books ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("granularity,keys", [
    ("day", ["2026-08-03", "2026-08-04"]),
    ("month", ["2026-08"]),
    ("year", ["2026"]),
])
def test_granularity_decides_the_partition(tmp_path, granularity, keys):
    """The right book size depends on how fast a project writes, which is a
    measurement rather than a constant."""
    j = jrnl(tmp_path, granularity)
    file_entry(j, "2026-08-03T21:19:26", "One")
    file_entry(j, "2026-08-04T03:27:11", "Two")
    assert sorted(journal.books(j)) == keys


def test_book_lists_its_contents(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, "2026-08-03T21:19:26", "The first thing")
    file_entry(j, "2026-08-04T03:27:11", "The second thing")
    book = journal.render_book(j, "2026-08", journal.books(j)["2026-08"])
    assert "# Development log — August 2026" in book
    assert "- [3 Aug 21:19 — The first thing](#20260803211926)" in book
    assert "- [4 Aug 03:27 — The second thing](#20260804032711)" in book
    # Every contents entry has somewhere to land.
    for anchor in ("20260803211926", "20260804032711"):
        assert f'<a name="{anchor}"></a>' in book


def test_anchor_is_the_timestamp_not_the_title(tmp_path):
    """A title can be corrected. A heading-derived anchor would break every
    link to it silently, which is the failure polarity DP-3 rules out."""
    j = jrnl(tmp_path)
    file_entry(j, "2026-08-03T21:19:26", "Before")
    before = journal.entries(j)[0].anchor
    file_entry(j, "2026-08-03T21:19:26", "After — retitled")
    assert journal.entries(j)[0].anchor == before


def test_tags_are_shown_when_present(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, "2026-08-03T21:19:26", "Tagged", tags=["lint", "record"])
    book = journal.render_book(j, "2026-08", journal.books(j)["2026-08"])
    assert "*2026-08-03 21:19:26 · lint · record*" in book


def test_index_lists_books_newest_first(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, "2026-07-01T09:00:00", "July")
    file_entry(j, "2026-08-03T21:19:26", "August")
    index = journal.render_index(j, journal.books(j))
    assert index.index("[2026-08]") < index.index("[2026-07]")
    assert "2 entries across 2 books" in index


def test_a_single_book_reads_as_one(tmp_path):
    j = jrnl(tmp_path)
    file_entry(j, "2026-08-03T21:19:26", "Only")
    assert "1 entry across 1 book," in journal.render_index(j, journal.books(j))


# ── Against the real corpus ──────────────────────────────────────────────


def test_this_repos_journal_is_filed_correctly():
    """The record Luria keeps of itself is the first consumer (ADR-009)."""
    cfg = current()
    assert cfg.journals, "this repo configures a devlog journal"
    for j in cfg.journals.values():
        filed = journal.entries(j)
        assert filed
        for entry in filed:
            assert journal.path_for(j, entry.created) == entry.path
            assert entry.title


def test_entries_are_never_consumed():
    """A journal's sources persist — that is the whole difference from a
    collected view (ADR-012), and it is what makes staleness computable."""
    cfg = current()
    j = next(iter(cfg.journals.values()))
    before = {p for p in j.dir.rglob("*.md")}
    journal.outputs()
    assert {p for p in j.dir.rglob("*.md")} == before


def test_an_unused_journal_renders_nothing(tmp_path, monkeypatch):
    """The default config names a devlog. A project that never files an entry
    should not grow an empty `docs/devlog/`."""
    (tmp_path / "luria.toml").write_text('[luria]\nissue_url = ""\n')
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    from luria import config as config_mod
    config_mod.reset()
    assert current().journals                      # configured…
    assert journal.outputs() == {}                 # …and silent
    config_mod.reset()
