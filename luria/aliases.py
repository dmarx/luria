"""Old spellings of moved documents, derived from `formerly:` (ADR-040).

A migrated document carries its past in its own frontmatter:

    formerly:
    - DP-4

That field is the *only* persistent bookkeeping a migration leaves in the
record — config describes the present, documents carry their pasts — and
this module is the projection: a map from every old spelling to the code
that answers for it now. Nothing here is hand-maintained; delete the field
and the alias is gone.

A reference written in an old spelling still resolves through this map, but
it draws a `legacy-spellings` warning (`luria lint`) and `luria link --fix`
rewrites it to the current code. That loop is what makes a migration safe
to land while branches are in flight: a branch written before the rename
merges clean, warns, and is modernized on its next `--fix`.
"""

from __future__ import annotations

import re

from .adr_index import parse_frontmatter
from .config import Config, current

CODE_RE = re.compile(r"^([A-Za-z]{2,10})[- ]0*(\d{1,4})$")

# Keyed on the Config instance: `config.reset()` mints a new one, so tests
# and long processes invalidate for free without a reset of their own.
_cache: tuple[Config, dict[str, str]] | None = None


def canon(code: str) -> str | None:
    """`dp-4`, `DP 4` and `DP-004` are one spelling: `DP-004`."""
    m = CODE_RE.match(code.strip())
    return f"{m.group(1).upper()}-{int(m.group(2)):03d}" if m else None


def alias_map(cfg: Config | None = None) -> dict[str, str]:
    """Canonical old code → canonical current code, across every scheme.

    Derived fresh from the documents (and cached per config): an alias that
    outlived its `formerly:` entry would be exactly the hand-kept ledger
    ADR-040 rejected."""
    global _cache
    cfg = cfg or current()
    if _cache is not None and _cache[0] is cfg:
        return _cache[1]
    out: dict[str, str] = {}
    for scheme in cfg.schemes.values():
        for number, path in scheme.documents().items():
            meta, _ = parse_frontmatter(path.read_text())
            for old in meta.get("formerly") or []:
                old_code = canon(str(old))
                if old_code is not None:
                    out[old_code] = scheme.code(number)
    _cache = (cfg, out)
    return out


def reset() -> None:
    """Drop the cache — for the migration executor, which edits the very
    frontmatter this map is derived from."""
    global _cache
    _cache = None


def split(code: str) -> tuple[str, int]:
    prefix, number = code.rsplit("-", 1)
    return prefix, int(number)
