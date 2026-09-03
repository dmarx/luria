# luria/edges.py
"""Typed edges, derived from what the record already says.

The citation graph has one kind of edge: A mentions B, found in prose. Three
facts in the record are stronger than a mention, and each was already
written down before this module read it as an edge:

    A ──superseded_by──→ B     the `Superseded — by B` status note (ADR-003)
    A ──influenced_by──→ B     the `influenced_by:` list (ADR-012)
    A ──source─────────→ B     any field a scheme declares a reference (ADR-060)

The field name is the relation. Nothing here is a new authoring surface:
`superseded_by:` as a frontmatter field beside the note that already says it
would be the second copy of one fact that DP-3 says will drift, so the edge
is read out of the note. That is a regex over prose, which ADR-003 chose
frontmatter to avoid — defensible here because the whole citation graph is
already codes found in prose, and `luria migrate` writes this exact note
shape mechanically (ADR-040). The note may cite more than one code, so the
edge is "the codes a Superseded note cites", not "the successor".

Consumers: the site renders each page's edges both ways (#141). A remote
code is never an edge — the graph has no node for it to land on (ADR-016).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import doc_refs
from .adr_index import Adr, load_scheme
from .config import current
from .contract import reference_code

SUPERSEDED_BY = "superseded_by"
INFLUENCED_BY = "influenced_by"

# `Superseded — by …`: the bare word, then the note (ADR-003).
_NOTE_RE = re.compile(r"\s+—\s+")


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    # Where the fact was read from, for a reader asking why the edge exists.
    because: str


def _codes_in(text: str) -> list[str]:
    """Local scheme codes cited in a note, linked or bare, in order.

    The note is prose, so it is read the way prose is read everywhere else:
    links unwrapped, then the scheme-driven finder (ADR-046). Issues and
    remote codes come back as other kinds and are dropped here."""
    plain = doc_refs.UNLINK_RE.sub(r"\1", text)
    return [ref.describe() for ref in doc_refs.find_refs(plain)
            if ref.kind == "scheme"]


def outbound(doc: Adr) -> list[Edge]:
    """Every typed edge this document is the source of."""
    out: list[Edge] = []
    word, *rest = _NOTE_RE.split(doc.status, maxsplit=1)
    if word.strip() == "Superseded" and rest:
        for code in _codes_in(rest[0]):
            if code != doc.code:
                out.append(Edge(doc.code, SUPERSEDED_BY, code,
                                "the `status:` note"))
    for code in doc.influenced_by:
        out.append(Edge(doc.code, INFLUENCED_BY, code,
                        "frontmatter `influenced_by:`"))
    for ref in doc.scheme.references:
        raw = doc.meta.get(ref.field)
        if not raw:
            continue
        # A value that is not a code of the declared scheme is the lint's to
        # report (ADR-060); the graph does not invent a node for it.
        code = reference_code(str(raw))
        if code and code.startswith(f"{ref.scheme}-"):
            out.append(Edge(doc.code, ref.field, code,
                            f"frontmatter `{ref.field}:`"))
    return out


@dataclass(frozen=True)
class Graph:
    edges: tuple[Edge, ...]

    def outbound(self, code: str) -> list[Edge]:
        return [e for e in self.edges if e.source == code]

    def inbound(self, code: str) -> list[Edge]:
        """The backlinks: every typed edge that lands on `code`."""
        return [e for e in self.edges if e.target == code]


def graph() -> Graph:
    """Every typed edge in the record, read once."""
    found: list[Edge] = []
    for scheme in current().schemes.values():
        for doc in load_scheme(scheme):
            found.extend(outbound(doc))
    return Graph(tuple(found))


def code_of(path: Path) -> str | None:
    """Which node a scheme document's file is, or None for anything else."""
    for scheme in current().schemes.values():
        if path.parent != scheme.dir:
            continue
        number = scheme.number_of(path)
        if number is not None:
            return scheme.code(number)
        if tail := scheme.temp_of(path):
            return f"{scheme.prefix}-{tail}"
    return None
