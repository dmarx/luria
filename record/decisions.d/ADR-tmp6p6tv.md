---
status: Proposed
title: 'A reference may name several schemes'
version: 1
tags:
- record
- mechanism
date: '2026-10-07'
issue: '#160'
summary: >-
  `scheme:` on a reference takes a list as well as a string, and a code
  passes if it belongs to any scheme listed. A string is a list of one, so
  no config changes meaning. A converse is a field of the same name on every
  scheme listed, each naming the declaring scheme back; a chain walks the
  relation only when its own scheme is the sole target. Rejected: a field
  per target family, a loose `requires` field, a refinement predicate
  language, and letting a chain walk a union that includes its scheme.
influenced_by:
- ADR-060
- ADR-097
- ADR-106
---

# ADR-tmp6p6tv: A reference may name several schemes

## Context

A typed reference named exactly one scheme ([ADR-060](ADR-060.md)), so a relation whose
legitimate targets span two families could not be declared. [#160](https://github.com/dmarx/luria/issues/160) found the
case in `examples/constitution`: a boundary that overrides another boundary
is rejected as "not a PRACTICE code", though a carve-out that beats a
prohibition is the same relation whichever kind of rule it beats. The same
shape appears in an anthology where a practice cites a paper or a dataset,
and in a spec that supersedes a spec or an RFC.

It came up again from a downstream record. Nucleation, which keeps literature
(LIT) and accounts drawn from it (THEORY), is designing schemes for
developing its owner's own arguments. Its candidate CLAIM scheme needs
premises that are THEORY entries, other CLAIMs or worked cases. Under one
scheme per reference, that is three parallel fields per relation.

## Decision

`scheme:` takes a string or a list of strings:

```yaml
rests_on:
  scheme: [LIT, CASE]
  many: true
  converse: supports
```

- **Membership, not equality.** A code passes if it belongs to any scheme
  listed, and resolves in its own scheme. The finding names the union: "is
  not a LIT or CASE code". Every check that compared a code's scheme against
  the declared one now tests membership instead: the contract, the typed
  edges, `luria relate`, `ref::` statements, grouped views and invariants.
- **A string is a list of one.** Internally `Reference.scheme` and
  `Field.reference` are tuples, so there is one representation and no
  branch on the shape.
- **One relation, one name.** A converse lives on every scheme listed, by
  the same field name, and each must name the declaring scheme among its
  own targets ([ADR-097](ADR-097.md) applied per target). `relations.pairs()` yields one
  pair per target scheme. Each target holds its own half, so the fixer
  completes each one independently, and the existing machinery for a
  crossing pair needed no other change.
- **A chain still walks within one scheme.** A chain may walk a relation
  only if the chain's own scheme is its sole target. A union that includes
  the chain's scheme can still leave it, and a chain is a sequence within
  one scheme ([ADR-106](ADR-106.md)). To assert a shared field over the relation, declare
  `invariant` on it. That is now checked against every target scheme.
- **A followed derivation is checked against every target.** `from:` reads
  whichever scheme the code names, so a template that only some targets can
  render is refused.

## Alternatives considered

- **A field per target family** (`overrides_practice`, `overrides_boundary`).
  This is what a project had to do before this change. It moves the type
  system's job into the field name, reads as two relations, and leaves
  every reader of the graph to know which fields to union.
- **A loose `requires` field.** This checks presence and nothing else, which
  is the failure [ADR-060](ADR-060.md) was written against.
- **A refinement predicate** (`Ref[LIT where status = Active]`). [#141](https://github.com/dmarx/luria/issues/141) defers
  this. A union of schemes is strictly less expressive, needs none of the
  predicate machinery, and widens an existing check rather than adding a
  new kind of check.
- **Letting a chain walk a union that includes its own scheme**, skipping
  the edges that leave it. A chain would then silently drop edges it was
  declared over, and that is how a rendered line comes to omit a step
  without a finding.
- **A different converse name per target scheme.** This would let LIT call
  the relation `supports` and CASE call it `grounds`. A converse is the same
  relation read backwards, and a second name would let two readings of one
  fact disagree about what they are called.

## Consequences

- Existing configs are unchanged: every string target becomes a one-element
  tuple, and the full test suite passes. Seven assertions that compared the
  internal representation to a bare string were updated to the tuple.
- Code that reads `Reference.scheme` or `Field.reference` must treat them as
  tuples. `contract.targets`, `contract.target_of` and `contract.spelled`
  are the helpers, and nothing should compare a code's prefix against the
  declaration by hand.
- `relations.converse_scheme_of` is removed. It had no callers, and for a
  multi-scheme field it would have named one target out of several.
- `examples/constitution` declares `overrides: [PRACTICE, BOUNDARY]`, the
  shape [#160](https://github.com/dmarx/luria/issues/160) asked for. It was fired on the example before being trusted
  (see the devlog of 2026-10-07).
