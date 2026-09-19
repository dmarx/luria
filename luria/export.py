# luria/export.py
"""The record as a database, and the database as a record (#110).

    luria export                       # a SQLite file, for querying
    luria export --out record.sqlite   # …somewhere in particular
    luria export --markdown            # the sources, as a markdown tree

A record's sources live either as files or as rows (`backend` in
`luria.yaml`; `luria/store.py`). This command converts between the two, and
in the same file writes the tables a reader queries.

The SQLite file holds two kinds of table. **`sources`** is the record: one
row per source, its text as written, and the only table the SQLite backend
reads. Under the files backend it is a copy of the tree; point `backend` at
the file and it *is* the record. Everything else is **derived** — rebuilt
from the sources on every export and never written back to:

    documents        one row per scheme document — code, scheme, number,
                     title, status, version, date, path, the whole
                     frontmatter as JSON, and the body
    fields           one row per value: a list field explodes into one row
                     per element, positioned, so `WHERE field = 'tags' AND
                     value = 'record'` is a question SQL can answer
    edges            the typed graph `luria/edges.py` derives — a reference
                     field, `superseded_by:`, `influenced_by:`
    citations        every code the lint's scanner counts as a citation, with
                     the file and line it sits on, whether it resolves, and
                     whether a directive excuses it — a suppression is
                     counted, never hidden (DP-1)
    journal_entries  one row per entry, keyed on the timestamp that is its
                     identity; `journal_tags` holds their tags
    meta             which version of luria wrote it, when, and from where

Under the SQLite backend the default `--out` is the record's own database,
and there the export refreshes the derived tables in place — `sources`
untouched, the way `luria index` rewrites views and never a source. Any
other `--out` gets a fresh file: sources copied, derived tables built. A
file at `--out` that is not a SQLite database is reported and left alone.

`--markdown` goes the other way: every source written as a file at its own
path under `--out` (default `build/record`), which is the tree a files
backend would read. Under the files backend that is a copy; under SQLite it
is the markdown corpus as an artifact of the database.

Every derived row comes through the record's own readers — `load_scheme`
for a document, `edges.graph` for a relation, `ref_status.scan` for a
citation — rather than a second parse of the sources. That is the same
rule the site follows (DP-4): a mention in backticks is not a citation here
for exactly the reason it is not one in the lint, and a derived field
arrives as an ordinary field for the reason it does everywhere else.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from . import __version__, edges, journal, ref_status, store
from .adr_index import load_scheme, read_document
from .config import current

SQLITE_MAGIC = b"SQLite format 3\x00"

DERIVED = ("documents", "fields", "edges", "citations", "journal_entries",
           "journal_tags", "meta")

DERIVED_SCHEMA = """
CREATE TABLE documents (
    code        TEXT PRIMARY KEY,
    scheme      TEXT NOT NULL,
    number      INTEGER,            -- NULL for a temporary code (ADR-049)
    title       TEXT NOT NULL,
    status      TEXT NOT NULL,
    version     INTEGER NOT NULL,
    date        TEXT,
    path        TEXT NOT NULL,      -- relative to the record's root
    frontmatter TEXT NOT NULL,      -- JSON, every field as the record reads it
    body        TEXT NOT NULL
);
CREATE TABLE fields (
    code     TEXT NOT NULL REFERENCES documents(code),
    field    TEXT NOT NULL,
    position INTEGER NOT NULL,      -- 0 for a scalar; the index in a list
    value    TEXT NOT NULL
);
CREATE INDEX fields_by_field ON fields(field, value);
CREATE TABLE edges (
    source   TEXT NOT NULL,
    relation TEXT NOT NULL,
    target   TEXT NOT NULL,
    because  TEXT NOT NULL
);
CREATE TABLE citations (
    path     TEXT NOT NULL,
    line     INTEGER NOT NULL,
    code     TEXT NOT NULL,
    resolves INTEGER NOT NULL,      -- 0 when the code names no document here
    excused  INTEGER NOT NULL       -- 1 when a directive acknowledges it
);
CREATE INDEX citations_by_code ON citations(code);
CREATE TABLE journal_entries (
    journal TEXT NOT NULL,
    created TEXT NOT NULL,          -- ISO 8601; the entry's identity
    title   TEXT NOT NULL,
    path    TEXT NOT NULL,
    body    TEXT NOT NULL,
    PRIMARY KEY (journal, created)
);
CREATE TABLE journal_tags (
    journal TEXT NOT NULL,
    created TEXT NOT NULL,
    tag     TEXT NOT NULL
);
CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

