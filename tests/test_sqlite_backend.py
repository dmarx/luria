# tests/test_sqlite_backend.py
"""The machinery operating on a record whose sources are rows (#110).

`backend: {kind: sqlite}` and every command reads and writes the database:
`luria new` files a row, the lint validates its fields, `luria index`
renders the views from it, `luria export` refreshes the queryable tables in
place and writes the markdown tree back out. The strongest test is the
last one — this repository's own record, converted, lints and renders
byte-for-byte the same from a database as from the tree.
"""
import shutil
import sqlite3
from pathlib import Path

import pytest

from luria import adr_index, collect, config, export, lint, new, store
from luria.config import current

from _scheme import decision

REPO = Path(__file__).resolve().parents[1]

CONFIG = """
issue_url: https://example.test/issues/{n}
backend:
  kind: sqlite
  file: record.sqlite
vocabularies:
  statuses:
    Active: {blurb: in force}
    Proposed: {blurb: not yet}
    Deferred: {blurb: parked}
    Superseded: {blurb: replaced}
    Rejected: {blurb: declined}
schemes:
  ADR:
    dir: record/decisions.d
    output: docs/decisions
    active: Active
    render: index
    axis: tags
    fields:
      status:
        vocabulary: statuses
      tags:
        many: true
journals:
  devlog:
    dir: record/devlog.d
    output: docs/devlog
    granularity: month
fragments:
  record/changelog.d:
    file: CHANGELOG.md
    style: changelog
"""


@pytest.fixture
def db_project(tmp_path, monkeypatch):
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "luria.yaml").write_text(CONFIG, encoding="utf-8")
    (tmp_path / "docs" / "design-principles.md").write_text(
        "# Design principles\n\n## 1. First value\n\nBody.\n")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n<!-- luria-insert-here -->\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()


def rows(db: Path, sql: str) -> list[tuple]:
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchall()


def test_new_files_a_row_and_no_file(db_project):
    path = new.new_entry("adr", {"title": "Filed into the database"}, None)
    assert path == db_project / "record" / "decisions.d" / "ADR-001.md"
    assert not path.exists()
    assert rows(db_project / "record.sqlite",
                "SELECT path FROM sources") == [("record/decisions.d/ADR-001.md",)]
    assert "Filed into the database" in store.read_text(path)
    assert current().schemes["ADR"].documents() == {1: path}


def test_new_journal_entry_files_a_row(db_project):
    path = new.new_entry(None, {"title": "What happened"}, None)
    assert not path.exists()
    assert "title: 'What happened'" in store.read_text(path)
    assert path.parent.parent.parent.parent == current().journals["devlog"].dir


def test_lint_validates_the_fields_of_a_row(db_project):
    decision(db_project, 1, "Active")
    doc = db_project / "record" / "decisions.d" / "ADR-002.md"
    store.write_text(doc, "---\ntitle: 'No status here'\ntags: [record]\n"
                          "date: '2026-01-01'\n---\n\n# ADR-002: No status here\n")
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert any("ADR-002.md" in e and "status" in e for e in errors), errors
    assert not any("ADR-001.md" in e for e in errors)


def test_lint_reports_a_missing_database(db_project):
    errors: list[str] = []
    lint.check_backend(errors)
    assert errors and "record.sqlite" in errors[0]
    decision(db_project, 1, "Active")
    errors.clear()
    lint.check_backend(errors)
    assert errors == []


def test_lint_reports_a_row_no_source_directory_claims(db_project):
    decision(db_project, 1, "Active")
    with sqlite3.connect(db_project / "record.sqlite") as conn:
        conn.execute("INSERT INTO sources (path, text, rev) VALUES "
                     "('notes/stray.md', 'x', 1)")
    errors: list[str] = []
    lint.check_backend(errors)
    assert errors and "notes/stray.md" in errors[0]


def test_index_renders_views_from_rows(db_project):
    decision(db_project, 1, "Active", title="From a row", summary="row one")
    rendered = adr_index.outputs()
    index = rendered[db_project / "docs" / "decisions" / "README.md"]
    assert "ADR-001" in index and "From a row" in index


def test_documents_cache_invalidates_on_a_row_write(db_project):
    decision(db_project, 1, "Active", title="First")
    scheme = current().schemes["ADR"]
    assert list(scheme.documents()) == [1]
    decision(db_project, 2, "Active", title="Second")
    assert list(scheme.documents()) == [1, 2]
    meta, _ = adr_index.read_document(scheme.documents()[2])
    assert meta["title"] == "Second"
    store.write_text(scheme.documents()[2],
                     store.read_text(scheme.documents()[2])
                     .replace("title: 'Second'", "title: 'Second, revised'"))
    meta, _ = adr_index.read_document(scheme.documents()[2])
    assert meta["title"] == "Second, revised"


def test_collect_orders_fragments_by_filing_order(db_project):
    """The changelog style reads newest-first within a batch, and "newest"
    is filing order — which on disk is the commit that added the file and
    in the database is the row's sequence, whatever the names sort like."""
    frag = db_project / "record" / "changelog.d"
    store.write_text(frag / "zzz.md", "### Added\n\n- filed first\n")
    store.write_text(frag / "aaa.md", "### Added\n\n- filed second\n")
    collect.run()
    text = (db_project / "CHANGELOG.md").read_text()
    assert text.index("filed second") < text.index("filed first")
    assert store.glob(frag, "*.md") == []          # consumed


