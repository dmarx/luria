# luria/referents.py
"""The written frontmatter of a document named by a code (#233).

What a `from` derivation reads through. Small and separate for two reasons.

`derive` is pure — templates, no I/O, no config — which is what lets its rules
be tested against dictionaries. Following a reference is the opposite: it
needs the scheme table to find the directory and the disk to read the file. So
the resolution lives here and reaches `derive` as a callable, and neither
module grows the other's dependencies.

**Written frontmatter, never derived.** A referenced document is parsed and
handed over as it was typed. That is the one-hop rule from `derive`, enforced
where the reading happens: a derivation cannot see another derivation, so
there is no cycle to detect and no order in which schemes must be resolved.

**Cached per resolver, not globally.** A `Lookup` holds one run's readings.
The lint parses hundreds of documents and would otherwise re-read a
much-cited paper once per citing document; a module-level cache would instead
outlive the edit that invalidates it, which is the bug this shape avoids.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import current


@dataclass
class Lookup:
    """Code → that document's written frontmatter, read at most once each."""

    _seen: dict[str, dict] = field(default_factory=dict)

    def __call__(self, code: str) -> dict:
        """The frontmatter for `code`, or `{}` when it names no document.

        `{}` rather than an exception: a code that resolves to nothing is
        already the reference check's finding, and raising here would report
        one fault twice — on the line that cites it and on the line that
        derives from it."""
        if code in self._seen:
            return self._seen[code]
        self._seen[code] = meta = _read(code)
        return meta


def _read(code: str) -> dict:
    from .adr_index import parse_frontmatter
    path = path_of(code)
    if path is None:
        return {}
    try:
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return {}
    return meta or {}


def path_of(code: str) -> Path | None:
    """The file a local code names, or None — a remote, an unknown scheme, or
    a number no document carries.

    Temporary codes resolve too (ADR-049): a merge-allocated document is a
    real document that has not been numbered yet, and a derivation off one
    should not go blank until the merge that numbers it."""
    prefix, _, tail = str(code).strip().partition("-")
    scheme = current().schemes.get(prefix.upper())
    if scheme is None or not tail:
        return None
    if tail.isdigit():
        return scheme.documents().get(int(tail))
    return scheme.temp_documents().get(tail)
