---
status: Proposed
title: "The site builds on Quartz 5"
version: 1
tags:
- mechanism
- process
date: '2026-09-14'
summary: >-
  [ADR-042](ADR-042.md) rejected Quartz 5 because v5.0.0 could not build at all, and said to
  revisit. The blocker is gone, and the upgrade pays for itself twice: the
  popover bug that sent a reader to the wrong section is fixed upstream, and
  v5 positions components from each plugin's own entry, so the generated
  `quartz.layout.ts` — 90 lines of TSX luria wrote to move one component —
  disappears. Pins a commit rather than a tag, because v5.0.0 is still the
  newest tag and is the release that does not build.
---

# ADR-tmp39e44: The site builds on Quartz 5

<!-- inactive-ok-file: ADR-100 — Proposed. Named as the decision whose
     remaining wart this one closes; the citation is to its reasoning. -->

## Context

[ADR-042](ADR-042.md) pinned Quartz 4 and rejected 5 with a measurement and a condition:

> **Quartz v5.** Its config is YAML, which would have been generated rather
> than templated — a real improvement. Its plugin installer crashes on
> `.scss` under Node 22 … so v5.0.0 cannot build at all here. **Revisit on
> the next patch release.**

Two things have since made revisiting worth it.

**A bug that only v5 fixes.** [ADR-100](ADR-100.md) left one wart: hovering a link in
a book's contents list previewed the wrong section. The cause is in Quartz —
`showPopover` reads `popoverInner` before its `const`, and popovers are
cached per pathname, so on every hover after the first the scroll throws and
the preview stays where it was. Reported upstream-shaped and then found
already fixed: v5 derives the element from the popover it was handed.
Nothing in luria can reach that code; the only local options were to carry a
patched fork or to turn popovers off.

**The generated layout stops existing.** Quartz 5 takes each component's
position from that component's own config entry. Luria's `quartz.layout.ts`
existed to move one thing — the graph, out of the right rail and into the
content column ([#71](https://github.com/dmarx/luria/issues/71)) — and to restate Quartz's defaults around it in TSX so
that the one change could be made. That becomes two keys.

## Decision

**`luria site` writes one `quartz.config.yaml`.** It replaces both generated
files. The layout is expressed per plugin:

    - source: "@quartz-community/graph"
      layout: {position: beforeBody, priority: 40}

which is the whole of [#71](https://github.com/dmarx/luria/issues/71), and the reason `QUARTZ_LAYOUT` is deleted rather
than ported.

**Pinned to a COMMIT, not a tag.** This is the one place this departs from
[ADR-042](ADR-042.md), which says to pin a tag, and the departure is the reason that rule
was written: v5.0.0 is still the newest tag, and v5.0.0 is the release
[ADR-042](ADR-042.md) measured as unbuildable. Pinning the tag would ship the broken one.
The pin is the commit a real build of this record was verified against, and
it moves to a tag as soon as one ships past v5.0.0.

**The two settings the record depends on are asserted, not assumed.**
`markdownLinkResolution: relative` and dates without the `git` provider both
survived the major version under the same names — which is exactly the kind
of thing a major version moves, so the test reads them out of the generated
YAML rather than trusting that they came across.

## Alternatives considered

- **Patch Quartz 4 in the site action.** One line, and it keeps everything
  else still. Rejected: it makes the action carry a fork of a pinned
  generator, which is the arrangement [ADR-042](ADR-042.md)'s pin exists to avoid, and it
  fixes one bug in a version that is no longer maintained — the next one
  costs the same again.
- **Turn popovers off.** `enablePopovers: false`, and the wart is gone.
  Removing a feature to avoid a bug in it, in a record whose whole argument
  is that its pages should be readable.
- **Wait for a v5 tag past 5.0.0.** The tidy version, and [ADR-042](ADR-042.md)'s stated
  condition taken literally. Rejected because the condition was about
  *buildability*, which is now testable directly and passes — waiting on a
  tag that may not come for months, to avoid writing down one pin, is
  ceremony rather than caution.
- **Keep generating TSX for the layout.** v5 still allows a custom page
  frame. It would preserve the diff and keep 90 lines whose only purpose is
  to restate defaults around a single change.

## Consequences

Verified against a real build of this record, not a fixture: Quartz 5
installs (372 packages), builds all 317 pages, and the output was driven in
a browser. The popover lands on its own heading every time, the graph renders
in the content column and not the right rail, and 109 internal links across
four pages resolve.

`sharp` is still a Quartz dependency, so the favicon rasterisation in the
action is unchanged, and the 45 `@quartz-community/*` plugins ship as
ordinary dependencies, so `npm ci` still installs everything.

The published pages change — it is a major version of the generator, and its
markup and styling moved with it. Nothing about the record's addresses
changes: paths, anchors and the slugs [ADR-100](ADR-100.md) settled are all as they
were.
