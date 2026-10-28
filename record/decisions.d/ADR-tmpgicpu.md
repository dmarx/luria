---
status: Proposed
title: 'A named path pattern may render a page of its matches'
version: 1
tags:
- record
- mechanism
date: '2026-10-13'
issue: '#373'
summary: >-
  A pattern with an `output:` (and optional `title:`) renders there as a
  view luria supplies, `luria:pattern.md.j2`: one row per match, one column
  per named node. It is a list, never a finding; `report: true` is the
  separate lint consumer, a pattern may have both, and acknowledged matches
  stay listed. Every path luria renders is checked against every other at
  load. Rejected: a renderer of its own, closing the issue as served by
  views, a `reports:` family, fixed placement, and grouping rows.
influenced_by:
- ADR-129
- ADR-130
- ADR-131
- ADR-035
---

# ADR-tmpgicpu: A named path pattern may render a page of its matches

## Context

[ADR-129](ADR-129.md) gave patterns one consumer, a chain, which needs a pattern from its
own scheme back to it and shows matches only as steps. Most of what a record
asks has no such shape: a thesis nothing objects to (one node with
`WHERE NOT`), an argument an Active claim undercuts (across schemes), a step
the record calls unfinished. A view template ([ADR-130](ADR-130.md)) can already list
them with `match(name)`, and `report: true` ([ADR-131](ADR-131.md)) makes them findings. The
question is who writes the list's template.

## Decision

**A pattern table may take `output:` and `title:`, and the page is a view
luria supplies.**

```yaml
patterns:
  unopposed:
    match: >-
      (c:CLAIM {role: 'thesis'}) WHERE NOT (c)<-[:objects_to]-(:CLAIM)
    blurb: Theses nothing in the record has objected to yet.
    output: docs/unopposed.md
```

- **One template, shipped.** At load, a pattern with an `output` adds a
  view on `luria:pattern.md.j2` (`luria/view_templates/`), with the
  pattern's name, source, blurb, title and named nodes as its values. The
  view loader tries the `luria:` prefix in the package before the project
  root, inside the same sandbox. The template writes codes bare, and the
  link fixer links them in the page's frame.
- **The page.** A heading (the title, else the name), the blurb, the
  pattern in a code span with its count, and a table: one column per named
  node, headed `var (LABEL)` in pattern order; one row per match, sorted by
  its codes; each cell the code and " — " title, `|` escaped by a `cell`
  filter. "No matches." replaces an empty table. An anonymous node is not a
  column, so two matches differing only in one are a single row; `match`
  now collapses them for every template. A pattern that names no node, or a
  `title` without an `output`, is refused at load.
- **Being a view**, it is written by `luria index`, held fresh by
  `--check`, kept out of the reference scan, and located on error as
  `patterns.<name>` with the template line, which its stamp names too.
- **A list, never a finding.** No lint class reads the page; whether a
  match matters is a judgement ([ADR-035](ADR-035.md)). `report: true` is the consumer that
  makes matches findings, and a pattern may have both. A `pattern-ok:`
  acknowledgement silences the finding and leaves the row: the page lists
  what matches, not what is outstanding.
- **One collision check for every renderer.** At load, every path luria
  renders is gathered: scheme outputs and indexes, the status reports
  (`reports.NAMES`, which the renderer reads too), the record description,
  the configuration reference, chains, views and pattern pages. Two that
  coincide are refused, naming both. Before, no pair was checked, and
  whichever view wins looks correct.

## Alternatives considered

- **A renderer of its own**, with a `pattern_match/2` predicate, a tuple
  reader in the logic core and a module writing the table. This was the
  first version of this decision. It duplicated `match` and needed its own
  freshness, exclusion and error locating, which a view already has.
- **Close [#373](https://github.com/dmarx/luria/issues/373) as served by views**, each record writing its own template.
  Nothing new in luria, but every record rewrites the same twenty-line table
  and the copies drift: one escapes `|`, another forgets the empty case.
- **A `reports:` family that names patterns**: another family for what one
  key does, where `output:` already means "renders a page here" on a chain.
- **Fixed placement under `docs/reports/`**, which holds luria's own
  reports; a record's questions belong in its own docs.
- **Grouping rows under their first column.** Deferred until needed.

## Consequences

- `View` gains a context and an origin; `luria views` lists a pattern page
  as `patterns.<name>`. A page must be listed in `docs/README.md` like any
  other page there (`check_docs_index`).
- **Tried on nucleation** (scratch copy of cf318d525, network off). With no
  `output`, `luria index` writes the same files and `luria lint` prints the
  same lines as luria `main`, its `report: true` and chain patterns
  included. With `unopposed` and
  `undercut: (g:ARG)<-[:undercuts]-(c:CLAIM {status: 'Active'})` added, 286
  of 361 theses are unopposed and 8 rows cover 6 undercut arguments, the
  same sets a script reading the frontmatter found. The status reports did
  not change, and the lint added only the docs-index entries for the two
  pages.
- `examples/argument-map` declares `unfinished`; its one row is INF-004.
