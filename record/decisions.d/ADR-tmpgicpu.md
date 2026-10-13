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
  then renders there: one row per match, one column per named node in the
  order the pattern writes them, each cell a link to its document with its
  title, rows sorted, and "No matches" when empty. Any pattern in the subset
  renders, across schemes and with zero hops, which is what a chain cannot
  show. The page is a report, never a lint failure, and is excluded from the
  reference scan. An output another view already renders to is refused at
  load. Rejected: a `reports:` family, fixed placement under
  `docs/reports/`, grouping rows, acknowledgement directives, and a lint
  class.
influenced_by:
- ADR-129
- ADR-035
---

# ADR-tmpgicpu: A named path pattern may render a page of its matches

## Context

[ADR-129](ADR-129.md) gave patterns one consumer, a chain. A chain needs a pattern that
starts and ends on its own scheme and has a hop, and it shows matches only
as steps inside its lines. On dmarx/nucleation, `argued_from` draws three
steps among twelve lines, and nothing lists them on their own.

Everything else a record wants to ask has no shape a chain can draw: a
thesis nothing objects to (a single node with `WHERE NOT`), an argument an
Active claim undercuts (across schemes), a step the record calls unfinished.
That last is where [ADR-129](ADR-129.md)'s built-in *Open* list went. It named six complete
arguments on nucleation as unfinished, because whether a partial match is
unfinished depends on the schema. The record states it as a pattern instead,
and the pattern needs somewhere to render.

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

- **The page.** It has a heading (the title, else the name), the blurb, the
  pattern in a code span with a count of matches, then a table.
  - The table has one column per named node, headed `var (LABEL)`, and one
    row per match.
  - Each cell is a link to the document from the page's own directory,
    followed by its title, with `|` escaped.
  - Rows are sorted by their codes, column by column, and repeats collapse.
  - A pattern with no matches says "No matches." instead of a table.
- **Columns are the named nodes of the match**, first occurrence only, in
  pattern order. Anonymous nodes are matched and not shown, as in a chain's
  "through". A node named only under `WHERE NOT` never binds, so it is not a
  column. A pattern that names no node is refused if it asks for a page.
- **Any pattern in the subset renders**: zero hops, across schemes, closures
  and `WHERE NOT`. The lowering shows `pattern_match(P, (X, …))`, one atom per
  match carrying the tuple of its named nodes. `logic` turns a clingo tuple
  into a Python tuple.
- **The page is generated in the strict sense.**
  - `Config.is_generated` excludes it from the reference scan, as it does
    chain pages. A page that lists retired documents would otherwise fill the
    reference report with citations nobody can annotate.
  - An `output` that a scheme, a status report, a chain or another pattern
    already renders to is refused at load. Otherwise two views at one path
    overwrite each other on every build, and whichever wins looks correct.
  - The status report names now live in one table (`reports.NAMES`), which
    both the renderer and this check read.
- **A report, never a failure.** No lint class reads the page. What a pattern
  matches needs judgement ([ADR-035](ADR-035.md)), and CLAUDE.md admits a check to the lint
  only when it is always wrong and mechanically fixable.
- **Navigation is the record's.** A page under `docs/` must be listed in the
  docs front page, as every other page there must; `check_docs_index`
  enforces that already. So the record links its pattern pages where it
  chooses, and luria adds no navigation of its own.

## Alternatives considered

- **A `reports:` family that names patterns.** It would separate the query
  from the view, and one pattern could feed several pages. But it is a
  seventh family for what one key does, and every page would need a second
  name. A chain already says "this renders a page here" with `output:`, so
  the same key on a pattern reads the same way.
- **Fixed placement under `docs/reports/patterns/<name>.md`.** No path to
  choose, but no control over where the page lands, and `reports/` holds
  luria's own status reports. A record's questions belong in its own docs.
- **Grouping rows under their first column.** It is easier to scan when one
  claim has many matches. Deferred: a flat table sorts the same way, and
  nothing has needed grouping yet.
- **Acknowledgement directives on rows**, so a judged match stops showing.
  Deferred: a pattern that matches too much is fixed by narrowing the
  pattern, which keeps the reason in the line where a reader sees it.
- **A lint class for non-empty pages.** Rejected for the reasons in the
  Decision.

## Consequences

- `NamedPattern` gains `output` and `title`, and the configuration reference
  shows them. A pattern without `output` renders nothing. Parity holds: on
  dmarx/nucleation, which declares `argued_from` with no output, every file
  `luria index` writes and every line of `luria lint` (network off) is
  identical before and after this change.
- **A property map must be folded or quoted in YAML.**
  `(c:CLAIM {role: 'thesis'})` puts `: ` inside a plain scalar, which YAML
  reads as a key. The configuration reference says so and uses `>-`. The
  configuration-reference test that every YAML example parses caught this in
  the first docstring.
- **Tried on nucleation** in a scratch copy before trusting it:
  - `unopposed` listed 115 of 175 theses, and `undercut` listed 8 arguments
    with the Active claims that undercut them. Both counts match an
    independent read of the frontmatter. The ninth undercutting claim is
    Proposed, and the property map left it out.
  - The reference report was unchanged.
  - The lint failed until `docs/README.md` linked the two new pages, which is
    the navigation rule above, working.
- `examples/argument-map` declares `unfinished`, and its one row is INF-004
  with the premise it has.
- Not decided here: grouping, acknowledgements, a count badge, and the
  outline view that walks a pattern from a root across schemes.
