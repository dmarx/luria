# luria/edges.py
"""Typed edges, derived from what the record already says.

The citation graph has one kind of edge: A mentions B, found in prose. Three
facts in the record are stronger than a mention, and each was already
written down before this module read it as an edge:

    A ──source─────────→ B     any field a scheme declares a reference (ADR-060)
    A ──influenced_by──→ B     the `influenced_by:` list (ADR-012)
    A ──superseded_by──→ B     derived: status `Superseded`, note `by B`

Three levels of claim, and only the top two are edges. A code in prose is
a *mention* — the citation graph, found by scanning, and not this module's
business. A typed reference field is a *named relation*: the field name is
the relation, and the schema vouches for it. A recognised construction in
prose is a *derived relation*: `Superseded — by CODE` has a writer (`luria
migrate --strategy supersede`, ADR-040) and one meaning, so the code in
that position is the successor. Any other code in a status note — what a
Deferred was parked by, what a Rejected was overturned by — is a mention
with a location, not a relation; an earlier draft here named it one and a
reviewer caught it. It becomes an ordinary citation once the note is read
as the prose it is, which is a separate decision (#141).

The derivation reads `status_note:`, a prose field. There is no
`superseded_by:` field to author: the note already names the successor,
and a relation the tool derives from one authored fact beats a second
authored fact the tool would have to reconcile with the first.

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

# The canonical succession: the note opens with `by` and then the code —
# the shape `luria migrate --strategy supersede` writes (ADR-040).
_BY_RE = re.compile(r"^by\s+")


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    # Where the fact was read from, for a reader asking why the edge exists.
    because: str


def successor(doc: Adr) -> str | None:
    """The code a canonical `Superseded — by CODE` note names, or None.

    The one derived relation. It needs the status to be `Superseded` and
    the note to open with `by` and a local code, and it reads nothing else
    out of the note: a second code, or a code in a Deferred or Rejected
    note, is a mention, and mentions are the citation scanner's business.
    The note is read the way prose is read everywhere else — links
    unwrapped, then the scheme-driven finder (ADR-046) — so a linked or a
    bare code both count and a remote code never does."""
    if doc.status_value != "Superseded" or not doc.status_note:
        return None
    plain = doc_refs.UNLINK_RE.sub(r"\1", doc.status_note).strip()
    opening = _BY_RE.match(plain)
    if not opening:
        return None
    refs = [r for r in doc_refs.find_refs(plain) if r.kind == "scheme"]
    if not refs or refs[0].start != opening.end():
        return None
    code = refs[0].describe()
    return None if code == doc.code else code


def outbound(doc: Adr) -> list[Edge]:
    """Every typed edge this document is the source of."""
    out: list[Edge] = []
    if code := successor(doc):
        out.append(Edge(doc.code, SUPERSEDED_BY, code, "the `status:` note"))
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
