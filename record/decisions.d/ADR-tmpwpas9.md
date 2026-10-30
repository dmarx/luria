---
status: Proposed
title: 'A directed converse pair stores its primary side; the derived side is computed'
version: 1
tags:
- record
- mechanism
date: '2026-10-30'
influenced_by:
- DP-002
- DP-003
- DP-014
summary: >-
  Supersedes [ADR-084](ADR-084.md) for directed pairs. A converse pair marks its derived
  side with `derived: true` on that side's reference. Only the primary side
  is stored, and every reader gets the derived side from `relations.edges()`.
  The derived field may still be written, and `luria repair` moves what is
  written there. Where the primary side already holds the edge, the derived
  entry is dropped. Where it does not, the entry becomes the primary entry on
  the other document. A move that would assert a directed relation both ways,
  break a document's contract, or name no document is reported and left as
  filed. With nothing stored twice there is no HEAD baseline to consult for a
  directed pair, so a deletion is final. Symmetric relations, and pairs that
  declare no direction, keep [ADR-084](ADR-084.md)'s rule. The latter are reported as
  `undirected-relations` rather than refused. `one-sided-relations` now
  covers only those two kinds, and a hand-filed derived entry is
  `derived-relations`. Fired on Nucleation: 2,626 derived entries dropped, 62
  moved, 1,256 files, the relation graph unchanged at 10,815 edges.
  Rejected: `primary: true` on the forward side, refusing undirected pairs,
  completion run in CI, and keeping both sides stored.
---
<!-- inactive-ok-file: ADR-084 — the decision this supersedes, and the rule symmetric and undirected pairs keep -->

# ADR-tmpwpas9: A directed converse pair stores its primary side; the derived side is computed

## Context

[ADR-084](ADR-084.md) made a converse pair one fact written in two places, and
`luria link --fix` kept the two in step, working out against HEAD whether a
one-sided pair was a new write or a stale deletion. It weighed making one
side authoritative and rejected it:

> it gives up the symmetric case, where there is no canonical side, and it
> gives up declaring the relation from whichever document you happen to be
> holding — which is most of the value.

Its own Consequences section already saw the cost: "With a directed pair
there *is* a canonical side, and the converse is derivable, so storing it
buys one thing: the fact is legible when reading that document alone."

That cost has been measured since. Storing both sides is a hand-maintained
projection of one fact ([DP-003](../principles.d/DP-003.md)), and two writers keep it, the author and
whoever runs the fixer ([DP-002](../principles.d/DP-002.md)). It drifted at [DP-003](../principles.d/DP-003.md)'s rate. Nucleation
declares 63 converse fields and carried 812 one-sided pairs, because
completion lived in a command its CI never ran ([ADR-tmpu2wwj](ADR-tmpu2wwj.md)). Every reader
already worked around the gap: `relations.edges()` unions a relation with
its converse, so chains, invariants, patterns and reliance read a one-sided
pair correctly. The stored second side was serving only someone reading the
raw frontmatter of the derived document.

## Decision

**A directed pair declares which side is derived, and only the primary side
is stored.**

    references:
      extends:     { scheme: LIT, many: true, converse: extended_by }
      extended_by: { scheme: LIT, many: true, converse: extends, derived: true }

Every reader gets the derived side the way it already did, through
`relations.edges()` (`held/4` in `luria/logic/relations.lp`).

**The derived field can still be written.** This answers [ADR-084](ADR-084.md)'s second
objection. An author holding the earlier paper can write
`extended_by: LIT-007` on it. `luria repair` moves that entry as
`extends: LIT-001` to LIT-007 and removes it from where it was written. If
LIT-007 already says so, the written copy is just dropped. Either way the
author states the relation from whichever document they hold, and the record
stores it once.

**Normalization is a repair** ([ADR-tmpu2wwj](ADR-tmpu2wwj.md)). It reads the sources and the
configuration's marks and nothing else: no HEAD, because nothing ever writes
the derived side back. CI applies it on every pull request, and a second run
changes nothing. It is decided by `luria/logic/normalize.lp`.

**What it does not write, it reports**, under `derived-relations`, which
names `luria repair` as the remedy for the rest:

- a move that would make a directed relation run both ways within one scheme
  (A extends B, and B is written as extending A). That is [ADR-084](ADR-084.md)'s
  contradiction rule, unchanged: two things are present, nothing is missing;
- a move or drop that would put either document in breach of its contract.
  This is [ADR-084](ADR-084.md)'s "a repair never breaks the document it lands in",
  applied to the move as one unit, so the far side's refusal never loses the
  edge by removing it from the near side;
- a derived entry naming no document the field may hold. There is nowhere to
  move it. The contract reports the code as well.

