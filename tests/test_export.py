# tests/test_export.py
"""`luria export` writes the record as a SQLite database (#110).

The database is a *view* — generated from the sources, rebuilt from scratch
on every run, never a place anything is written back to. These tests hold
that contract: one row per document as the record reads it, lists exploded
so a value is a thing SQL can ask about, the typed edges and the citation
scan alongside, and a refusal to overwrite a file the command did not make.
"""
import json
import sqlite3
from pathlib import Path

import pytest

from luria import config, export
from luria.config import current

from _scheme import decision

# unresolved-ok-file: ADR-918, ADR-919 — fixture codes, deliberately not
# real: the citations test checks that they land in the table as unresolved.


def rows(db: Path, sql: str) -> list[tuple]:
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchall()


def test_one_row_per_document_as_the_record_reads_it(project):
    decision(project, 1, "Active", title="First", summary="one")
    decision(project, 2, "Superseded", title="Second", superseded_by="ADR-001")
    out = export.write(project / "build" / "record.sqlite")
    got = rows(out, "SELECT code, scheme, number, title, status, version, path "
                    "FROM documents ORDER BY code")
    assert got == [("ADR-001", "ADR", 1, "First", "Active", 1,
                    "record/decisions.d/ADR-001.md"),
                   ("ADR-002", "ADR", 2, "Second", "Superseded", 1,
                    "record/decisions.d/ADR-002.md")]


def test_frontmatter_is_kept_whole_as_json(project):
    decision(project, 1, "Active", title="First", summary="a summary")
    out = export.write(project / "record.sqlite")
    (frontmatter,), = rows(out, "SELECT frontmatter FROM documents")
    meta = json.loads(frontmatter)
    assert meta["title"] == "First"
    assert meta["summary"] == "a summary"
    assert meta["tags"] == ["record"]


def test_the_body_is_the_text_after_the_frontmatter(project):
    decision(project, 1, "Active", title="First")
    out = export.write(project / "record.sqlite")
    (body,), = rows(out, "SELECT body FROM documents")
    assert body.lstrip().startswith("# ADR-001: First")
    assert "---" not in body


def test_list_fields_explode_into_one_row_per_value(project):
    path = decision(project, 1, "Active")
    path.write_text(path.read_text().replace("tags:\n- record\n",
                                             "tags:\n- record\n- mechanism\n"))
    out = export.write(project / "record.sqlite")
    got = rows(out, "SELECT field, position, value FROM fields "
                    "WHERE code = 'ADR-001' AND field IN ('tags', 'title') "
                    "ORDER BY field, position")
    assert got == [("tags", 0, "record"), ("tags", 1, "mechanism"),
                   ("title", 0, "A decision")]


def test_the_typed_edges_are_exported(project):
    decision(project, 1, "Active")
    decision(project, 2, "Superseded", superseded_by="ADR-001")
    out = export.write(project / "record.sqlite")
    assert rows(out, "SELECT source, relation, target FROM edges") == \
        [("ADR-002", "superseded_by", "ADR-001")]


def test_citations_come_from_the_record_s_own_scanner(project):
    """A code in prose is a citation only where the lint says it is: a
    resolving one and a dangling one both land, told apart by `resolves`,
    and a mention in backticks is not a citation at all (ADR-105)."""
    decision(project, 1, "Active")
    (project / "docs" / "notes.md").write_text(
        "# Notes\n\nPer ADR-001, and see ADR-919. Not `ADR-001` in code.\n"
        "\n<!-- unresolved-ok: ADR-918 — a code kept on purpose -->\n"
        "And ADR-918, acknowledged.\n")
    out = export.write(project / "record.sqlite")
    got = rows(out, "SELECT path, line, code, resolves, excused FROM citations "
                    "WHERE path = 'docs/notes.md' ORDER BY code")
    assert got == [("docs/notes.md", 3, "ADR-001", 1, 0),
                   ("docs/notes.md", 6, "ADR-918", 0, 1),
                   ("docs/notes.md", 3, "ADR-919", 0, 0)]


def test_journal_entries_are_exported(tmp_path, monkeypatch):
    (tmp_path / "luria.yaml").write_text(
        "issue_url: https://example.test/{n}\n"
        "schemes:\n  ADR:\n    dir: record/decisions.d\n"
        "    output: docs/decisions\n"
        "journals:\n  devlog:\n    dir: record/devlog.d\n"
        "    output: docs/devlog\n    granularity: month\n",
        encoding="utf-8")
    entry = tmp_path / "record" / "devlog.d" / "2026" / "01" / "02" / "030405.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("---\ntitle: 'What happened'\ncreated: '2026-01-02T03:04:05'\n"
                     "tags: [record, process]\n---\n\nThe story.\n",
                     encoding="utf-8")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    out = export.write(tmp_path / "record.sqlite")
    assert rows(out, "SELECT journal, created, title, path, body "
                     "FROM journal_entries") == \
        [("devlog", "2026-01-02T03:04:05", "What happened",
          "record/devlog.d/2026/01/02/030405.md", "The story.")]
    assert rows(out, "SELECT tag FROM journal_tags ORDER BY tag") == \
        [("process",), ("record",)]


def test_rebuilt_from_scratch_every_run(project):
    """A view holds what the sources say now — a document deleted between two
    runs must not survive as a row."""
    decision(project, 1, "Active")
    gone = decision(project, 2, "Active")
    out = export.write(project / "record.sqlite")
    assert len(rows(out, "SELECT code FROM documents")) == 2
    gone.unlink()
    config.reset()
    export.write(out)
    assert rows(out, "SELECT code FROM documents") == [("ADR-001",)]


def test_refuses_to_overwrite_a_file_it_did_not_write(project):
    """Rebuilding means deleting, and deleting is only safe for a file this
    command made. Anything else at the path is reported, not replaced (DP-1)."""
    decision(project, 1, "Active")
    out = project / "record.sqlite"
    out.write_text("not a database\n")
    with pytest.raises(SystemExit) as caught:
        export.write(out)
    assert "not a SQLite database" in str(caught.value)
    assert out.read_text() == "not a database\n"


def test_records_what_made_it(project):
    decision(project, 1, "Active")
    out = export.write(project / "record.sqlite")
    keys = {k for (k,) in rows(out, "SELECT key FROM meta")}
    assert {"luria", "exported_at", "root"} <= keys


def test_run_reports_what_it_wrote(project, capsys):
    decision(project, 1, "Active")
    export.run(out="build/record.sqlite")
    printed = capsys.readouterr().out
    assert "exported build/record.sqlite" in printed
    assert "1 document" in printed


def test_the_command_is_registered():
    from luria import cli
    assert cli.COMMANDS["export"] is export.run


def test_exports_this_record(tmp_path):
    """Luria's first consumer is Luria (ADR-009): the export of the real
    corpus carries every scheme document the config sees, and its edges."""
    cfg = current()
    out = export.write(tmp_path / "record.sqlite")
    expected = sum(len(s.documents()) + len(s.temp_documents())
                   for s in cfg.schemes.values())
    (count,), = rows(out, "SELECT count(*) FROM documents")
    assert count == expected > 100
    (edge_count,), = rows(out, "SELECT count(*) FROM edges")
    assert edge_count > 0
    (entries,), = rows(out, "SELECT count(*) FROM journal_entries")
    assert entries > 0
