# luria/edges.py
"""Typed edges, derived from what the record already says.

The citation graph has one kind of edge: A mentions B, found in prose. Three
facts in the record are stronger than a mention, and each was already
written down before this module read it as an edge:

    A ──source─────────→ B     any field a scheme declares a reference (ADR-060)
    A ──superseded_by──→ B     the built-in `superseded_by:` field
    A ──influenced_by──→ B     the `influenced_by:` list (ADR-012)

Two levels of claim, and only the second is an edge. A code in prose is a
*mention* — the citation graph, found by scanning, and not this module's
business; a code in a status note is one of those. A reference field is a
*named relation*: the field name is the relation, and the schema vouches
for it. `superseded_by` is a reference field every scheme has, so a
succession is written as structure and read as structure. Two drafts here
inferred it from the `by CODE` shape of a status note instead, and were
corrected on review: a field is concrete and checkable, and inferring a
relation from free text is strictly weaker — it makes the author's prose
conform to a shape the tool happens to recognise. The old note shape is
read once more, by `luria index`, as the repair that fills the field.

Consumers: the site renders each page's edges both ways (#141). A remote
code is never an edge — the graph has no node for it to land on (ADR-016).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adr_index import Adr, load_scheme
from .config import current
from .contract import (ANY_SCHEME, for_scheme, is_remote, local_scheme,
                       reference_code)

SUPERSEDED_BY = "superseded_by"
INFLUENCED_BY = "influenced_by"


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    # Where the fact was read from, for a reader asking why the edge exists.
    because: str


def _lands(field, code: str) -> bool:
    """Whether a code is a node this graph has: a local document of the
    declared scheme, or of any scheme for a built-in reference. A remote
    code is a citation the remote machinery verifies, never an edge."""
    if field.reference == ANY_SCHEME:
        return not is_remote(code) and local_scheme(code) is not None
    return code.startswith(f"{field.reference}-")


def outbound(doc: Adr) -> list[Edge]:
    """Every typed edge this document is the source of."""
    out: list[Edge] = []
    for field in for_scheme(doc.scheme).fields:
        if field.reference is None:
            continue
        raw = doc.meta.get(field.name)
        values = raw if isinstance(raw, list) else [raw]
        # A value that is not a code of the declared scheme is the lint's to
        # report (ADR-060); the graph does not invent a node for it.
        for value in values:
            if value in (None, ""):
                continue
            code = reference_code(str(value))
            if code and code != doc.code and _lands(field, code):
                out.append(Edge(doc.code, field.name, code,
                                f"frontmatter `{field.name}:`"))
    for code in doc.influenced_by:
        out.append(Edge(doc.code, INFLUENCED_BY, code,
                        "frontmatter `influenced_by:`"))
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
