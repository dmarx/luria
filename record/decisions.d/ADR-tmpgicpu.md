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
  A pattern table may take an `output:` (and a `title:`), and the pattern
  then renders there as a view luria supplies: one template shipped in the
  package, `luria:pattern.md.j2`, reading the matches through the `match`
  every view template calls. One row per match, one column per named node
  in pattern order, each cell the document's code and title, rows sorted,
  and "No matches." when empty. Freshness, the reference-scan exclusion and
  render errors come from the view machinery. The page is a list, never a
  finding: `report: true` is the separate consumer that makes matches a lint
  class, a pattern may have both, and an acknowledged match stays on the
  page. Every path luria renders is now checked at load against every
  other. Rejected: a renderer of its own, closing the issue as served by
  views, a `reports:` family, fixed placement under `docs/reports/`, and
  grouping rows.
influenced_by:
- ADR-129
- ADR-130
- ADR-131
- ADR-035
---

# ADR-tmpgicpu: A named path pattern may render a page of its matches

## Context

[ADR-129](ADR-129.md) gave patterns one consumer, a chain. A chain needs a pattern that
starts and ends on its own scheme and has a hop, and it shows matches only
as steps inside its lines. Everything else a record wants to ask has no
shape a chain can draw: a thesis nothing objects to (a single node with
`WHERE NOT`), an argument an Active claim undercuts (across schemes), a step
the record calls unfinished. That last is where [ADR-129](ADR-129.md)'s built-in *Open*
list went: whether a partial match is unfinished depends on the schema, so
the record states it as a pattern, and the pattern needs somewhere to
render.

Two consumers already read patterns besides chains. A view template
([ADR-130](ADR-130.md)) can call `match(name)` and get every match as rows of documents.
And `report: true` ([ADR-131](ADR-131.md)) makes every match a row of a lint class. So the
list a record wants is already one template away. The question is who
writes that template.

## Decision

**A pattern table may take `output:` and `title:`.**

```yaml
patterns:
  unopposed:
    match: >-
      (c:CLAIM {role: 'thesis'}) WHERE NOT (c)<-[:objects_to]-(:CLAIM)
    blurb: Theses nothing in the record has objected to yet.
    output: docs/unopposed.md
    title: Unopposed theses
```

- **The page is a view luria supplies.** At load, a pattern with an
  `output` contributes a view whose template is `luria:pattern.md.j2`, one
  of luria's own (`luria/view_templates/`), with the pattern's name, source,
  blurb, title and named nodes as its values. The view environment loads a
  `luria:` name from the package and everything else from the project root,
  inside the same sandbox. The template reads rows through `match`, writes
  codes bare, and the link fixer makes the links in the page's own frame, as
  for any view.
- **What the page shows.** A heading (the title, else the name), the blurb,
  the pattern in a code span with a count of matches, then a table:
  - one column per named node, headed `var (LABEL)`, first occurrence only,
    in pattern order. An anonymous node is matched and not shown. A node
    named only under `WHERE NOT` never binds, so it is not a column, and a
    pattern that names no node is refused if it asks for a page;
  - one row per match, sorted by its codes column by column. Two matches
    that differ only in an anonymous node are one row, since nothing on the
    row tells them apart; `match` now collapses them for every template;
  - each cell is the code, linked, then " — " and the title, with `|`
    escaped by a `cell` filter any template may use;
  - "No matches." instead of a table when the pattern matches nothing.
- **What being a view gives it, with nothing written for it.** `luria index`
  writes it and `--check` calls it stale; `Config.is_generated` keeps it out
  of the reference scan, so a page listing retired documents does not fill
  the reference report; a render error names the pattern and the template
  line (`patterns.unopposed: luria:pattern.md.j2:5: …`). The stamp names
  `patterns.<name>` in `luria.yaml` rather than a template, because that is
  what a reader would edit.
- **A list, never a finding.** No lint class reads the page. Whether a match
  matters is a judgement ([ADR-035](ADR-035.md)). A record that wants its matches as
  findings says `report: true` ([ADR-131](ADR-131.md)), a separate consumer of the same
  pattern, and may say both. Then the page and the class list the same
  matches, and a `pattern-ok:` acknowledgement silences the finding without
  removing the row: the page is the list of what matches, not of what is
  outstanding.
- **One check for every output.** At load, every path luria renders is
  gathered: each scheme's output and index, the status reports
  (`reports.NAMES`, one table that both the renderer and this check read),
  the record description and configuration reference, chains, views and
  pattern pages. Any two that coincide are refused, naming both. Two views
  at one path overwrite each other on every build, and whichever wins looks
  correct. Before this, nothing checked any two of them.
- **Navigation is the record's.** A page under `docs/` must be listed in the
  docs front page, as every other page there must, and `check_docs_index`
  enforces that already.

## Alternatives considered

- **A renderer of its own**, beside `chains.outputs`, with its own clingo
  predicate (`pattern_match/2`), a tuple reader in the logic core and a
  module writing the table. This was the first version of this decision.
  It was a second implementation of what `match` already answers for every
  template, and then a third path to keep fresh, excluded and located on
  error. As a view it gets all three from code that exists.
- **Close [#373](https://github.com/dmarx/luria/issues/373) as served by views**, each record writing its own template
  over `match`. Nothing new in luria, but every record rewrites the same
  table of about twenty lines, and the copies drift: one escapes `|`,
  another forgets the empty case. Supplying the template keeps the page one
  key in the config.
- **A `reports:` family that names patterns.** It would separate the query
  from the page, and one pattern could feed several pages. But it is
  another family for what one key does. A chain already says "this renders
  a page here" with `output:`, so the same key on a pattern reads the same
  way. A record that wants a second page writes a view.
- **Fixed placement under `docs/reports/patterns/<name>.md`.** No path to
  choose, but no control over where the page lands, and `reports/` holds
  luria's own status reports. A record's questions belong in its own docs.
- **Grouping rows under their first column.** Easier to scan when one
  document has many matches. Deferred: a flat table sorts the same way, and
  nothing has needed grouping yet.

## Consequences

- `NamedPattern` gains `output` and `title`, and a pattern's keys are
  `match`, `blurb`, `report`, `output` and `title`. A pattern without
  `output` renders nothing. `View` gains a context and an origin for the
  views luria supplies; `luria views` lists a pattern page as
  `patterns.<name>`.
- **A property map must be folded or quoted in YAML.**
  `(c:CLAIM {role: 'thesis'})` puts `: ` inside a plain scalar, which YAML
  reads as a key. The configuration reference says so.
- **Tried on nucleation** in a scratch copy of its `main` (cf318d525), with
  `lint.network: never`:
  - With no pattern `output`, every file `luria index` writes and every line
    of `luria lint` is identical between luria `main` and this change.
    nucleation declares four `report: true` patterns and the `argued_from`
    chain pattern, so the parity covers both other consumers.
  - With `unopposed` and `undercut` (`(g:ARG)<-[:undercuts]-(c:CLAIM
    {status: 'Active'})`) added, `unopposed` lists 286 of 361 theses and
    `undercut` 8 rows across 6 arguments. A separate script reading the
    frontmatter got the same sets. The ninth undercutting claim, CLAIM-004
    against ARG-004, is Proposed, and the property map left it out.
  - The status reports were unchanged, so the `is_generated` exclusion
    holds. The lint added exactly two findings, the docs index missing the
    two new pages, which is the navigation rule above.
- `examples/argument-map` declares `unfinished`, and its one row is INF-004
  with the premise it has.
- Not decided here: grouping, a count badge, and the outline view that walks
  a pattern from a root across schemes.
