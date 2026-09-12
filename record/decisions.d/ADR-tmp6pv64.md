---
number: 0
status: Proposed
title: "Where a citation points is the project's choice, not the renderer's"
tags:
- architecture
- record
date: '2026-09-12'
summary: >-
  A `render = "document"` scheme gains `cite`, choosing whether a citation of
  its codes resolves to the cited document's own file or to an anchor in the
  assembled view, and `luria repair` moves links a record already wrote when
  that changes. Unset keeps today's behaviour. Rejected: defaulting to "page"
  now, which sends citations out to the repository while a document scheme's
  sources are unpublished, and emitting anchors that survive each publisher.
---

# ADR-tmp6pv64: Where a citation points is the project's choice, not the renderer's

## Context

A scheme rendered as one assembled document gives each of its sources two
addresses: the source file, and an anchor in the page it assembles into. Only
one of them was reachable — `doc_refs` resolved every citation of such a code
to `output#anchor`, with no way to say otherwise.

That anchor is more fragile than it looks. The ones this generator emits are
`<a name="dp-3"></a>`: raw HTML, correct as markdown, and preserved only by a
publisher that chooses to preserve it. Quartz does not — its remark→hast
pipeline drops the element and slugifies each heading's own text instead, so a
link written against an anchor the source genuinely contains lands on a page
that has no such id. The links work in the repository and fail on the site,
which is the worst place for a difference to live: every check this project
runs reads markdown, and `docs/design-principles.md` resolves perfectly as a
path.

There is also no single right answer. A set genuinely read in order — an
interface document, a constitution — is better cited at the passage than at a
file, and that is a property of the record, not of the renderer.

## Decision

**`[luria.schemes.X] cite` chooses**, and unset means what the scheme already
does:

```toml
[luria.schemes.SPEC]
render = "document"
output = "docs/interfaces.md"
cite   = "page"          # or "view"
```

`"page"` resolves a citation to the cited document's own file. `"view"`
resolves it to `output#anchor`. Unset resolves to `"view"` for a document
scheme and `"page"` for an index scheme — which has no second address — so
**adding this key changes nothing for a project that does not set it**, and
`cite` always states where a citation goes rather than sometimes meaning
nothing.

Two refusals, because they are different mistakes. An unknown word is a typo.
An explicit `cite = "view"` on an index scheme is a request that cannot be
honoured — there is no assembled document to anchor into — and resolving to
the page anyway would answer a question the project did not ask.

**`luria repair` moves the links a record already wrote.** Without it the key
would be half a feature: flipping it governs every citation written from then
on and nothing at all already on disk, because those are plain markdown links
and the linkifier spells *bare* references. `retarget_view_citations` is
deliberately narrow — it leaves the link TEXT alone, because that is the
author's sentence rather than a field; it leaves a link with no fragment
alone, because pointing at the whole assembled document is a real thing to do;
and it leaves an anchor naming no document alone, because rewriting that would
swap a dead fragment for a dead FILE, which is worse and hides it from the
lint.

## Alternatives considered

- **Default to `"page"` now.** The target this is all heading for, and wrong
  today. A page target is only better than an anchor once the sources ARE
  pages, and a document scheme's sources are not published — the view is. So
  defaulting to `page` sends every such citation out of the site to the
  repository instead. Measured rather than argued: with `page` as the blanket
  default, `examples/constitution` goes from **0 to 15** links redirected to
  source, and `test_every_example_stages_its_own_site` fails by name, calling
  it "a target the site had no page for". That test has been asserting this
  since before the key existed. The default becomes `page` in the change that
  publishes those sources, not in this one.

- **Emit anchors that survive the publisher.** Keeps every existing link
  working and needs no rewrite. Rejected on where the fix would have to live:
  the anchors are already correct as markdown, and what drops them is a
  generator's HTML handling — so the repair means finding a spelling Quartz
  keeps today, and re-finding it for the next publisher and the next version,
  in a place where the failure is invisible from the source. A page is a page
  in every renderer.

- **Retarget as a one-shot migration** rather than part of `repair`. Rejected:
  the rewrite is derivable from the config and the sources, which is the line
  `repair` already draws — it writes what a generator can decide and leaves
  what needs judgement to the lint. A one-shot also strands every project that
  flips the key later.

- **Status quo.** One address per document, chosen by the renderer, and no way
  for a project whose publisher eats anchors to say so.

## Consequences

**Nothing changes on this record.** `luria repair` reports `repaired 0
file(s)`, the full suite passes unmodified, and `luria lint` is clean — which
is the evidence that the key is inert until set, not a claim about it.
`retarget_view_citations` is covered by unit tests rather than by this
repository's own content, and will get its first real exercise from the change
that flips the default.

**Under `cite = "page"`, a code naming no document resolves to nothing.** The
anchor was *constructed* from the number, so a citation of any number produced
a link whether or not the document existed. A page target cannot be
constructed, so the lint gets to report it. A project switching may discover
dangling citations it did not know it had.
