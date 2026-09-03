# luria/edges.py
"""Typed edges, derived from what the record already says.

The citation graph has one kind of edge: A mentions B, found in prose. Three
facts in the record are stronger than a mention, and each was already
written down before this module read it as an edge:

    A ──superseded_by──→ B     a `Superseded — by B` status note (ADR-003)
    A ──status_note────→ B     any other code a status note cites
    A ──influenced_by──→ B     the `influenced_by:` list (ADR-012)
    A ──source─────────→ B     any field a scheme declares a reference (ADR-060)

The field name is the relation. Nothing here is a new authoring surface:
`superseded_by:` as a frontmatter field beside the note that already says it
would be the second copy of one fact that DP-3 says will drift, so the edge
is read out of the note. That is a regex over prose, which ADR-003 chose
frontmatter to avoid — defensible here because the whole citation graph is
already codes found in prose, and `luria migrate` writes this exact note
shape mechanically (ADR-040).

Two relations, because the note says two kinds of thing. `Superseded — by
CODE` is a convention with a writer (the migration) and a single meaning,
so the code in that position is the successor. Every other code a status
note cites — a second one after the successor, what a Deferred was parked
by, what a Rejected was overturned by — is a fact the author wrote down
whose meaning the tool does not know. `status_note` keeps it as exactly
that: this note names that code, and no more (#141).

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
from .contract import for_scheme, reference_code, values_of

SUPERSEDED_BY = "superseded_by"
STATUS_NOTE = "status_note"
INFLUENCED_BY = "influenced_by"

# `Superseded — by …`: the bare word, then the note (ADR-003).
_NOTE_RE = re.compile(r"\s+—\s+")
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


def _note_edges(doc: Adr) -> list[Edge]:
    """What a status note says, as edges: the successor when the note has
    the canonical shape, and every other code as a bare mention.

    The note is prose, so it is read the way prose is read everywhere else:
    links unwrapped, then the scheme-driven finder (ADR-046). Issues and
    remote codes come back as other kinds and are dropped."""
    word, *rest = _NOTE_RE.split(doc.status, maxsplit=1)
    if not rest:
        return []
    plain = doc_refs.UNLINK_RE.sub(r"\1", rest[0]).strip()
    refs = [r for r in doc_refs.find_refs(plain) if r.kind == "scheme"]
    successor = None
    if word.strip() == "Superseded" and refs:
        opening = _BY_RE.match(plain)
        if opening and refs[0].start == opening.end():
            successor = refs[0].describe()
    out: list[Edge] = []
    seen: set[str] = set()
    for ref in refs:
        code = ref.describe()
        if code == doc.code or code in seen:
            continue
        seen.add(code)
        relation = SUPERSEDED_BY if code == successor else STATUS_NOTE
        out.append(Edge(doc.code, relation, code, "the `status:` note"))
    return out


def outbound(doc: Adr) -> list[Edge]:
    """Every typed edge this document is the source of."""
    out: list[Edge] = list(_note_edges(doc))
    for code in doc.influenced_by:
        out.append(Edge(doc.code, INFLUENCED_BY, code,
                        "frontmatter `influenced_by:`"))
    for field in for_scheme(doc.scheme).fields:
        if field.reference is None:
            continue
        # A value that is not a code of the declared scheme, or a list where
        # one code was declared, is the lint's to report (ADR-060); the
        # graph neither invents a node nor guesses which element was meant.
        for value in values_of(field, doc.meta.get(field.name)) or ():
            code = reference_code(str(value))
            if code and code.startswith(f"{field.reference}-"):
                out.append(Edge(doc.code, field.name, code,
                                f"frontmatter `{field.name}:`"))
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
