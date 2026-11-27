---
status: Proposed
title: 'The site is a bespoke shell that renders the record in the browser, replacing Quartz'
version: 1
tags:
- architecture
date: '2026-11-26'
summary: >-
  Proposed. Replace the Quartz build behind `actions/site` with mantle
  (github.com/dmarx/mantle), a publisher of its own that luria feeds but
  does not contain: a small static shell that fetches a document's markdown on
  demand and renders it in the visitor's browser, with search and graph data
  sharded so no page loads the whole record. Grounded in CI history:
  nucleation's site step grew from 61 s to 2731 s between 2026-09-25 and
  2026-11-25, near-linear in a 442.9 MB artifact (r = 0.985, n = 18), and
  Quartz's emit phase is 84% of the build. Rejected: tuning Quartz (it
  pre-renders every page on every merge, which is the cost itself), another
  static generator (the same shape, faster), and the status quo.
---

# ADR-tmpj6kwd: The site is a bespoke shell that renders the record in the browser, replacing Quartz

## Context

[ADR-042](ADR-042.md) published the record as a Quartz vault and [ADR-101](ADR-101.md) moved it to Quartz 5.
Every page is rendered to HTML at build time, along with a social-card image
per page, a full-text `contentIndex.json`, and a graph view on every page.
That was cheap at luria's size. It is not cheap at the size records reach.

**Measured, from CI history.** Every `pages.yml` run of the three records
that publish with `actions/site` and whose Actions history this analysis
could read, 2026-08 to 2026-11. Durations are from Actions step timestamps,
artifact bytes from the `upload-pages-artifact` log:

| record | real builds | median | trend |
|---|---|---|---|
| luria | 334 | 78 s run, 83.5 s site step | flat, about 90 s since 2026-09 |
| nucleation | 336 | 946 s run, p90 1798 s, max 3988 s | monthly median 134.5 s (Sep) → 871 s (Oct) → 1634 s (Nov) |
| mathematics-of-meaning | 0 of 157 | — | every run fails inside `luria site` (a frontmatter `ScannerError`); Quartz is never reached |

nucleation's site step against its artifact, over two months:

| date | site step | artifact |
|---|---|---|
| 2026-09-25 | 61 s | 8.6 MB |
| 2026-10-17 | 811 s | 150.9 MB |
| 2026-11-13 | 1548 s | 327 MB |
| 2026-11-25 | 2731 s | 442.9 MB |

The 2026-11-25 build (12,799 input files, 49,341 output files) split as
`luria site` 299.4 s, Quartz parse 373.7 s and Quartz emit 2038.0 s, which is
84% of the build step. npm, node setup, pip and checkout came to under 30 s
together. No readable log shows an out-of-memory failure. At this size the
failures are in **deploy**: three `deploy-pages` runs hit their 10-minute
limit (2026-11-04, -06, -10) on 360–440 MB artifacts. Of 79 cancelled runs,
the one inspected had finished its build and was superseded at deploy, so
its build was thrown away.

**What the output is made of.** One local build each of luria's and
strata-g's records, measuring files, not time. Per-page social cards are 534
of luria's 1,627 output files. `contentIndex.json` is 2.9 MB (luria) and
4.2 MB (strata-g), and the search and graph components fetch it on page load.
The largest single pages are the collected changelog and devlog books, at
0.5–1.2 MB of HTML each. nucleation's sources are 159 MB of markdown; 66 MB
of that is generated views, and its largest single view,
`docs/literature/README.md`, is one 4.9 MB markdown table. Nothing in the
current build keeps a page that size from being what a visitor opens.

**The cost is per page, so it only grows.** Every build re-renders every
page with the same per-page extras. A record that gains a hundred documents
a day gains a hundred documents' worth of build time a day.

