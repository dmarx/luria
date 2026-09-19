# luria/export.py
"""The record as a database you can ask questions of (#110).

    luria export --out build/record.sqlite

writes one SQLite file holding every scheme document, every frontmatter
field, the typed edges, the citation scan and every journal entry. It is a
**view**: generated from the sources, rebuilt from scratch on each run, and
never a place anything is written back to. The sources stay one markdown
file per entry in git, because that is what makes a contribution reviewable,
mergeable and blameable — a database in the repository would be the shared
file DP-2 exists to abolish. What "store it in a database" actually buys is
being able to *ask* the record arbitrary questions, which ADR-111 named as
the thing a database is for, and a generated one answers that without
touching what the record is made of.

The shape is plain on purpose, so `sqlite3`, Datasette or a pandas call can
read it without a schema lesson:

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

Every row comes through the record's own readers — `load_scheme` for a
document, `edges.graph` for a relation, `ref_status.scan` for a citation —
rather than a second parse of the files. That is the same rule the site
follows (DP-4): a mention in backticks is not a citation here for exactly the
reason it is not one in the lint, and a derived field arrives as an ordinary
field for the reason it does everywhere else.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from . import __version__, edges, journal, ref_status
from .adr_index import load_scheme, read_document
from .config import current

SQLITE_MAGIC = b"SQLite format 3\x00"

SCHEMA = """
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

TABLES = ("documents", "fields", "edges", "citations", "journal_entries",
          "journal_tags")


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


def _clear(out: Path) -> None:
    """Make room for a fresh database — and only where one already was.

    Rebuilding means deleting, and deleting is safe only for a file this
    command made. A path holding anything else is reported and left alone
    rather than replaced (DP-1): a typo in `--out` should cost a message,
    not a file."""
    if not out.exists():
        return
    with out.open("rb") as handle:
        head = handle.read(len(SQLITE_MAGIC))
    if head != SQLITE_MAGIC:
        raise SystemExit(f"luria export: {out} exists and is not a SQLite "
                         "database — choose another --out, or move it aside")
    out.unlink()


def write(out: Path, cfg=None) -> Path:
    """Write the record to `out` as a SQLite database, from scratch.

    Returns the path written. The counts a caller might report are one
    `SELECT count(*)` away, which is the point of the format."""
    cfg = cfg or current()
    out = Path(out)
    _clear(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    docs, fields = _document_rows(cfg)
    entries, tags = _journal_rows(cfg)
    graph = edges.graph()
    with closing(sqlite3.connect(out)) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)",
                         docs)
        conn.executemany("INSERT INTO fields VALUES (?,?,?,?)", fields)
        conn.executemany("INSERT INTO edges VALUES (?,?,?,?)",
                         [(e.source, e.relation, e.target, e.because)
                          for e in graph.edges])
        conn.executemany("INSERT INTO citations VALUES (?,?,?,?,?)",
                         _citation_rows(cfg))
        conn.executemany("INSERT INTO journal_entries VALUES (?,?,?,?,?)",
                         entries)
        conn.executemany("INSERT INTO journal_tags VALUES (?,?,?)", tags)
        conn.executemany("INSERT INTO meta VALUES (?,?)", [
            ("luria", __version__),
            ("exported_at", dt.datetime.now(dt.timezone.utc)
                              .replace(microsecond=0).isoformat()),
            ("root", str(cfg.root)),
        ])
        conn.commit()
    return out


def counts(db: Path) -> dict[str, int]:
    """Rows per table, for the report."""
    with closing(sqlite3.connect(db)) as conn:
        return {table: conn.execute(f"SELECT count(*) FROM {table}")
                                .fetchone()[0] for table in TABLES}


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def run(out: str = "build/record.sqlite") -> None:
    """Write the record as a SQLite database at OUT — every document, field,
    typed edge, citation and journal entry — rebuilt from scratch, for
    querying; never a source."""
    cfg = current()
    path = Path(out) if Path(out).is_absolute() else cfg.root / out
    write(path, cfg)
    print(f"exported {out}")
    got = counts(path)
    print("  " + ", ".join([
        _plural(got["documents"], "document", "documents"),
        _plural(got["fields"], "field value", "field values"),
        _plural(got["edges"], "edge", "edges"),
        _plural(got["citations"], "citation", "citations"),
        _plural(got["journal_entries"], "journal entry", "journal entries"),
    ]))


if __name__ == "__main__":
    sys.exit(run())
