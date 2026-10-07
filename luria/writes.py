# luria/writes.py
"""Every write luria makes to the tree, through one door.

luria reads the record many times in one process, so it caches what it
reads: a document's parse (`adr_index`), a directory's listing and a file's
number (`config`), the corpus scan (`ref_status`) and the facts the logic
core reasons over (`facts`). Each of those is keyed on `stat` — mtime and
size — which is cheap, and right as long as a write moves one of them. A
rewrite that keeps the size inside one tick of a coarse clock moves
neither, and a fixer that writes and then reads back in the same process
(`luria link --fix`, `repair`, `migrate`) would read the old document.

So a write tells the caches, rather than hoping the clock does:
`write_text` and `unlink` do the write, then `wrote`, which drops what is
cached about that path and, when it is a scheme document, bumps the
generation that the corpus-wide caches are keyed on. A generated view is
not a scheme document, so `luria index` writing a few hundred of them
leaves the facts alone.

`tests/test_writes.py` holds every module in `luria/` to this door: a
`write_text` or `unlink` anywhere else is a write the caches never hear of.
"""
from __future__ import annotations

from pathlib import Path

_generation = 0


def generation() -> int:
    """How many scheme documents this process has written or removed. A
    cache over the whole record keys on this beside its stat fingerprint."""
    return _generation


def _is_document(path: Path) -> bool:
    """Whether `path` sits in a scheme's directory, asked of the config only
    when it is already loaded. A write must never be what loads it: `luria
    upgrade` rewrites a config that may not load until it has, and with no
    config loaded nothing is cached against one, so the answer that costs
    nothing — yes — is also the safe one."""
    from .config import current
    if current.cache_info().currsize == 0:
        return True
    dirs = {s.dir.resolve() for s in current().schemes.values()}
    return path.resolve().parent in dirs


def wrote(path: Path) -> None:
    """Forget what is cached about `path`, and about the record when `path`
    is one of its documents."""
    global _generation
    from . import adr_index, config
    # The caches key on the path as their caller spelled it, so both
    # spellings are dropped.
    for p in {path, path.resolve()}:
        adr_index._DOCUMENT_CACHE.pop(p, None)
        config._NUMBER_CACHE.pop(p, None)
        config._LISTING_CACHE.pop(p.parent, None)
    if _is_document(path):
        _generation += 1
        from . import ref_status
        ref_status.forget_scan()


def write_text(path: Path, text: str) -> None:
    """Write `text` to `path` as UTF-8, and say so."""
    path.write_text(text, encoding="utf-8")
    wrote(path)


def unlink(path: Path, missing_ok: bool = False) -> None:
    """Remove `path`, and say so."""
    path.unlink(missing_ok=missing_ok)
    wrote(path)