**What the timing data cannot yet say.** Quartz runs its emitters
concurrently and logs only a rounded total. So until the weekly timed build
has run (`actions/site`'s `timings`, added alongside this proposal), it is
unmeasured how emit time splits between page HTML, social cards, the content
index and the graph. The case for replacing Quartz doesn't rest on that
split. The order of the work does.

## Decision

*Proposed.* `actions/site` publishes a **shell**, not a rendered site.

**Requirements**, each traceable to a measurement above:

- **R1, build cost tracks metadata, not rendered pages.** Publishing does
  work proportional to the record's metadata, or to what changed, never to
  every page's rendered size. Target: a nucleation-sized record builds in
  under 2 minutes, against 2731 s on 2026-11-25.
- **R2, small deploy.** The artifact is the shell plus whatever data can't
  be fetched from the repository. Target: under 50 MB for nucleation, against
  442.9 MB, well inside `deploy-pages`' limit.
- **R3, bounded page weight.** No page load fetches the whole record. Search
  and graph data are sharded or queried. A view above a size threshold is
  paginated or virtualized, not rendered whole. First paint needs only the
  document asked for.
- **R4, same URLs.** Paths stay as [ADR-042](ADR-042.md) made them, and anchors stay
  the ones luria owns ([ADR-100](ADR-100.md)), so existing links into the published site keep
  resolving, including the ones strata-g's luria intake reads.
- **R5, one renderer.** One implementation renders markdown, shared by the
  site and anything else that shows a record in a browser. A second resolver
  would drift from luria's ([DP-004](../principles.d/DP-004.md)).
- **R6, observable.** The weekly timed build keeps reporting step durations,
  phase totals and output bytes, so R1–R3 are checked against a series rather
  than asserted once.
- **R7, honest failure.** A document the shell cannot fetch or render says so
  on the page ([DP-001](../principles.d/DP-001.md)). A blank page is not a state.
- **R8, no server.** GitHub Pages only. That means no response headers, so no
  cross-origin isolation, and no server-side code.

**The first increment.** `luria site` writes a manifest: every document's
path, code, title, scheme, status and edges. The shell reads it, and fetches
a document's markdown when that document is opened, either from the deployed
bytes or from `raw.githubusercontent.com` at the published commit. Views stay
committed markdown for now ([the views ADR](ADR-tmpnqetk.md) changes that), so this
increment needs no new data format. Graph and search read the manifest,
sharded by scheme. Brand settings ([ADR-043](ADR-043.md)) carry over as configuration.

**Where it lives.** The shell is **mantle**
(`https://github.com/dmarx/mantle`), a separate project meant to be usable
without luria. That fixes the boundary: mantle defines the manifest it reads
and renders any markdown tree described by one, while luria's side is a
producer. `luria site` writes a mantle manifest from the record, the same
readers and resolver as everything else ([DP-004](../principles.d/DP-004.md)), and `actions/site` calls
mantle's build. luria-specific meaning (schemes, statuses, typed edges)
travels as manifest data mantle displays generically, not as code in mantle.

## Alternatives considered

- **Tune Quartz**: drop the social-card emitter, the graph or the content
  index. Each may buy a constant factor, and the weekly timing will say how
  much. It is the right *stopgap* if the record grows faster than the
  replacement arrives. But the build still renders every page on every merge,
  so R1 is out of reach by construction, and each Quartz major version has
  needed a migration ([ADR-101](ADR-101.md)).
- **Another static generator** (Hugo, Eleventy, MkDocs): faster per page,
  same total shape. Hugo might bring nucleation from tens of minutes to
  minutes, but it still deploys every rendered page (R2) and ships a
  whole-record search index (R3).
- **Incremental Quartz builds with a cached output**: Quartz's incremental
  path is built for `--serve`, not for CI. A cache across Actions runs is one
  more moving part, and the deploy is still 443 MB.
- **Status quo**: nucleation's site step grew about 45× in two months
  (61 s → 2731 s). On that trend it reaches GitHub-hosted runners' 6-hour job
  limit within months, and deploys already time out.

## Consequences

- A published page needs JavaScript. A record that must read with scripts off
  needs a fallback; the cheap one is a plain list of links to the
  repository's rendered markdown.
- Search engines index a shell less well than static HTML. Where that
  matters, prerendering only the index pages is a bounded fix, not a return
  to rendering every page.
- The front-end code (a build, a test runner, a pinned dependency set)
  lives in mantle, so luria stays Python only. The cost moves to a contract:
  the manifest schema is an interface between two repositories, versioned,
  and a luria release names the mantle versions whose manifest it writes.
- The Quartz-specific code (the `quartz.config.yaml` writer in `site.py`, and
  `site_page.py`'s frontmatter for `note-properties`, [ADR-121](ADR-121.md)) retires once the
  shell reaches parity. [ADR-042](ADR-042.md)'s path rules stay.
- mathematics-of-meaning has never published, for a reason unrelated to
  Quartz. That crash is its own bug and shouldn't wait on this.