TABLES = ("sources",) + DERIVED[:-1]


def _text(value) -> str:
    """One cell's worth of a frontmatter value. Scalars as they print; a
    mapping or a nested list as JSON, so nothing is dropped and nothing is
    guessed at."""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=str, ensure_ascii=False)
    return str(value)


def _field_rows(code: str, meta: dict) -> list[tuple]:
    rows: list[tuple] = []
    for name, value in meta.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            rows += [(code, name, i, _text(v)) for i, v in enumerate(value)
                     if v is not None]
        else:
            rows.append((code, name, 0, _text(value)))
    return rows


def _document_rows(cfg) -> tuple[list[tuple], list[tuple]]:
    docs: list[tuple] = []
    fields: list[tuple] = []
    for scheme in cfg.schemes.values():
        for adr in load_scheme(scheme):
            _, body = read_document(adr.path)
            date = adr.meta.get("date")
            docs.append((adr.code, scheme.prefix, adr.number, adr.title,
                         adr.status_value, adr.version,
                         str(date) if date is not None else None,
                         cfg.rel(adr.path),
                         json.dumps(adr.meta, default=str, ensure_ascii=False),
                         body))
            fields += _field_rows(adr.code, adr.meta)
    return docs, fields


def _citation_rows(cfg) -> list[tuple]:
    scan = ref_status.scan()
    rows: list[tuple] = []
    for pool, resolves in ((scan.cited, 1), (scan.dangling, 0)):
        for code, sites in pool.items():
            rows += [(cfg.rel(c.path), c.line, code, resolves,
                      int(c.excused_by is not None)) for c in sites]
    return sorted(rows)


def _journal_rows(cfg) -> tuple[list[tuple], list[tuple]]:
    entries: list[tuple] = []
    tags: list[tuple] = []
    for name, jrnl in cfg.journals.items():
        for entry in journal.entries(jrnl):
            created = entry.created.isoformat()
            entries.append((name, created, entry.title, cfg.rel(entry.path),
                            entry.body))
            tags += [(name, created, tag) for tag in entry.tags]
    return entries, tags


def _source_rows(cfg) -> list[tuple]:
    """Every source, in filing order, as `sources` rows."""
    paths = sorted(store.sources(), key=store.added_order)
    return [(cfg.rel(p), store.read_text(p), 1) for p in paths]


def _is_sqlite(path: Path) -> bool:
    with open(path, "rb") as handle:
        return handle.read(len(SQLITE_MAGIC)) == SQLITE_MAGIC


def _clear(out: Path) -> None:
    """Make room for a fresh database — and only where one already was.

    Rebuilding means deleting, and deleting is safe only for a file this
    command made. A path holding anything else is reported and left alone
    rather than replaced (DP-1): a typo in `--out` should cost a message,
    not a file."""
    if not store.exists(out):
        return
    if not _is_sqlite(out):
        raise SystemExit(f"luria export: {out} exists and is not a SQLite "
                         "database — choose another --out, or move it aside")
    store.unlink(out)


def in_place(out: Path, cfg=None) -> bool:
    """Whether `out` is the record's own database, under the SQLite backend."""
    cfg = cfg or current()
    return (cfg.backend.kind == "sqlite"
            and Path(out).resolve() == Path(cfg.backend.file).resolve())


