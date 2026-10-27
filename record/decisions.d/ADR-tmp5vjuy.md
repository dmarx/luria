---
status: Proposed
title: 'A chain may list several schemes, and a step may be a document of any of them'
version: 1
tags:
- record
- mechanism
date: '2026-10-27'
summary: >-
  `scheme:` on a chain takes a list as well as a string, and a string is a
  list of one, so no config changes meaning. Any listed scheme's documents
  may be a step. A field the chain walks may be declared on any listed
  scheme and may land on any of them. A pattern it walks may start and end
  on any of them. A target outside the list is still refused, with a
  message that says to list the scheme. A facet needs one listed scheme to
  hold it, and an invariant needs all of them. This reverses the
  one-scheme rule that [ADR-106](ADR-106.md) set, [ADR-126](ADR-126.md) kept for multi-scheme fields
  and [ADR-129](ADR-129.md) kept for pattern ends. The case that forced it: an objection
  thread in dmarx/nucleation runs claim, argument, claim, and an argument
  nobody undercuts could not be a step at all. Rejected: rendering a
  pattern's inner nodes as steps, a chain per scheme pair, and the status
  quo.
influenced_by:
- ADR-106
- ADR-126
- ADR-129
---

# ADR-tmp5vjuy: A chain may list several schemes, and a step may be a document of any of them

## Context

A chain is a sequence of documents of one scheme. [ADR-106](ADR-106.md) made that a
refusal: a chain whose `relation` points at another scheme is refused at
load. [ADR-126](ADR-126.md) kept it for a reference naming several schemes: a chain
walks such a relation only when its own scheme is the sole target.
[ADR-129](ADR-129.md) kept it for patterns: a pattern's first and last nodes must both
be the chain's scheme, and an inner node renders only as what the step
went "through".

dmarx/nucleation keeps its own argument in two schemes. A CLAIM is a
proposition, and an ARG is an inference from premises to a conclusion.
Its dialectic page walks `objects_to` between claims. An objection to an
inference undercuts the ARG, not its conclusion. On 2026-10-26 five of its
nine undercutting claims were on no thread at all. A pattern,
`(u:CLAIM)-[:undercuts]->(g:ARG)-[:concludes]->(c:CLAIM)`, put them under
the conclusion, "through" the argument. That fixed those five. It could
not place an ARG that nobody undercuts, because there is no claim at
either end. That is the case nucleation's own [ADR-054](ADR-054.md) makes the common
one: "X does not show Y" is filed as the ARG from X to Y, Rejected, with
no counter-claim beside it.

The owner's reading of patterns was that they exist to express paths that
are not homogeneous. They do match such paths. What refused the step was
the chain, which allowed only its own scheme at a step's two ends.

[ADR-106](ADR-106.md) considered teaching the walker to carry far-scheme nodes and
rejected it for three reasons:

- **"A rendered page nobody asked for."** It was right for `SOTA source
  LIT`, a one-hop relation with nothing to sequence. Someone asks now.
- **"A new rule for depth and ordering at a node with no outgoing spine,
  which a far-scheme leaf always is."** The walk needs no new rule. A node
  with no outgoing spine is a root, and the walk already orders roots.
  And an ARG is no leaf: it holds `concludes`, and claims undercut it.
- **"A bipartite graph with sequence vocabulary."** An objection thread is
  a sequence that changes kind as it goes. Claim, the argument for it,
  the objection to that argument, the reply. The sequence is the point,
  and the kinds alternate because the record's schemes say what each step
  is.

## Decision

**`scheme:` on a chain takes a list.** A string is a list of one, so every
existing chain means what it did. The first scheme listed is the chain's
`scheme` wherever one is named.

```yaml
chains:
  dialectic:
    scheme: [CLAIM, ARG]
    relation: [objects_to, undercuts, concludes]
    facet_by: [role, status]
```

- **Any listed scheme's documents may be a step.**
- **A field the chain walks** may be declared on any listed scheme. It is
  read on every listed scheme that declares it, and the results form one
  spine. Every target it may name must be a listed scheme. A field that
  can land elsewhere is refused, and the message says to list that
  scheme. This is [ADR-126](ADR-126.md)'s rule restated: its targets must all be the
  chain's, which with one scheme meant "the chain's scheme alone".
- **A pattern the chain walks** may start and end on any listed scheme. A
  named inner node still renders as "through".
- **`facet_by`** needs one listed scheme that can hold the field. A step
  of a scheme that cannot hold it shows its other facets, so an argument
  in a thread of claims shows its status and no voice.
- **`invariant`** needs every listed scheme to hold the field. The
  invariant is checked at every step, so a scheme that cannot hold it
  would make every one of its steps a finding.
- **A step links into its own scheme's directory**, and the page says
  "on CLAIM and ARG documents".

## Alternatives considered

- **Render a pattern's named inner nodes as steps.** With this,
  `(u)-[:undercuts]->(g)-[:concludes]->(c)` would draw c, then g, then u.
  It still draws nothing for an argument nobody undercuts, because a
  pattern draws only whole matches ([ADR-129](ADR-129.md)). And it hides in a pattern
  what is a fact about the chain: which kinds of document its steps are.
- **A chain per pair of schemes.** One page for claims and one for
  arguments, with links between them. The thread is what a reader wants,
  and it would be split across two pages at every change of kind.
- **Status quo.** A record that argues through a second scheme loses
  every intermediate document that is not "through" a step between two of
  the chain's own. That is the gap nucleation found.

## Consequences

- **Fired on a real case before being trusted.** The tests in
  `tests/test_mixed_chains.py` were written first and seen failing. The
  change was then run on dmarx/nucleation's dialectic page with `scheme:
  [CLAIM, ARG]`; the devlog entry for this change records what it drew.
- **[ADR-106](ADR-106.md)'s refusal is narrowed, not dropped.** A relation into a scheme
  the chain does not list is refused as before. The message now names
  both remedies: list the scheme, or declare `invariant` on the
  reference.
- **[ADR-126](ADR-126.md)'s sole-target rule and [ADR-129](ADR-129.md)'s rule on pattern ends become
  one rule:** every end is a listed scheme.
- **Single-scheme chains render the same pages.** Every listed-scheme
  check reduces to the old one when the list has one entry. Only the
  refusal for a relation that leaves the chain is reworded, and the two
  tests that pinned its old wording ("points at LIT rather than SOTA",
  "rather than CLAIM alone") now pin the new one.
