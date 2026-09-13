---
status: Active
title: "A converse belongs to the scheme whose codes the field holds"
version: 1
tags:
- mechanism
date: '2026-09-13'
issue: '#253'
summary: >-
  `converse` was resolved against the declaring scheme's own fields, so a
  relation crossing a scheme boundary was sayable from one end and unreachable
  from the other — luria.toml said so out loud on `NOTE.paper`. The converse
  now lives on the scheme whose codes the field holds, with same-scheme as the
  case where those coincide. Rejects a `converse_scheme` key and a
  fully-qualified converse name.
---

# ADR-tmp02d4w: A converse belongs to the scheme whose codes the field holds

## Context

`_checked_converses(prefix, refs)` looked the converse up in the declaring
scheme's own reference table:

    by_name = {r.field: r for r in refs}     # this scheme's references
    other = by_name.get(ref.converse)
    ...
    if other.scheme != ref.scheme: raise

So a pair could only exist inside one scheme. Nothing about the *idea* of a
converse requires that — a relation read backwards is still the same relation
when its two ends are different kinds of document — and the constraint was
never argued for. It is what falls out of validating one TOML table at a time.

The cost was not theoretical. `luria.toml` carried it as a known limitation on
`NOTE.paper`:

> There is no converse on the LIT side, because Luria's converse must be
> same-scheme and this crosses.

And the case that forced it: a practice declaring `introduced_by:` — the paper
that first stated the recommendation — with no way to ask a paper what it
originated. That is the argument [#211](https://github.com/dmarx/luria/issues/211) already made for `extended_by`, that the
fork in a line should be legible from the trunk and not only from the branches.
It just happens to cross. Without the field, the answer lives in prose on both
sides and drifts, which is the whole reason relations are fields ([ADR-036](ADR-036.md)).

## Decision

**The converse is a field on the scheme whose codes the near field holds.**

For `A.f` holding `B` codes with `converse = "g"`, the pair is valid when:

- `g` is a reference **`B`** declares (not `A`)
- `B.g.scheme == A` — the relation read backwards points back at the near side
- `B.g.converse == "f"` — mutual, unchanged
- both `many = true` — unchanged

**Same-scheme is the case where `A == B`**, and the old rule falls out of the
new one rather than being special-cased: when the relation does not cross,
`B` *is* the declaring scheme and the lookup is the one it always was.

Two consequences in the machinery:

- **The check moved to `_schemes`**, which already exists for "the cross-scheme
  checks that need them all" and already validates that a reference names a
  declared scheme. It runs after that loop, so a converse naming an undeclared
  scheme is reported as the missing scheme rather than as a missing field on it.
- **`pairs()` returns four elements**, `(scheme, field, converse, converse
  scheme)`. Everything downstream that assumed one document set now takes two —
  `_held`, `_intents`, `_committed`, `relation_spans` — and for a non-crossing
  relation the two are the same object, so the existing path is unchanged by
  construction rather than by care.

`_blocked` is the one that changed shape rather than arity: a repair can now
land in either of a pair's two schemes, so the contract that judges it is read
from the document's own directory instead of from the relation's near end.

## Alternatives considered

- **A `converse_scheme = "LIT"` key.** The obvious one. Rejected because it is
  derivable and therefore a second place for the same fact to live: the field
  already declares `scheme`, and the converse necessarily belongs to it. A key
  that can disagree with something else in the same table is a key that
  eventually will ([DP-3](../principles.d/DP-003.md)).
- **A qualified name, `converse = "LIT.introduces"`.** Reads well and is worse:
  it invents a second naming syntax for references, one the rest of the config
  does not use, and it still has to be checked against the field's `scheme` —
  so it adds a spelling without removing a check.
- **Leave it, and write the reverse edge in prose.** The status quo, and the
  thing this project exists to stop. It is also what the two records already
  did: a paragraph on both sides, which is how the residual chain went stale in
  six documents before [ADR-036](ADR-036.md).
- **Let a converse name any scheme at all, unchecked.** Removes the constraint
  and the guarantee together. The fixer writes files; it has to know that the
  far side can hold what it is about to write there.

## Consequences

A relation between two kinds of document is now one fact with two ends, and
`luria link --fix` completes it in both directions. Verified on
`anthology-of-the-sota`: declaring `SOTA.introduced_by` ↔ `LIT.introduces` and
running the fixer wrote `introduces: [SOTA-060, SOTA-087, SOTA-tmpu69f8]` onto
the paper those three practices name, from nothing but the near side's
declarations.

`pairs()` is a signature change. It is internal, and the one caller outside
this module uses `converse_of`, which is unchanged — but a project reaching
into `relations.pairs()` will need the fourth element.

What this does **not** do is give the two ends different words for what they
mean; `introduced_by` and `introduces` are documented in a TOML comment like
every other relation, which is [#254](https://github.com/dmarx/luria/issues/254) and a separate decision.