def _write_derived(conn: sqlite3.Connection, cfg) -> None:
    docs, fields = _document_rows(cfg)
    entries, tags = _journal_rows(cfg)
    graph = edges.graph()
    citations = _citation_rows(cfg)
    for table in DERIVED:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(DERIVED_SCHEMA)
    conn.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)", docs)
    conn.executemany("INSERT INTO fields VALUES (?,?,?,?)", fields)
    conn.executemany("INSERT INTO edges VALUES (?,?,?,?)",
                     [(e.source, e.relation, e.target, e.because)
                      for e in graph.edges])
    conn.executemany("INSERT INTO citations VALUES (?,?,?,?,?)", citations)
    conn.executemany("INSERT INTO journal_entries VALUES (?,?,?,?,?)", entries)
    conn.executemany("INSERT INTO journal_tags VALUES (?,?,?)", tags)
    conn.executemany("INSERT INTO meta VALUES (?,?)", [
        ("luria", __version__),
        ("exported_at", dt.datetime.now(dt.timezone.utc)
                          .replace(microsecond=0).isoformat()),
        ("root", str(cfg.root)),
        ("backend", cfg.backend.kind),
    ])


def write(out: Path, cfg=None) -> Path:
    """Write the record to `out` as a SQLite database.

    The record's own database (SQLite backend, `out` naming it) has its
    derived tables refreshed in place and its sources left alone. Anywhere
    else is written from scratch: sources copied, derived tables built.
    Returns the path written."""
    cfg = cfg or current()
    out = Path(out)
    if in_place(out, cfg):
        with closing(sqlite3.connect(out)) as conn:
            _write_derived(conn, cfg)
            conn.commit()
        return out
    sources = _source_rows(cfg)         # read before `out` is touched
    _clear(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(out)) as conn:
        conn.executescript(store.SOURCES_SCHEMA)
        conn.executemany("INSERT INTO sources (path, text, rev) VALUES (?,?,?)",
                         sources)
        _write_derived(conn, cfg)
        conn.commit()
    return out


def write_markdown(out: Path, cfg=None) -> list[Path]:
    """Write every source as a file at its own path under `out`. Returns
    the files written. Files already there are overwritten — the tree is
    an artifact of the record, and this is the command that makes it."""
    cfg = cfg or current()
    out = Path(out)
    written: list[Path] = []
    for path in store.sources():
        dest = out / cfg.rel(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        store.write_file(dest, store.read_text(path))
        written.append(dest)
    return written


def counts(db: Path) -> dict[str, int]:
    """Rows per table, for the report."""
    with closing(sqlite3.connect(db)) as conn:
        return {table: conn.execute(f"SELECT count(*) FROM {table}")
                                .fetchone()[0] for table in TABLES}


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def run(out: str | None = None, markdown: bool = False) -> None:
    """Write the record as a SQLite database at OUT — the sources, plus every
    document, field, typed edge, citation and journal entry as tables to
    query. Under the SQLite backend OUT defaults to the record's own
    database and only the derived tables are refreshed. --markdown instead
    writes every source as a file under OUT (default build/record)."""
    cfg = current()
    if markdown:
        out = out or "build/record"
        path = Path(out) if Path(out).is_absolute() else cfg.root / out
        written = write_markdown(path, cfg)
        print(f"exported {out}")
        print(f"  {_plural(len(written), 'source', 'sources')} written as files")
        return
    if out is None:
        out = (cfg.rel(cfg.backend.file) if cfg.backend.kind == "sqlite"
               else "build/record.sqlite")
    path = Path(out) if Path(out).is_absolute() else cfg.root / out
    write(path, cfg)
    print(f"exported {out}" + (" (derived tables refreshed in place)"
                               if in_place(path, cfg) else ""))
    got = counts(path)
    print("  " + ", ".join([
        _plural(got["sources"], "source", "sources"),
        _plural(got["documents"], "document", "documents"),
        _plural(got["fields"], "field value", "field values"),
        _plural(got["edges"], "edge", "edges"),
        _plural(got["citations"], "citation", "citations"),
        _plural(got["journal_entries"], "journal entry", "journal entries"),
    ]))


if __name__ == "__main__":
    sys.exit(run())
