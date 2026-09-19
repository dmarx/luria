# luria/store.py
"""Where the record's sources live, and the one door to them (#110).

Every module that reads or writes a source — a scheme document, a journal
entry, a fragment — does it through here, and nothing else in the package
opens a file for itself (a test holds that shape closed, the way
`test_one_reader` holds `read_document`). The package keeps addressing a
document by its path, `record/decisions.d/ADR-012.md`, because that path is
its identity everywhere downstream: in a finding's `path:line`, in a link's
filename, in the frame the fixer resolves a target from. What this module
decides is only where the bytes behind that path are kept.

Two backends, chosen by `backend.kind` in `luria.yaml`:

    backend:
      kind: files            # the default: one markdown file per entry
    backend:
      kind: sqlite           # the same documents, as rows in one database
      file: record.sqlite

Routing is by path. A path under a **source directory** — any scheme's
`dir`, any journal's, any fragment directory — goes to the configured
backend. Everything else (docs pages, generated views, code the reference
scan reads, `luria.yaml`, a staging directory) is a file on disk whichever
backend is configured, because none of it is the record. Under the SQLite
backend a file that happens to sit on disk inside a source directory is
ignored entirely: the database is the source, and two sources of truth is
the one thing a record must not have.

The SQLite backend stores each source as text, keyed by its path, with a
revision counter that stands in for the mtime the caches key on. The
document stays what it always was — markdown with YAML frontmatter — so
every reader, writer and check in the package works on it unchanged, the
markdown tree is a lossless export of the database, and the database is a
lossless import of the tree. `luria export` produces both directions.

The backend is *activated* by `config.current()` rather than looked up from
in here, for one reason: loading the config reads `luria.yaml` through this
module, and a module that asked the config where the config is would
recurse. Before anything is active, every path is a file.
"""

from __future__ import annotations

import fnmatch
import sqlite3
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

KINDS = ("files", "sqlite")

