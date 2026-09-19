# tests/test_store.py
"""The store: one door to the record's sources, two backends behind it (#110).

What these hold: routing is by path and only a source path reaches the
backend; the SQLite backend answers the same questions a directory of files
does — list, read, write, delete, move, revision — and under it a file on
disk inside a source directory is not the record.
"""
from pathlib import Path

import pytest

from luria import config, store
from luria.config import current

# unresolved-ok-file: ADR-tmpabcde, ADR-404 — fixture codes: a temporary
# document being moved, and a row that is deliberately not there.


def sqlite_record(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "luria.yaml").write_text(
        "issue_url: https://example.test/{n}\n"
        "backend:\n  kind: sqlite\n  file: record.sqlite\n"
        "schemes:\n  ADR:\n    dir: record/decisions.d\n"
        "    output: docs/decisions\n"
        "journals:\n  devlog:\n    dir: record/devlog.d\n"
        "    output: docs/devlog\n    granularity: month\n"
        "fragments:\n  record/changelog.d:\n    file: CHANGELOG.md\n",
        encoding="utf-8")
    (tmp_path / "docs").mkdir()
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    current()
    return tmp_path


def test_a_files_backend_is_the_default():
    assert current().backend.kind == "files"


def test_an_unknown_backend_is_refused(tmp_path, monkeypatch):
    (tmp_path / "luria.yaml").write_text("backend:\n  kind: parchment\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    with pytest.raises(ValueError, match="parchment"):
        current()


def test_before_any_config_every_path_is_a_file(tmp_path):
    config.reset()
    path = tmp_path / "note.md"
    store.write_text(path, "hello")
    assert path.read_text() == "hello"
    assert store.read_text(path) == "hello"
    assert not store.is_source(path)


def test_only_source_paths_are_the_record_s(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    assert store.is_source(root / "record" / "decisions.d" / "ADR-001.md")
    assert store.is_source(root / "record" / "decisions.d")
    assert store.is_source(root / "record" / "devlog.d" / "2026" / "01" / "01" / "000000.md")
    assert store.is_source(root / "record" / "changelog.d" / "x.md")
    assert not store.is_source(root / "docs" / "page.md")
    assert not store.is_source(root / "luria.yaml")
    assert not store.is_source(root / "record")


def test_sqlite_round_trip(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    doc = root / "record" / "decisions.d" / "ADR-001.md"
    assert not store.exists(doc)
    store.write_text(doc, "---\nstatus: Active\n---\n\nBody.\n")
    assert store.exists(doc) and store.is_file(doc)
    assert store.read_text(doc) == "---\nstatus: Active\n---\n\nBody.\n"
    assert not doc.exists(), "a source under the SQLite backend is not a file"
    assert (root / "record.sqlite").exists()


def test_a_missing_row_reads_like_a_missing_file(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    with pytest.raises(OSError):
        store.read_text(root / "record" / "decisions.d" / "ADR-404.md")
    with pytest.raises(OSError):
        store.unlink(root / "record" / "decisions.d" / "ADR-404.md")


def test_revision_moves_on_every_write(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    doc = root / "record" / "decisions.d" / "ADR-001.md"
    assert store.revision(doc) is None
    store.write_text(doc, "one")
    first = store.revision(doc)
    store.write_text(doc, "one")           # same text, still a new revision
    assert store.revision(doc) != first
    assert store.revision(root / "record" / "decisions.d") is not None


def test_a_directory_s_revision_moves_when_its_set_does(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    d = root / "record" / "decisions.d"
    assert store.revision(d) is None
    store.write_text(d / "ADR-001.md", "a")
    before = store.revision(d)
    store.write_text(d / "ADR-002.md", "b")
    assert store.revision(d) != before
    # Back to one row, but a different one: the key must not land back on
    # `before`, or a listing cached at `before` would name ADR-001.
    store.unlink(d / "ADR-001.md")
    assert store.revision(d) != before
    assert store.glob(d, "*.md") == [d / "ADR-002.md"]


def test_glob_and_rglob_see_rows_and_not_stray_files(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    d = root / "record" / "decisions.d"
    store.write_text(d / "ADR-001.md", "a")
    store.write_text(d / "_template.md", "t")
    store.write_text(d / "README.stub", "s")
    entry = root / "record" / "devlog.d" / "2026" / "01" / "02" / "030405.md"
    store.write_text(entry, "e")
    # A file on disk inside a source directory is not the record.
    d.mkdir(parents=True, exist_ok=True)
    (d / "ADR-009.md").write_text("stray")
    assert store.glob(d, "*.md") == [d / "ADR-001.md", d / "_template.md"]
    assert store.glob(d, "*.stub") == [d / "README.stub"]
    assert store.rglob(root / "record" / "devlog.d", "*.md") == [entry]
    assert entry in store.rglob(root, "*.md")
    assert d / "ADR-009.md" not in store.rglob(root, "*.md")
    assert not store.exists(d / "ADR-009.md")


def test_glob_still_sees_the_files_that_are_not_sources(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    (root / "docs" / "page.md").write_text("p")
    assert store.glob(root / "docs", "*.md") == [root / "docs" / "page.md"]
    assert store.rglob(root, "*.yaml") == [root / "luria.yaml"]


def test_move_within_the_store_and_across_the_boundary(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    d = root / "record" / "decisions.d"
    store.write_text(d / "ADR-tmpabcde.md", "temp")
    store.move(d / "ADR-tmpabcde.md", d / "ADR-001.md")
    assert store.read_text(d / "ADR-001.md") == "temp"
    assert not store.exists(d / "ADR-tmpabcde.md")
    out = root / "build" / "ADR-001.md"
    store.move(d / "ADR-001.md", out)
    assert out.read_text() == "temp"
    assert not store.exists(d / "ADR-001.md")


def test_sources_lists_every_row_under_every_source_dir(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    d = root / "record" / "decisions.d"
    store.write_text(d / "ADR-001.md", "a")
    store.write_text(root / "record" / "changelog.d" / "x.md", "x")
    (root / "docs" / "page.md").write_text("p")
    assert store.sources() == [root / "record" / "changelog.d" / "x.md",
                               d / "ADR-001.md"]


def test_added_order_is_the_filing_sequence(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    frag = root / "record" / "changelog.d"
    store.write_text(frag / "b.md", "b")
    store.write_text(frag / "a.md", "a")
    assert store.added_order(frag / "b.md") < store.added_order(frag / "a.md")


def test_reading_never_creates_the_database(tmp_path, monkeypatch):
    """A record whose database is missing is a record with a problem to
    report, not an empty one to quietly invent."""
    root = sqlite_record(tmp_path, monkeypatch)
    assert store.glob(root / "record" / "decisions.d", "*.md") == []
    assert not store.exists(root / "record" / "decisions.d" / "ADR-001.md")
    assert not (root / "record.sqlite").exists()


def test_reset_closes_the_backend(tmp_path, monkeypatch):
    root = sqlite_record(tmp_path, monkeypatch)
    store.write_text(root / "record" / "decisions.d" / "ADR-001.md", "a")
    config.reset()
    assert store.active() is None
    (root / "record.sqlite").unlink()       # nothing holds it open
    current()
    assert store.glob(root / "record" / "decisions.d", "*.md") == []
