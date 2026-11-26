---
status: Proposed
title: "Views render in the visitor's browser from the graph, and are not committed as markdown by default"
version: 1
tags:
- architecture
date: '2026-11-26'
summary: >-
  Proposed, and the third step after the [site shell](ADR-tmpj6kwd.md) and the [LadybugDB
  export](ADR-tmpc1dme.md). The published site computes a view (a scheme's index, a field
  value's page, a pattern's page, a chain) when a visitor opens it, by
  running its selection against the exported graph and rendering the view's
  template in the browser. `luria index` stops committing those views as
  markdown by default; a record can still ask for them. In nucleation,
  generated views are 66 MB of 159 MB of markdown, and the largest is 4.9 MB.
  Rejected: keeping committed views as the site's source (the size and the
  bot commits stay), and computing views on a server (Pages has none).
---

# ADR-tmpnqetk: Views render in the visitor's browser from the graph, and are not committed as markdown by default

## Context

Generated views are committed to the default branch ([ADR-068](ADR-068.md)), rebuilt on
every merge, and published page by page. In nucleation they are 1,088 files
and 66 MB, 42% of the repository's markdown. The largest,
`docs/literature/README.md`, is a single 4.9 MB table, and
`docs/literature/status/Active.md` is 3.3 MB. These are the pages most
likely to be what a browser chokes on: Quartz renders each one whole, with
the graph and the content index on top.

A view is a selection plus a rendering. The selection is declared in
`luria.yaml` (a scheme, a field value, a pattern, a chain), and the rendering
is luria's or a project's Jinja template ([ADR-130](ADR-130.md)). With the record exported
as a graph ([the export ADR](ADR-tmpc1dme.md)), both halves can run where the view is
read.

## Decision

*Proposed, in two halves:*

1. **The site computes views.** For each view `luria.yaml` declares, the
   manifest records its selection as a query, and the shell runs it against
   the exported database when the page opens. It renders the rows with the
   view's template, paginated past a threshold (the [site
   ADR's](ADR-tmpj6kwd.md) R3). Templates luria ships are ported to the
   browser. A project's Jinja template either renders through a Jinja
   implementation in JavaScript (Nunjucks is close but not exact), or the
   project keeps that view committed. Which one is an open question, settled
   on a real project template, not in advance.
2. **`luria index` stops committing views by default**, once the site renders
   them. The generated files a reader needs *in the repository* keep being
   written: the `CLAUDE.md` bootloader, the README's generated regions, and
   the record description. A record that wants committed markdown views
   (for GitHub's own renderer, or offline reading) sets one flag, and gets
   today's behaviour.

`luria lint` reads sources ([ADR-068](ADR-068.md)), so it needs no view on disk, and the
links checked into prose still resolve against the paths a view *would*
have. The site serves a computed view at the same URL ([the site ADR's](ADR-tmpj6kwd.md)
R4).

## Alternatives considered

- **Keep committed views as the site's source.** This is the site ADR's first
  increment, and is fine as one. As the end state it keeps the 66 MB, the
  per-merge bot commit, and the 4.9 MB page.
- **Compute views at build time, but only into the artifact.** That removes
  them from git but not from the deploy (R2) or the page weight (R3).
- **A server that renders views.** GitHub Pages serves files only, and a
  server is something every adopter would then have to run.

## Consequences

- A view is no longer readable on github.com without the site, unless the
  record opts back in. For a project whose readers live on GitHub, that is a
  real loss, and the reason the flag exists.
- Templates now have two renderers, luria's Jinja and the browser's. The two
  are held together by a test that renders each luria-shipped view both ways
  over this record and compares the output.
- Drift between "what the view says" and "what the record says" disappears
  for readers of the site: the view is computed from the same export, at the
  same commit.
