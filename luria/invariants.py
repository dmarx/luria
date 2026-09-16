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

**Two places may declare an invariant, and they assert different things.**

- `references.<field>.invariant` asserts the *edge*: the two documents this
  relation joins share a value. It is the relation's own property, so it
  holds whether or not any chain walks the field, and it may cross schemes —
  a practice and the paper it rests on are joined by exactly one relation and
  sit in no sequence together (ADR-106, #272).
- `chains.<name>.invariant` asserts the edge *and the line*: every member of
  a component holds one value in common. Only a chain can say that, because
  transitivity is what a chain is.

Declared both ways on one field, they are one assertion and report once.

**Nothing is checked unless something declares `invariant`.** That default is
load-bearing rather than cautious, and the reason is in what a relation is
for: it names a commonality, and naming it is usually the whole job. Two
papers joined by `extends` have succession in common, and `extends` is where
that is written; no other field repeats it. Where a record does keep a field
whose values a relation should agree in, saying so is one key. Where it does
not, a check reading some other field would report every edge — and a report
that fires on everything ranks nothing, which is worse than no report at all
(DP-15).

Opt-in also keeps the choice of field with the record. `tags` and a derived
`primary_topic` are different assertions over the same documents — any shared
subject, against the same first subject — and only the record knows which one
its relations mean.

Cardinality decides what "shared" means, and it falls out rather than being
configured: a list-valued field is compared by non-empty intersection, a
single-valued one by equality — which is the same operation once a scalar is
read as a set of one.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import chains, relations
from .adr_index import Adr, load_scheme
from .config import Chain, Reference, current


@dataclass(frozen=True)
class Unbound:
    """One finding: the documents, and what each holds in the field."""
    # What declared the invariant — a chain by name, or a relation as
    # `SCHEME.field`. The report prints it so a reader knows which key to
    # change, not merely which documents to look at.
    declared_by: str
    field: str
    members: tuple[Adr, ...]

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(d.code for d in self.members)


def _documents(prefix: str) -> dict[str, Adr]:
    return {d.code: d for d in load_scheme(current().schemes[prefix])}


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


def relation_edges(prefix: str, ref: Reference) -> list[Unbound]:
    """Pairs joined by one declared relation that share no value in its
    invariant field.

    The far scheme's documents are loaded beside the near one's, which is the
    whole difference from the chain walk: a relation names the scheme it
    points at, so both ends are known without a sequence to walk them along.

    Edges only. A relation asserts something about the pair it joins and
    nothing about what else either end is joined to, so the transitive
    reading — every member of a component holding one value in common — is
    not the relation's to make. It is the chain's, and a chain is where it
    stays (#272)."""
    docs = _documents(prefix)
    if ref.scheme != prefix:
        docs = {**docs, **_documents(ref.scheme)}
    out, seen = [], set()
    for code, targets in sorted(relations.edges(prefix, ref.field).items()):
        for other in sorted(targets):
            pair = tuple(sorted((code, other)))
            if pair in seen or not all(c in docs for c in pair):
                continue
            seen.add(pair)
            a, b = docs[pair[0]], docs[pair[1]]
            if not (held(a, ref.invariant) & held(b, ref.invariant)):
                out.append(Unbound(f"{prefix}.{ref.field}", ref.invariant,
                                   (a, b)))
    return out


def declared() -> list[tuple[str, str]]:
    """What asserts an invariant, as (what declared it, the field) — relations
    first, then chains, in declaration order. What the report names."""
    out = [(f"{prefix}.{ref.field}", ref.invariant)
           for prefix, scheme in current().schemes.items()
           for ref in scheme.references if ref.invariant]
    return out + [(c.name, c.invariant)
                  for c in current().chains.values() if c.invariant]


def findings() -> tuple[list[Unbound], list[Unbound]]:
    """Everything that declares an invariant, as (edges, paths).

    Relations are read first, so a pair a relation and a chain both speak for
    is attributed to the relation — the narrower declaration, and the one
    whose key a reader would change. The same pair is reported once per
    field: two declarations of one assertion are one assertion, and a second
    row would say the config is redundant rather than that the record is.

    Declaring nothing contributes nothing, silently. A record that has not
    said which field its relations mean should read the same as a record with
    no relations at all."""
    edge_hits, path_hits, seen = [], [], set()

    def keep(hits: list[Unbound]) -> list[Unbound]:
        fresh = [h for h in hits if (h.field, h.codes) not in seen]
        seen.update((h.field, h.codes) for h in fresh)
        return fresh

    for prefix, scheme in current().schemes.items():
        for ref in scheme.references:
            if ref.invariant:
                edge_hits += keep(relation_edges(prefix, ref))
    for chain in current().chains.values():
        if not chain.invariant:
            continue
        edge_hits += keep(edges(chain))
        path_hits += paths(chain)
    return edge_hits, path_hits
