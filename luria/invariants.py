# luria/invariants.py
"""What a relation asserts, checked against what the fields say (#214).

A relation is an assertion that an invariant exists. `A extends B` claims the
two are steps in one thing; `A compared_against B` claims they are rivals for
one job. Either way the record has said these documents have something in
common — and if no field names that something, the record has not said *what*.

That is the finding. Its usual reading is not that the documents are
mis-related but that **the vocabulary is missing a word**: the relation was
easy to write because the author could see the commonality, and the tag list
was left alone because no existing value fitted.

Two findings, and they are genuinely two:

- **Unbound edge.** Two documents in a declared relation share no value in
  the invariant field. The strong case: one assertion, one pair, nothing
  named.
- **Unbound path.** A connected component whose members hold no value in
  common, even though every edge within it might. `A∩B = {x}`, `B∩C = {y}`,
  `A∩B∩C = ∅` — every step expressed, the line unexpressed.

Edge findings are a strict subset of path findings, and the containment is
why both are reported rather than one: the path check alone would bury the
sharp case among the diffuse ones, and the edge check alone would miss a line
that drifts a little at every step.

The path case is the weaker signal and is reported as such, because a
component's intersection **shrinks monotonically as the component grows**. One
distant member can unbind a chain that is locally coherent throughout, so the
reader has to look at the whole line to judge it. A report, never a failure.

**Nothing is checked unless a chain declares `invariant`.** That default is
load-bearing rather than cautious. Measured on the record this was built for,
running the check over `source:` — which joins a practice to its paper across
two vocabularies that a decision had deliberately separated — makes findings
of 48 of 235 edges, and every one of them is a cross-domain citation the
record was changed to permit. A check that fires on a project for doing the
thing it decided to do is worse than no check.

Cardinality decides what "shared" means, and it falls out rather than being
configured: a list-valued field is compared by non-empty intersection, a
single-valued one by equality — which is the same operation once a scalar is
read as a set of one.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import chains, relations
from .adr_index import Adr, load_scheme
from .config import Chain, current


@dataclass(frozen=True)
class Unbound:
    """One finding: the documents, and what each holds in the field."""
    chain: str
    field: str
    members: tuple[Adr, ...]

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(d.code for d in self.members)


def held(doc: Adr, field: str) -> set[str]:
    """The values a document holds in `field`, as a set.

    A scalar is a set of one, which is what lets equality and intersection be
    the same test — `status: Active` on both sides intersects to `{"Active"}`
    exactly when the two are equal."""
    raw = doc.meta.get(field)
    if raw in (None, ""):
        return set()
    values = raw if isinstance(raw, list) else [raw]
    return {str(v).strip() for v in values if v not in (None, "")}


def _neighbours(chain: Chain) -> dict[str, set[str]]:
    """Every undirected edge the chain walks — spine and cross-link alike.

    Read through `relations.edges`, which unions a relation with its declared
    converse, so a one-sided declaration is walked before the fixer has
    written the other half. A finding that waited for `luria link --fix` would
    be a finding about tidiness rather than about the record."""
    out: dict[str, set[str]] = {}
    fields = list(chain.relation) + ([chain.sibling] if chain.sibling else [])
    for field in fields:
        for code, targets in relations.edges(chain.scheme, field).items():
            for other in targets:
                out.setdefault(code, set()).add(other)
                out.setdefault(other, set()).add(code)
    return out


def _walk(chain: Chain) -> tuple[dict[str, Adr], dict[str, set[str]]]:
    docs = {d.code: d for d in load_scheme(current().schemes[chain.scheme])}
    near = {c: {o for o in v if o in docs}
            for c, v in _neighbours(chain).items() if c in docs}
    return docs, {c: near.get(c, set()) for c in docs}


def edges(chain: Chain) -> list[Unbound]:
    """Pairs in a declared relation that share no value in the field."""
    docs, near = _walk(chain)
    seen, out = set(), []
    for code in sorted(near):
        for other in sorted(near[code]):
            pair = tuple(sorted((code, other)))
            if pair in seen:
                continue
            seen.add(pair)
            a, b = docs[pair[0]], docs[pair[1]]
            if not (held(a, chain.invariant) & held(b, chain.invariant)):
                out.append(Unbound(chain.name, chain.invariant, (a, b)))
    return out


def paths(chain: Chain) -> list[Unbound]:
    """Components whose members hold no value in common.

    A one-member component is not a finding: a document alone in the graph
    asserts nothing about anything, so there is no invariance to express."""
    docs, near = _walk(chain)
    out = []
    for group in chains._components(sorted(docs), near):
        if len(group) < 2:
            continue
        members = tuple(docs[c] for c in group)
        common = set.intersection(*(held(d, chain.invariant) for d in members))
        if not common:
            out.append(Unbound(chain.name, chain.invariant, members))
    return out


def findings() -> tuple[list[Unbound], list[Unbound]]:
    """Every chain that declares an invariant, as (edges, paths).

    Chains without one contribute nothing, silently — the check is opt-in
    because most relations assert no shared field, and a record that has not
    said which one it means should read the same as a record with no
    relations at all."""
    edge_hits, path_hits = [], []
    for chain in current().chains.values():
        if not chain.invariant:
            continue
        edge_hits += edges(chain)
        path_hits += paths(chain)
    return edge_hits, path_hits
