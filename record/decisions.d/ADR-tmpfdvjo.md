---
status: Proposed
title: 'A chain may walk a composed relation'
version: 1
tags:
- record
- mechanism
date: '2026-10-13'
issue: '#371'
summary: >-
  A scheme may declare a composed relation: a name and the reference fields
  it follows in order, `leads_to: [premise_of, concludes]`, from the scheme
  through one or more other schemes and back. A chain names it in
  `relation` or `sibling` as it names a field, so a chain stays a sequence
  within one scheme while a step passes through another. It is read-only:
  never written, completed or converse-paired, and every leg must land in
  exactly one scheme. The page names the document each step passed through
  and shows where a path stops partway. Rejected: a hop key on the chain, a
  derived reference field (`derive`/`from:`), writing the relation into
  frontmatter, walking intermediates as steps, legs over a union of
  schemes, and a query language in `luria.yaml`.
influenced_by:
- ADR-106
- ADR-125
- ADR-126
- ADR-127
---

# ADR-tmpfdvjo: A chain may walk a composed relation

## Context

A chain walks reference fields: `relation` names one field or several
([#211](https://github.com/dmarx/luria/issues/211)), `sibling` one more, all declared on the chain's own scheme. A chain
is a sequence within one scheme ([ADR-106](ADR-106.md)), and [ADR-126](ADR-126.md) kept it so when
references gained unions: a chain walks a relation only if its own scheme
is the sole target, because skipping the edges that leave would drop steps
without a finding.

That leaves a line the record states and no chain can draw. [ADR-127](ADR-127.md) names
it: in a downstream record, an argument runs claim → inference → claim. The
inference is its own document, citing the claims it starts from and the
claim it concludes, so the step from one claim to the next is real but is
two edges through another scheme. The chain stops at the inference, and
the line of argument the record was built to show is never rendered.
Illustratively:

```yaml
schemes:
  CLAIM:
    fields:
      premise_of: {scheme: INF, many: true, converse: premises}
  INF:
    fields:
      premises:   {scheme: CLAIM, many: true, converse: premise_of}
      concludes:  {scheme: CLAIM}
```

[ADR-127](ADR-127.md) put "chains over a derived relation rather than a field" after the
logic core, outside its decision. The core is in ([#360](https://github.com/dmarx/luria/issues/360)): `held/4` in
`luria/logic/relations.lp` reads every declared relation from either side,
and the joins this needs are one rule over it.

Two words are already taken. A *derived field* is `derive` ([#216](https://github.com/dmarx/luria/issues/216)): a value
computed from a template, read everywhere as an ordinary field. `paths:` is
the settings table for directories. So this decision says *composed*.

## Decision

**A scheme may declare composed relations.** Each is a name and the
reference fields it follows, in order:

```yaml
schemes:
  CLAIM:
    composed:
      leads_to: [premise_of, concludes]
chains:
  argument:
    scheme: CLAIM
    relation: leads_to
    output: docs/arguments.md
```

`A leads_to B` holds when A stands in `premise_of` to some INF document I,
and I stands in `concludes` to B. Each leg is read through `held/4`, so a
leg stated only on its converse side counts, as it does for every chain
today.

- **Declared on the scheme, named once.** A chain names a composed relation
  in `relation` or `sibling` wherever it names a field, and may mix it with
  fields in one spine as [#211](https://github.com/dmarx/luria/issues/211) mixes fields. The chain gains no key, and
  the name is a fact of the scheme that `luria facts` prints:
  `composed(S, N)` and `composed_leg(S, N, I, F)`.
- **Every leg lands in exactly one scheme, and the last in the declaring
  one.** The first field is a reference declared on the scheme. Each later
  field is declared on the sole target of the field before it. The last
  field's sole target is the declaring scheme. A leg whose field names a
  union is refused at load, for [ADR-126](ADR-126.md)'s reason: following only the
  codes that land in the next leg's scheme would drop edges with no
  finding. These are new refusals in `consistency.lp`, beside
  `walk_leaves`.
- **Read-only.** A composed relation is never written into frontmatter,
  has no converse, is never completed by `luria link --fix`, and cannot be
  written by `luria relate`. It restates facts two fields already hold, so
  it has no source of its own to drift from.
- **The step says what it passed through.** A spine step from a composed
  relation renders under its parent as a field step does, and names the
  intermediate documents that connect the pair: "— through INF-004". With
  several, all are named, in code order. The page shows the line; the
  inference is still where the argument is read.
- **A path that stops partway is shown, not dropped.** An intermediate the
  first leg reaches and the last leg never leaves (an inference with
  premises and no conclusion yet) is listed on the chain's page under the
  step it hangs from, as "open at INF-007". It is not a lint finding,
  because an inference in progress is a legitimate state, and nothing
  mechanical can supply its conclusion. Not drawing it would read exactly
  like a line that ends there ([DP-15](../principles.d/DP-015.md)).
- **A chain's `invariant` covers composed steps.** It is checked between
  the two endpoints, as for any edge the chain walks. A composed relation
  takes no `invariant` of its own here: [ADR-106](ADR-106.md)'s relation-level
  invariant belongs to a field, and its legs already carry one if they
  need it.
- **Derived in the logic core.** A rule in `luria/logic/` derives the
  composed edges and the intermediates, recursing over leg index so
  length is not fixed at two. Python reads the derived atoms into the same
  spine the walk already consumes, so cycles, depth, ordering and facets
  behave the same whichever kind of step filled them.

## Alternatives considered

- **A hop key on the chain** (`through: INF`, or a leg list under the
  chain). Smaller, but the composition would be restated in every chain
  that walks it, and a chain's config would carry a second way to name a
  relation beside the fields. On the scheme it is one declaration that
  `luria facts`, and later a report or [ADR-127](ADR-127.md)'s queries, can read without
  a chain.
- **A derived reference field**, by extending `derive` and `from:`. That
  machinery renders a template against one hop to one document
  (`source[0]`), and its result is an ordinary field everywhere, which a
  reference would then expose to the contract, converse pairing and the
  fixer. A composed relation fans out over every intermediate, and the
  page needs to know which intermediate connected each pair, which a field
  value loses.
- **Writing the relation into frontmatter**, kept by the fixer as a
  materialized `leads_to:`. The same fact stored twice, free to disagree
  with the two fields it restates, and a fixer writing a claim nobody
  stated.
- **Walking intermediates as steps** (rendering the INF documents in the
  spine). [ADR-106](ADR-106.md) refused far-scheme nodes in a chain. Facets, status
  vocabularies and invariants are the chain scheme's, and a line that
  alternates schemes reads as neither.
- **Legs over a union of schemes**, following only the codes that land in
  the next leg's scheme. This is the union skip [ADR-126](ADR-126.md) refused, one level
  down. A record that needs it can declare one composed relation per
  route; widening this later is additive.
- **A query language in `luria.yaml`** (a pattern, or ASP rules). [ADR-125](ADR-125.md)
  keeps configuration readable as the rule in the line. A list of field
  names is that. A rule body is not, and the `.lp` programs stay luria's
  implementation.
- **Status quo.** Records that argue through intermediate documents keep
  writing their lines in prose, one paragraph per participant, which is
  the duplication chains were built to end ([#171](https://github.com/dmarx/luria/issues/171)).

## Consequences

- Records that declare no composed relation are unchanged. Under
  [ADR-127](ADR-127.md)'s rule, the change merges only if `luria lint` and `luria index`
  output is byte-identical on luria's own record, every example,
  dmarx/nucleation and dmarx/anthology-of-the-sota.
- Anything that reads a chain's `relation` as field names must accept a
  composed name. Today that is the chain loader, `consistency.lp`'s
  `walk_undeclared`, the chain facts and the page's intro sentence, which
  should say `` `leads_to:` (premise_of → concludes) ``.
- A composed relation and a field may not share a name on one scheme. A
  refusal at load keeps every name a chain uses meaning one thing.
- The chain page grows two renderings: "through" on a step and "open at"
  under one. Both need tests against a real record before they are
  trusted, and an example that declares the shape. `examples/` has none
  today.
- The derivation is joins only: no choice rules, one answer set, so the
  page stays deterministic, as [ADR-127](ADR-127.md) requires.
- Reports and invariants over composed relations, and a composed relation
  used outside chains, are not decided here. They become possible because
  the declaration lives on the scheme, and are left to whichever record
  needs them first.