def test_export_refreshes_derived_tables_in_place(db_project):
    decision(db_project, 1, "Active", title="Kept")
    db = db_project / "record.sqlite"
    export.write(db)
    assert rows(db, "SELECT code FROM documents") == [("ADR-001",)]
    assert rows(db, "SELECT path FROM sources") == [("record/decisions.d/ADR-001.md",)]
    decision(db_project, 2, "Active", title="Added later")
    export.write(db)
    assert rows(db, "SELECT code FROM documents ORDER BY code") == \
        [("ADR-001",), ("ADR-002",)]
    assert len(rows(db, "SELECT path FROM sources")) == 2
    assert store.read_text(db_project / "record" / "decisions.d" / "ADR-001.md")


def test_export_elsewhere_copies_the_sources(db_project):
    decision(db_project, 1, "Active")
    out = export.write(db_project / "build" / "copy.sqlite")
    assert rows(out, "SELECT path FROM sources") == [("record/decisions.d/ADR-001.md",)]
    assert rows(out, "SELECT code FROM documents") == [("ADR-001",)]


def test_export_markdown_writes_the_tree(db_project, capsys):
    decision(db_project, 1, "Active", title="On disk at last")
    export.run(markdown=True)
    written = db_project / "build" / "record" / "record" / "decisions.d" / "ADR-001.md"
    assert written.exists()
    assert "On disk at last" in written.read_text()
    assert "1 source written as files" in capsys.readouterr().out


def test_a_files_record_converts_by_export_then_config(tmp_path, monkeypatch):
    """The conversion story: export, point `backend` at the file, and the
    same documents answer from the database."""
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "luria.yaml").write_text(
        CONFIG.replace("backend:\n  kind: sqlite\n  file: record.sqlite\n", ""),
        encoding="utf-8")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    path = decision(tmp_path, 1, "Active", title="Born a file")
    assert path.exists()
    export.write(tmp_path / "record.sqlite")
    (tmp_path / "luria.yaml").write_text(CONFIG, encoding="utf-8")
    config.reset()
    assert current().backend.kind == "sqlite"
    docs = current().schemes["ADR"].documents()
    assert list(docs) == [1]
    meta, _ = adr_index.read_document(docs[1])
    assert meta["title"] == "Born a file"
    # The file that is still on disk is not what is being read.
    path.write_text("garbage")
    config.reset()
    meta, _ = adr_index.read_document(current().schemes["ADR"].documents()[1])
    assert meta["title"] == "Born a file"


def _copy_repo(dest: Path) -> None:
    for name in ("luria.yaml", "README.md", "CLAUDE.md", "CONTRIBUTING.md",
                 "CHANGELOG.md", "remotes.lock.json"):
        if (REPO / name).exists():
            shutil.copy(REPO / name, dest / name)
    shutil.copytree(REPO / "record", dest / "record")
    shutil.copytree(REPO / "docs", dest / "docs")
    shutil.copytree(REPO / "assets", dest / "assets")
    # Code globs and nested example records are read as files either way;
    # the equivalence is about the record, so they are left out and the
    # config told so.
    text = (dest / "luria.yaml").read_text(encoding="utf-8")
    text = text.replace("include_records:\n- examples/*\n", "")
    (dest / "luria.yaml").write_text(text, encoding="utf-8")


def test_this_record_reads_the_same_from_a_database(tmp_path, monkeypatch):
    """Luria's first consumer is Luria (ADR-009): converted to SQLite, this
    repository's record renders every view and reports every lint section
    identically — the one test that catches a module reading the disk for
    itself, because on the database side the disk is empty."""
    files = tmp_path / "files"
    files.mkdir()
    _copy_repo(files)
    monkeypatch.setenv("LURIA_ROOT", str(files))
    config.reset()
    views_from_files = {current().rel(p): t
                        for p, t in adr_index.outputs(nested=False).items()}
    sections_from_files = lint.status_sections()
    documents_from_files = {s.prefix: sorted(s.documents())
                            for s in current().schemes.values()}
    db = files / "record.sqlite"
    export.write(db)

    # The database is the record now: the source tree goes away entirely.
    shutil.rmtree(files / "record")
    text = (files / "luria.yaml").read_text(encoding="utf-8")
    (files / "luria.yaml").write_text(
        text + "backend:\n  kind: sqlite\n  file: record.sqlite\n",
        encoding="utf-8")
    config.reset()
    assert current().backend.kind == "sqlite"
    assert not (files / "record").exists()

    documents_from_db = {s.prefix: sorted(s.documents())
                         for s in current().schemes.values()}
    assert documents_from_db == documents_from_files
    assert documents_from_db["ADR"], "an empty record proves nothing"

    views_from_db = {current().rel(p): t
                     for p, t in adr_index.outputs(nested=False).items()}
    # The record page describes the config, and the config now differs by
    # exactly one row — `backend.kind` — which is the page doing its job.
    views_from_db.pop("docs/record.md")
    views_from_files.pop("docs/record.md")
    assert views_from_db == views_from_files

    sections_from_db = lint.status_sections()
    assert sections_from_db == sections_from_files

    errors: list[str] = []
    lint.check_backend(errors)
    assert errors == []
