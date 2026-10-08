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

from . import logic
from .adr_index import Adr, load_scheme
from .config import Chain, Reference, current
from .facts import members


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


def _documents(*prefixes: str) -> dict[str, Adr]:
    return {d.code: d for p in prefixes if p in current().schemes
            for d in load_scheme(current().schemes[p])}


def held(doc: Adr, field: str) -> set[str]:
    """The values a document holds in `field`, as a set.

    A scalar is a set of one, which is what lets equality and intersection be
    the same test — `status: Active` on both sides intersects to `{"Active"}`
    exactly when the two are equal. `facts.members` is the one definition;
    the rules compare the same sets through `holds/3`."""
    return members(doc.meta.get(field))


def shared(docs, field: str) -> set[str]:
    """What every one of `docs` holds in `field` — the invariant they have in
    common, empty when they have none.

    One definition because two consumers ask it: this module, to report a
    component that shares nothing, and `chains._sections`, to give a line the
    heading it belongs under. They are the same question read two ways, and a
    view that grouped by a rule the check did not use would be worse than no
    grouping at all."""
    docs = list(docs)
    if not docs:
        return set()
    return set.intersection(*(held(d, field) for d in docs))


# Which pairs and lines are unbound is decided by `luria/logic/invariants.lp`
# over `relations.lp`'s reading of each relation from both sides — so a
# one-sided declaration is checked before `luria link --fix` has written the
# other half. A finding that waited for the fixer would be a finding about
# tidiness rather than about the record. What follows only puts the derived
# atoms in the order the report has always printed them.

def _derived() -> logic.Derived:
    return logic.derive("relations", "invariants")


def edges(chain: Chain) -> list[Unbound]:
    """Pairs in a declared relation that share no value in the field — every
    edge the chain walks, spine and cross-link alike, as sorted pairs."""
    if not chain.invariant:
        return []
    docs = _documents(chain.scheme)
    pairs = sorted((a, b) for n, a, b in _derived().get("unbound_edge", ())
                   if n == chain.name)
    return [Unbound(chain.name, chain.invariant, (docs[a], docs[b]))
            for a, b in pairs]


def paths(chain: Chain) -> list[Unbound]:
    """Components whose members hold no value in common, ordered by their
    earliest member, each member list sorted.

    A one-member component is not a finding: a document alone in the graph
    asserts nothing about anything, so there is no invariance to express."""
    if not chain.invariant:
        return []
    derived = _derived()
    groups: dict[str, list[str]] = {}
    for n, root, code in derived.get("member", ()):
        if n == chain.name:
            groups.setdefault(root, []).append(code)
    docs = _documents(chain.scheme)
    out = []
    for n, root in sorted(derived.get("unbound_line", ())):
        group = sorted(groups.get(root, ())) if n == chain.name else []
        if len(group) >= 2:
            out.append(Unbound(chain.name, chain.invariant,
                               tuple(docs[c] for c in group)))
    return out


def relation_edges(prefix: str, ref: Reference) -> list[Unbound]:
    """Pairs joined by one declared relation that share no value in its
    invariant field.

    A relation names the scheme it points at, so both ends are known without
    a sequence to walk them along; that is the whole difference from the
    chain check.

    Edges only. A relation asserts something about the pair it joins and
    nothing about what else either end is joined to, so the transitive
    reading — every member of a component holding one value in common — is
    not the relation's to make. It is the chain's, and a chain is where it
    stays (#272)."""
    if not ref.invariant:
        return []
    derived = _derived()
    joined = {(c, x) for s, f, c, x in derived.get("held", ())
              if s == prefix and f == ref.field}
    pairs = [(a, b) for s, f, a, b in derived.get("unbound_relation", ())
             if s == prefix and f == ref.field]
    # Each pair where a reading from the near side meets it first: by the
    # near document, then the far one.
    pairs.sort(key=lambda p: min(t for t in (p, p[::-1]) if t in joined))
    docs = _documents(prefix, *ref.scheme)
    return [Unbound(f"{prefix}.{ref.field}", ref.invariant, (docs[a], docs[b]))
            for a, b in pairs]


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


def lines() -> tuple[list[str], list[str]]:
    """`findings()` as the lint's two row lists — (relations, lines) (#311).

    Until this existed the invariants were a *report* and nothing else: no
    class, so `lint.fail_on`, `lint.mute` and `lint.baseline` all missed them,
    and a project could only ever read the rows. That made an `invariant:`
    all-or-nothing — declarable over a corpus already at zero, and otherwise
    a report that says a number nobody can act on.

    Two classes rather than one, because the two findings differ in strength
    and `unbound-lineage.md` already says so: an unbound *edge* is two
    documents joined directly with nothing in common, while an unbound *line*
    is a whole sequence with no value common to every member — which happens
    while every single step is expressed, since a component's intersection
    only shrinks as the component grows. A project that wants the strong
    signal fatal and the weak one standing needs them separable to say it."""
    edge_hits, path_hits = findings()
    edges_out = []
    for f in edge_hits:
        docs = " ↔ ".join(f.codes)
        holds = " / ".join(", ".join(sorted(held(d, f.field))) or "(none)"
                           for d in f.members)
        edges_out.append(f"{docs} share no `{f.field}` "
                         f"({f.declared_by}; each holds: {holds})")
    paths_out = [f"{', '.join(f.codes)} share no `{f.field}` across the whole "
                 f"line ({f.declared_by})" for f in path_hits]
    return sorted(edges_out), sorted(paths_out)
