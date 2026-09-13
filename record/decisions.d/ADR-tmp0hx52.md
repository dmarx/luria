---
status: Proposed
title: "A project can show a graph it designed in place of Quartz's"
version: 1
tags:
- record
- architecture
date: '2026-09-12'
summary: >-
  `[luria.site] graph` points at a strata-g `Canvas — graph data (JSON)`
  export; set, that one curated picture replaces `Component.Graph` on every
  page. Opt-in, and the inverse of the generated lineage graph: one graph the
  project laid out, everywhere, rather than a neighbourhood computed per page.
  Rejected: a Quartz component that fetches the data (needs a network request
  and a viewer change), and base64 in the file (opaque for no gain).
---

# ADR-tmp0hx52: A project can show a graph it designed in place of Quartz's

## Context

Two graphs can appear on a page of a luria site, and until now a project chose
neither of them.

Quartz draws the **page-link graph**: a neighbourhood computed from what links
to what. It is honest and it is automatic, and it says only that a page was
mentioned. [ADR-tmpronup](ADR-tmpronup.md) added the **lineage graph** — the document's typed
edges, generated per page, at the foot.

Neither is a picture anybody *drew*. A project that knows what it is made of —
these are the decisions, that is the devlog, this is how they relate — has no
way to say so. Meanwhile strata-g is a tool for laying graphs out by hand, and
its viewer is already vendored here for the lineage graph.

## Decision

`[luria.site] graph` points at a strata-g `Canvas — graph data (JSON)` export.
Set, that graph is rendered **on every page, where Quartz's local graph
was** — `Component.Graph` is dropped from the generated layout and the element
is inserted above each document's own heading. Unset, nothing changes.

Why this is a replacement rather than an addition, when [ADR-tmpronup](ADR-tmpronup.md) argued
the opposite for the lineage graph: the objection there was density — a graph
generated per page is empty on most pages, so swapping would leave most readers
with a box and nothing in it. A configured graph is **the same picture
everywhere**. There is no page it is empty on, so there is no page the swap
makes worse. Two graphs stacked above every document's first paragraph is not
a thing anyone would choose deliberately.

The load-bearing details:

**The file is validated at build time, with the error naming which way it is
wrong** — missing, not JSON, not a graph, a node without a position. A site
that builds and then shows an empty box has told the author nothing ([DP-1](../principles.d/DP-001.md)).

**A node whose URL the viewer will not follow is reported, not rejected.** A
graph whose nodes are not links is a perfectly good picture; a node that looks
clickable and silently is not, is not. The viewer only ever writes an `href`
it recognises as http(s), so a relative or `javascript:` URL is named in the
staging report.

**`graph` set with no `base_url` is reported too**, rather than silently doing
nothing: the viewer is served from the site root, which needs a site to have a
root, and the reason a project's graph did not appear should not be something
they have to guess.

**Nested records get the parent's graph.** There is one layout for the whole
site, so a child whose pages kept Quartz's graph would be referring to a
component the layout no longer has.

## Alternatives considered

- **A Quartz component that fetches the JSON.** One copy over the wire instead
  of one inlined per page, and a natural fit for Quartz's own plugin model.
  Rejected for now: it needs a fetch in the viewer (which currently reads its
  data from the element), a second failure mode when the request fails, and a
  component written against a Quartz version this generator deliberately pins
  rather than tracks. The inlined cost is measured and small — a 7-node map is
  about 2 KB per page.
- **Keep both graphs.** Two graphs above every document's first paragraph,
  answering different questions, with the reader left to work out which is
  which. The lineage graph still appears, at the foot, where it is a place to
  go next rather than a toll.
- **A per-page override.** A project could name a different graph on different
  pages. No evidence anyone wants it, and it multiplies the validation surface;
  the config key is one line to extend if that changes.
- **Status quo — paste an embed snippet into a page.** strata-g already exports
  one, and it works. It puts the viewer's 25 KB in every page that uses it, it
  does not survive Quartz's markdown pipeline without the attribute carrier,
  and it is per page rather than per site.

## Consequences

A project that has designed a graph gets it everywhere for one config line. A
project that has not is unaffected — the key defaults to empty and Quartz's
graph stays.

**The graph is the same on every page, which is the trade.** Quartz's local
graph highlights where you are; this does not. Marking the current page's node
is possible at build time — the staging loop knows which page it is emitting —
and is deliberately not done here, because it would make the data island differ
per page and the value of the feature is that it does not.

**The panel scrolls on a short element.** Measured in a real build at 320px:
the side panel wants 198px and gets 143px in the stacked layout, so the legend
and the empty-state hint are below the fold until scrolled. Nothing is lost —
the panel is `overflow-y: auto` — and `graph_height` is the dial. Raising the
default would cost every page the height to save a scroll on one panel.