**One side, exactly.** A pair with both sides marked `derived` is refused when
the configuration loads, as is `derived` on a field with no `converse`. A
self-converse relation is refused too, because marking it marks both of its
sides.

### Why `derived: true` and not `primary: true`

The mark goes on the side whose behaviour changes. A `derived` field is never
stored, and repair moves what is written in it. That is a fact about that
field, and a reader of the configuration sees it where they would look to
learn what the field holds. The primary side behaves exactly as an ordinary
reference does. Nucleation's configuration already describes its derived
fields this way, each blurb reading "the converse of `extends`, written by
`luria link --fix`", so the key sits beside the sentence it replaces. One key
on one side also keeps the declaration from repeating itself ([DP-003](../principles.d/DP-003.md), the
argument [ADR-097](ADR-097.md) used against `converse_scheme`). A rule requiring
`primary: true` on one side and `derived: true` on the other could disagree
with itself.

### What keeps [ADR-084](ADR-084.md)'s rule

**Symmetric relations.** `compared_against`, `rivals` and `complements` have no
derived side. Each document is an equally natural home for the fact. They
stay stored on both documents and completed by `luria link --fix` against
HEAD, and they still appear in `one-sided-relations` until it runs. Storing
each edge once on a canonical document, such as the lower code, would extend
this decision to them. That choice is left open for the owner rather than
made here: the canonical home would be arbitrary, a temporary code changes
its order when `luria concretize` numbers it, so edges would move at merge,
and a symmetric relation would need its own opt-in key to avoid changing
every existing record silently.

**A pair declaring no direction.** It keeps working exactly as before, with
both sides stored and completion in `link --fix`. The lint reports it as
`undirected-relations`, once per pair, naming the key to add. Refusing to
load would break every record the moment it upgraded, over a choice only its
owner can make ([DP-014](../principles.d/DP-014.md)). Which side is primary is a judgement about the
relation and cannot be inferred, so `luria upgrade` cannot write it either.
The report is the disclosure, and `lint.fail_on` can promote it for a record
that wants the migration enforced.

`one-sided-relations` therefore covers only symmetric and undirected pairs. A
directed pair is never one-sided, because its derived side is computed.

## Alternatives considered

- **Keep both sides stored ([ADR-084](ADR-084.md)).** This is what produced the 812 pending
  pairs. Every one-sided pair was ambiguous between a write and a deletion,
  and only HEAD could tell them apart, which only works where an author runs
  the fixer before committing.
- **`primary: true` on the forward side.** It reads naturally, but it marks
  the side whose behaviour does not change and leaves the unusual one
  unmarked. See above.
- **Refuse a pair that declares no direction.** This is cleaner, and it is
  hostile to every record that predates the key. See [DP-014](../principles.d/DP-014.md) above.
- **Infer the direction**, by declaration order or by which field holds more
  entries. Rejected for the reason [ADR-084](ADR-084.md) rejected inferring the converse:
  that would be a guess written into the record.
- **Make normalization a `link --fix` step.** It would run where completion
  ran and pile up the same way. [ADR-tmpu2wwj](ADR-tmpu2wwj.md) puts it in `repair`.
- **Forbid writing the derived field.** This gives up [ADR-084](ADR-084.md)'s real
  objection, stating a relation from the document you hold, for nothing:
  moving the entry is mechanical.

## Consequences

**Deletion means deleting the primary entry.** Removing a derived entry while
the primary holds the edge changes nothing anyone reads, because the
relation is still derived. That is the intended reading: there is one place
the fact lives. One transitional edge follows from this. In a record that
stored both sides, an author who deletes only the primary entry before
`repair` has dropped the derived copy will see the copy moved back. The
first `repair` on the default branch closes that window, since no derived
copies remain after it.

**[ADR-084](ADR-084.md)'s HEAD baseline is no longer consulted for a directed pair.** Open
PR [#387](https://github.com/dmarx/luria/issues/387), which makes that baseline read aliases, is moot for directed pairs.
It still matters for symmetric and undirected ones.

**`luria export`'s edge table holds a directed relation under its primary
field only.** A query for the reverse reads the primary edge backwards. The
site and the chains already render both directions from `relations.edges()`.

**Fired on Nucleation** (a `git archive` of its default branch, with
`derived: true` added to 28 reference fields): `luria repair` dropped 2,626
derived entries the primary side already held and moved 62 that it did not.
It changed 1,256 files (4,228 lines out, 105 in), held nothing back, found
no clash and no dangling entry, and the second run changed nothing.
`luria lint` stayed clean, `one-sided-relations` fell from 812 rows to 79
(all symmetric), and `held/4`, the relation every reader sees, was identical
before and after at 10,815 edges.