SOURCES_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,  -- filing order; never reused
    path  TEXT NOT NULL UNIQUE,   -- posix, relative to the record's root
    text  TEXT NOT NULL,          -- the document, frontmatter and all
    rev   INTEGER NOT NULL        -- bumped on every write; the caches' mtime
);
"""


# ── The SQLite backend ───────────────────────────────────────────────────


class SqliteStore:
    """Sources as rows. One connection per process, shared across the thread
    pool `parallel.pmap` runs — SQLite serialises on the lock, and the
    workloads here are point lookups."""

    def __init__(self, root: Path, file: Path):
        self.root = root
        self.file = file
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None

    def _db(self) -> sqlite3.Connection:
        """The connection, creating the database if it is not there. Only a
        write calls this: a read of a missing database is a missing record,
        which is a finding, not an empty one to invent (DP-1)."""
        if self._conn is None:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.file, check_same_thread=False,
                                   isolation_level=None)
            conn.executescript(SOURCES_SCHEMA)
            self._conn = conn
        return self._conn

    def _reading(self) -> sqlite3.Connection | None:
        if self._conn is None and not self.file.exists():
            return None
        return self._db()

    def present(self) -> bool:
        """Whether the database file exists at all."""
        return self._conn is not None or self.file.exists()

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def key(self, path: Path) -> str:
        """`path` relative to the root, posix; the root itself is ``""``."""
        path = Path(path)
        if path.is_absolute():
            path = path.relative_to(self.root)
        rel = path.as_posix()
        return "" if rel == "." else rel

    def _row(self, sql: str, *args):
        with self._lock:
            conn = self._reading()
            return conn.execute(sql, args).fetchone() if conn else None

    def _rows(self, sql: str, *args) -> list:
        with self._lock:
            conn = self._reading()
            return conn.execute(sql, args).fetchall() if conn else []

    def read(self, path: Path) -> str:
        row = self._row("SELECT text FROM sources WHERE path = ?", self.key(path))
        if row is None:
            raise FileNotFoundError(f"{path} is not in {self.file}")
        return row[0]

    def write(self, path: Path, text: str) -> None:
        with self._lock:
            self._db().execute(
                "INSERT INTO sources (path, text, rev) VALUES (?, ?, 1) "
                "ON CONFLICT(path) DO UPDATE SET text = excluded.text, "
                "rev = sources.rev + 1", (self.key(path), text))

    def delete(self, path: Path) -> None:
        with self._lock:
            done = self._db().execute("DELETE FROM sources WHERE path = ?",
                                      (self.key(path),)).rowcount
        if not done:
            raise FileNotFoundError(f"{path} is not in {self.file}")

    def move(self, src: Path, dst: Path) -> None:
        with self._lock:
            done = self._db().execute(
                "UPDATE sources SET path = ?, rev = rev + 1 WHERE path = ?",
                (self.key(dst), self.key(src))).rowcount
        if not done:
            raise FileNotFoundError(f"{src} is not in {self.file}")

    def is_file(self, path: Path) -> bool:
        return self._row("SELECT 1 FROM sources WHERE path = ?",
                         self.key(path)) is not None

    def is_dir(self, path: Path) -> bool:
        prefix = self.key(path)
        return self._row("SELECT 1 FROM sources WHERE path LIKE ? ESCAPE '\\' LIMIT 1",
                         _like(prefix)) is not None

    def paths(self, under: Path | None = None) -> list[Path]:
        """Every source path, absolute, sorted — optionally only those under
        one directory."""
        if under is None or not self.key(under):
            rows = self._rows("SELECT path FROM sources ORDER BY path")
        else:
            rows = self._rows("SELECT path FROM sources WHERE path LIKE ? ESCAPE '\\' "
                              "ORDER BY path", _like(self.key(under)))
        return [self.root / r[0] for r in rows]

    def revision(self, path: Path) -> tuple | None:
        row = self._row("SELECT rev, length(text) FROM sources WHERE path = ?",
                        self.key(path))
        if row is not None:
            return (int(row[0]), int(row[1]))
        # A directory's revision moves when the SET of rows under it does —
        # the bargain the file backend's directory mtime offers. Two sets
        # with the same count and the same highest id are the same set,
        # because an id is never reused (AUTOINCREMENT); `(count, max rev)`
        # was not enough, since add-then-delete lands back on the same key
        # with a different member. The rev sum moves it on rewrites too.
        found = self._row(
            "SELECT count(*), COALESCE(MAX(id), 0), COALESCE(SUM(rev), 0) "
            "FROM sources WHERE path LIKE ? ESCAPE '\\'",
            _like(self.key(path)))
        if not found or not found[0]:
            return None
        return tuple(int(x) for x in found)

    def added(self, path: Path) -> int | None:
        row = self._row("SELECT id FROM sources WHERE path = ?",
                        self.key(path))
        return int(row[0]) if row else None


def _like(prefix: str) -> str:
    """The LIKE pattern for "under this directory". `_` and `%` in a path are
    escaped so a directory named `a_b` does not match `axb`; the root
    (an empty prefix) is everything."""
    if not prefix:
        return "%"
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped + "/%"


# ── Activation: which backend, and which paths are the record's ──────────


@dataclass(frozen=True)
class Active:
    root: Path
    kind: str
    dirs: tuple[Path, ...]              # the source directories
    sqlite: SqliteStore | None


_ACTIVE: Active | None = None
_OPEN: dict[Path, SqliteStore] = {}
_ACTIVATING = threading.local()


def _ensure() -> Active | None:
    """The active backend, loading the config to find it if nothing has.

    Every command calls `config.current()` early, but "every" is a
    promise the first test to write before reading would break, and a
    write that missed the backend lands on disk where the record is not.
    So the door activates itself. Loading the config reads `luria.yaml`
    back through this module; the flag makes that nested call see no
    backend and read the file, instead of recursing into a load that is
    already underway."""
    if _ACTIVE is None and not getattr(_ACTIVATING, "busy", False):
        _ACTIVATING.busy = True
        try:
            from .config import current
            current()
        except Exception:               # no config to be had: files, then
            pass
        finally:
            _ACTIVATING.busy = False
    return _ACTIVE


def activate(cfg) -> None:
    """Route the record's source paths to `cfg.backend`. Called by
    `config.current()` once per loaded config; `deactivate` by `reset`."""
    global _ACTIVE
    dirs = tuple([s.dir for s in cfg.schemes.values()]
                 + [j.dir for j in cfg.journals.values()]
                 + [cfg.root / d for d in cfg.fragments])
    backend = cfg.backend
    sqlite = None
    if backend.kind == "sqlite":
        file = Path(backend.file)
        sqlite = _OPEN.get(file)
        if sqlite is None or sqlite.root != cfg.root:
            sqlite = _OPEN[file] = SqliteStore(cfg.root, file)
    _ACTIVE = Active(cfg.root, backend.kind, dirs, sqlite)


def deactivate() -> None:
    """Forget the backend and close its connections — for tests that point
    `LURIA_ROOT` somewhere else, and for a database deleted underneath."""
    global _ACTIVE
    _ACTIVE = None
    for open_store in _OPEN.values():
        open_store.close()
    _OPEN.clear()


def active() -> Active | None:
    return _ACTIVE


def is_source(path: Path) -> bool:
    """Whether `path` is the record's — under a scheme, journal or fragment
    directory of the active config, or one of those directories itself."""
    if _ensure() is None:
        return False
    path = Path(path)
    if not path.is_absolute():
        path = _ACTIVE.root / path
    return any(d == path or d in path.parents for d in _ACTIVE.dirs)


def source_dirs() -> tuple[Path, ...]:
    live = _ensure()
    return live.dirs if live else ()


def _sqlite_for(path: Path) -> SqliteStore | None:
    """The SQLite store when `path` is a source and that is the backend."""
    live = _ensure()
    if live is None or live.sqlite is None:
        return None
    return live.sqlite if is_source(path) else None


# ── The door ─────────────────────────────────────────────────────────────


def read_text(path: Path) -> str:
    """The text at `path`, wherever it lives. Raises `FileNotFoundError`
    (an `OSError`) for a path the store does not have, like a file would."""
    if (db := _sqlite_for(path)) is not None:
        return db.read(path)
    return Path(path).read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """Write `text` at `path`, wherever that lives. A file's directory is
    made on the way, so a writer never has to — and never leaves an empty
    source directory on disk beside a database that holds the record."""
    if (db := _sqlite_for(path)) is not None:
        db.write(path, text)
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def unlink(path: Path) -> None:
    if (db := _sqlite_for(path)) is not None:
        db.delete(path)
        return
    Path(path).unlink()


def move(src: Path, dst: Path) -> None:
    """Rename a source. Across the boundary — a source becoming a file or a
    file becoming a source — it is a read, a write and a delete."""
    db_src, db_dst = _sqlite_for(src), _sqlite_for(dst)
    if db_src is not None and db_src is db_dst:
        db_src.move(src, dst)
        return
    if db_src is None and db_dst is None:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(src).rename(dst)
        return
    text = read_text(src)
    if db_dst is None:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
    write_text(dst, text)
    unlink(src)


def exists(path: Path) -> bool:
    if (db := _sqlite_for(path)) is not None:
        return db.is_file(path) or db.is_dir(path) or Path(path) in _ACTIVE.dirs
    return Path(path).exists()


def is_file(path: Path) -> bool:
    if (db := _sqlite_for(path)) is not None:
        return db.is_file(path)
    return Path(path).is_file()


def is_dir(path: Path) -> bool:
    if (db := _sqlite_for(path)) is not None:
        return db.is_dir(path) or Path(path) in _ACTIVE.dirs
    return Path(path).is_dir()


def revision(path: Path) -> tuple | None:
    """A value that changes whenever the content at `path` does — the cache
    key every reader keys on. None when there is nothing there."""
    if (db := _sqlite_for(path)) is not None:
        return db.revision(path)
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def _segments_match(rel: Path, pattern: str) -> bool:
    """`Path.glob` semantics: one pattern segment per path segment, `*`
    never crossing a `/`."""
    parts = pattern.split("/")
    if len(rel.parts) != len(parts):
        return False
    return all(fnmatch.fnmatchcase(a, b) for a, b in zip(rel.parts, parts))


def _db_matches(base: Path, pattern: str, recursive: bool) -> list[Path]:
    db = _ACTIVE.sqlite
    base = Path(base)
    if not base.is_absolute():
        base = _ACTIVE.root / base
    out = []
    for path in db.paths(under=base):
        rel = path.relative_to(base)
        if not is_source(path):
            continue
        if recursive:
            if fnmatch.fnmatchcase(path.name, pattern):
                out.append(path)
        elif _segments_match(rel, pattern):
            out.append(path)
    return out


def glob(base: Path, pattern: str) -> list[Path]:
    """`sorted(base.glob(pattern))`, over both worlds: the files on disk
    that are not the record's, and the record's sources wherever they live."""
    live = _ensure()
    routed = live is not None and live.sqlite is not None
    found = [p for p in Path(base).glob(pattern)
             if not routed or not is_source(p)]
    if routed:
        found += _db_matches(base, pattern, recursive=False)
    return sorted(set(found))


def rglob(base: Path, pattern: str) -> list[Path]:
    """`sorted(base.rglob(pattern))`, over both worlds."""
    live = _ensure()
    routed = live is not None and live.sqlite is not None
    found = [p for p in Path(base).rglob(pattern)
             if not routed or not is_source(p)]
    if routed:
        found += _db_matches(base, pattern, recursive=True)
    return sorted(set(found))


def iterdir(base: Path) -> list[Path]:
    """`sorted(base.iterdir())`: files and directories one level down."""
    return glob(base, "*")


def added_order(path: Path) -> tuple[int, str]:
    """Sort key: when `path` entered the record, then its name.

    On disk that is the commit that added it; an uncommitted file sorts
    last, because locally the entry you just wrote is the newest thing in
    the batch. In the database it is the row's filing sequence."""
    if (db := _sqlite_for(path)) is not None:
        added = db.added(path)
        return (added if added is not None else sys.maxsize, Path(path).name)
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%ct", "-1", "--",
             str(path)],
            cwd=_ensure().root if _ensure() else Path(path).parent,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return (int(out), Path(path).name)
    except (subprocess.CalledProcessError, ValueError, OSError):
        pass
    return (sys.maxsize, Path(path).name)


def sources() -> list[Path]:
    """Every source the record holds, absolute and sorted: each file under
    each source directory, wherever the backend keeps it. Templates and
    stubs included — under the SQLite backend they live there too."""
    out: list[Path] = []
    for d in source_dirs():
        out += [p for p in rglob(d, "*") if is_file(p)]
    return sorted(set(out))


# ── Files, unrouted ──────────────────────────────────────────────────────
#
# For the few things that are never the record's and may be read before any
# config exists: `luria.yaml` itself, and the scaffold the package ships.


def read_file(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_file(path: Path, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")
