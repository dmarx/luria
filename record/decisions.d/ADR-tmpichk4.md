---
status: Active
title: A relation is walked transitively and rendered as sequences, on one page
version: 1
tags:
- record
- mechanism
date: '2026-09-06'
summary: >-
  Typed edges gave every page its neighbours and no view answered "what
  sequence is this document a step in", so the sequences stayed as prose,
  re-described once per participant, and went stale in two places at once.
  `[luria.chains]` walks a declared relation transitively and renders the
  lines on one page; a cycle and a one-sided comparison become findings.
---

# ADR-NNN: A relation is walked transitively and rendered as sequences, on one page

## Context

Reference fields are typed relations and `edges.py` reads them both ways, so
every page can show what is next to it. Nothing answered the question a
reader actually has, which is *what sequence is this a step in* — and that
question was being answered, in the consumer record, by a hand-written
paragraph in each participating document.

The predictable thing happened. Two notes each ended with a sentence saying
two rival designs had never been compared against each other. True when
written, false three weeks later, corrected in two places, and found only
because one person read both notes the same afternoon. A third note carrying
the same paragraph would have been a third place and would have been missed.

The single relation the schema already modelled — `superseded_by:` — has
never had this problem, and that is the argument: it renders from a field,
so there is no paragraph to forget.

## Decision

    [luria.chains.lineage]
    scheme   = "LIT"
    relation = "extends"              # the spine, directed: A extends B
    sibling  = "compared_against"     # optional cross-link, symmetric
    output   = "docs/lineage.md"

`luria index` walks `relation` transitively, groups the scheme's documents
into maximal weakly-connected lines, and renders each as an ordered list with
its cross-linked rivals alongside. Both fields must already be declared
references on the scheme: a chain over a field nothing types walks no edges
and renders an empty page, and an empty page is indistinguishable from a
correct one ([DP-15](../../docs/design-principles.md#dp-15)), so it is a config error.

**The field carries the sequence; the prose carries the argument.** The page
renders order, title and status and nothing else. A chain rendered
mechanically is *shallower* than the paragraphs it replaces — "A extends B"
loses "free mixing is what made B unstable, and constraining it is the whole
point" — so each document keeps explaining its own step and stops restating
the line. That split is the point of the change; a view that licensed
deleting the argument would make the record worse.

**Two structural findings**, both in `broken-chains`, neither acknowledgeable:

- a **cycle** in the spine — A extends B extends A, so neither is the
  earlier step. There is no reading under which that is what the author
  meant.
- a **one-sided comparison** — A declares `compared_against: B` and B does
  not declare A. Comparison is symmetric in a way succession is not, so one
  side alone is one document updated and one not: the exact failure the
  field exists to end, reappearing inside the mechanism.

## Alternatives considered

**One page per line, in a directory.** Rejected on identity: a line has no
stable name, so the file would be named after whichever document is
currently its root, and adding an earlier step would rename the page and
break every link to it. The set of lines is also read *as a set* — which is
the shape `render = "document"` already exists for ([ADR-012](ADR-012.md)).

**A `chains.yaml` listing each sequence by hand.** Rejected: a second place
to forget, sitting outside the documents it describes, so adding a note means
editing a file the filer has no reason to open.

**Reuse `superseded_by:` for the spine.** Rejected because it would lie. Two
live designs in different production systems, one extending the other's
idea, are not a retirement — and flattening "extends" into "supersedes" would
retire documents nothing has retired, which is the deletion-by-status the
status vocabulary exists to prevent.

**Infer the sequence from prose.** Strictly weaker, and already rejected once
for typed edges: it makes an author's paragraph conform to a shape the tool
happens to recognise, and it is unfixable when it guesses wrong.

## Consequences

A project adopting this should migrate **one** line first and read the
result, rather than converting ten and discovering afterwards that the
mechanical rendering lost the argument. The consequence to watch for is a
record whose sequences are correct, current, and say nothing about why any
step happened.
