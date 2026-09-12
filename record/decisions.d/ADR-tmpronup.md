---
status: Proposed
title: "A document's typed lineage is drawn on its page, beside Quartz's graph"
version: 1
tags:
- record
- architecture
date: '2026-09-11'
summary: >-
  `luria site` renders each document's typed edges as an interactive graph at
  the foot of its page, using strata-g's vendored export viewer. Rejected:
  replacing Quartz's `Component.Graph` with it, which was the first plan —
  measured, the typed-edge graph reaches 47% of scheme documents and none of
  the journal entries, so the swap would have left most pages with an empty
  box where a neighbourhood used to be.
---

# ADR-tmpronup: A document's typed lineage is drawn on its page, beside Quartz's graph

## Context

A record's typed edges — `superseded_by:`, `influenced_by:`, and whatever
relations a project declares — live in frontmatter, which a site renders as
nothing at all. [ADR-042](ADR-042.md) already answers half of that: `luria site` writes a
**record line** under each document's title stating those edges as prose, with
every code resolved to a link.

The other half is that lineage is a *shape*, and a table of links is a poor way
to show a shape. Quartz draws a graph, but it is the page-link graph: it says a
page was mentioned, never how. A decision that supersedes another and a decision
that merely cites it are the same line in Quartz's picture.

strata-g ([dmarx/strata-g](https://github.com/dmarx/strata-g)) exports a graph as a
self-contained interactive viewer — a custom element, a data island, no network
and no dependencies. That is a payload a static-site generator can vendor.

## Decision

`luria site` renders each document's **depth-1 typed neighbourhood** as an
interactive graph under a `## Lineage` heading at the foot of its page, and
**leaves Quartz's own graph in place**.

The load-bearing details:

**The layout is computed here, not simulated in the browser.** A depth-1
neighbourhood is a star: the centre at the origin, the neighbours evenly on a
ring starting at the top. Exact for the shape, no physics, and identical on
every load — a graph that settles differently each time is harder to recognise
on a page you revisit.

**Node URLs are absolute, and a record with no `site.base_url` gets no graphs.**
The viewer only writes an `href` it recognises as `http(s)`; a site-relative
path is refused, and nodes that navigate nowhere are worse than no picture. A
nested record is mounted at a path its own config has never heard of, so the
*parent* supplies the URL base for its children rather than each child spelling
one from its own `base_url` — which would omit the mount prefix and 404 on
every node.

**A scheme rendered into one assembled document resolves to an anchor.** Design
principles have no page each. Measured on this record, 50 of 122 typed-edge
endpoints are principles — leaving them out would have drawn less than half the
lineage. The anchor is asked of `doc_refs.wikilink_target`, the resolver
everything else links through, rather than spelled a second time ([DP-4](../../docs/design-principles.md#dp-4)).

**Nodes are labelled with the code alone.** Measured, not preferred: at 300px
the real titles ran off the canvas and overlapped each other. The record line is
two lines up and states every one of these edges in prose, so the graph carries
the shape and the prose carries the words.

**The viewer is vendored with a content-hash pin.** `luria/assets/` holds the
payload; `LINEAGE_VIEWER_SHA256` pins it and a test compares them, so a copy
edited in place is a failure rather than a surprise — the same offline-drift
discipline [ADR-016](ADR-016.md) applies to remote document content.

## Alternatives considered

- **Replace Quartz's `Component.Graph` with this**, which is what was asked for
  and what this deliberately does not do. Measured first, on this record: 61
  typed edges across 110 scheme documents, so 52 of them (47%) have any typed
  edge at all, degrees 1–6 — and journal entries, reports and the README have
  none by construction. Quartz's graph is dense precisely because the generated
  indexes link every document they list. Swapping one for the other would trade
  a dense neighbourhood on every page for an empty box on most of them. Adding
  costs a heading and 300px on the 58 pages that have lineage; replacing costs
  every other page its graph.
- **Render the lineage as a static image** (SVG at build time). Cheaper and
  themable, but a picture you cannot click is a picture you cannot use as
  navigation, which is most of the value.
- **Force-directed layout in the browser.** More general, and worse here: a
  star has an exact layout, and a simulation would spend CPU to land somewhere
  slightly different each visit.
- **Status quo — the record line alone.** It is correct and complete, and it is
  a table. Shape is what it cannot show.

## Consequences

The lineage graph appears on 58 of 280 staged pages on this record, and nowhere
else. One copy of the viewer (about 20 KB) is served from the site root and
written only when at least one page references it.

**The graph does not follow the site's theme toggle.** The viewer paints canvas
labels with literal 2D-context colours, so a `var(--light)` would be dropped by
half the widget. It is drawn as a single dark figure that reads on both of
Quartz's themes. Fixing this properly needs a re-theme hook in the viewer
upstream, not a change here.

**This record now has an upstream.** The vendored viewer is generated from
strata-g's `web/src/graph/export/webappViewer.ts`; updating it means re-emitting,
dropping the file in, and moving the pin. The behaviour the pin protects —
that it draws, that a click navigates, that a `javascript:` URL is refused — is
covered by strata-g's browser suite, which this package does not duplicate
because a browser is not a dependency it is willing to take on.
