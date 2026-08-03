---
status: Active
tags:
- record
- mechanism
date: '2026-08-03'
influenced_by: []
summary: >-
  Design principles are decomposed into one fragment each, with frontmatter
  carrying a `version`, the decisions that shaped them (`influenced_by`), and an
  `origin` note; `docs/design-principles.md` becomes a generated view. This is
  the same move as the decision index, not a third mechanism — a scheme gains a
  `render` setting, `index` (a table plus tag pages) or `document` (bodies
  concatenated). The distinction that matters is not frontmatter but whether the
  sources survive: collected views (changelog, devlog) consume their fragments
  and can only be appended to; generated views are a pure function of sources
  that persist, which is the only reason `luria lint` can detect a stale one.
  Rejected: collecting principles like a changelog (the fragments would be
  deleted, taking the version history with them, and staleness would become
  undetectable), and leaving the document hand-maintained (a lock and a drifting
  projection, [DP-2](../design-principles.md) and [DP-3](../design-principles.md)).
---

# ADR-012: Principles are fragments too, rendered as a document

## Context

`docs/design-principles.md` was one hand-maintained file. Every principle added
or revised edited it in the same place, which makes it the lock
[DP-2](../design-principles.md) names — the same shape as the changelog and the
decision index before them.

It also could not answer two questions the principles themselves raise. **Which
decisions produced this?** — the evidence that stops a principle reading as
taste, per [ADR-009](adr-009-extracted-with-provenance.md). And **has this been
revised?** — [DP-2](../design-principles.md) and [DP-3](../design-principles.md)
were both first written scoped too narrowly and only generalized after a second
instance forced it, which is the single most useful thing either of them
teaches, and a flat document had nowhere to say so.

## Decision

**One fragment per principle, in `docs/principles/`, with frontmatter; the
document is generated from them.**

```yaml
status: Active
version: 2
influenced_by: [ADR-002, ADR-004]
origin: >-
  Fragments assembled into a changelog; then the identical conflicts recurring
  on the narrative log months later; then the decision index.
```

- **`version`** belabours the point that principles are living documents. A
  revised principle *says* it was revised, and `history:` records what changed.
- **`influenced_by`** is the inverse of the citation direction: decisions cite
  principles, and this names the decisions whose experience *produced* the
  principle. Rendered as followable backlinks.
- **`status`** brings principles under the same vocabulary as decisions
  ([ADR-003](adr-003-status-vocabulary-and-frontmatter.md)), so a retired
  principle still cited is reportable exactly like a superseded decision.

A scheme now declares how its view is rendered:

| `render` | output | right when |
|---|---|---|
| `index` | a table of links, plus per-tag pages | documents are browsed and read one at a time |
| `document` | bodies concatenated into one page | the set is read *as a whole* |

Principles are read as a whole — people cite "DP-3" and then read it among its
neighbours — so they render as a document. Decisions are read one at a time, so
they render as an index. **This is the first exercise of
[ADR-006](adr-006-reference-schemes-are-configured.md)'s claim that a second
scheme is a config entry and a directory**, and it held: no scanner changed.

### Generated, not collected — and the frontmatter is not the difference

The obvious objection is that this is what the changelog collector already does:
concatenate fragment bodies into a view. Nearly. The difference is not that one
strips frontmatter — it is **whether the sources survive**, and it is already
the distinction [ADR-002](adr-002-fragments-and-generated-views.md) draws:

- A **collected** view (changelog, devlog) *consumes* its fragments. They are
  deleted; the view accumulates; it can only ever be appended to. `CHANGELOG.md`
  cannot be rebuilt, because the fragments that produced last month's entries no
  longer exist.
- A **generated** view (decision index, principles document) is a pure function
  of sources that persist. It is rebuilt from scratch every time, which is the
  *only* reason `luria lint` can tell that one is stale.

Principles must be generated: they are durable, numbered, versioned and
revisable, and the frontmatter is precisely what makes them so. Collecting them
would delete the fragments — taking the version history with them — and would
make a hand-edit to the assembled document undetectable, which is the property
[ADR-004](adr-004-generated-decision-index.md) exists for.

The two conventions encode that difference honestly, which is worth noticing
rather than tidying away: a collected view keeps an **insert marker** in its
output, because collection appends to it again next time; a generated view uses
a **`{placeholder}` in a stub**, which does *not* survive into the output,
because generation rewrites wholesale. Same idea, opposite persistence, and each
convention is shaped by which one it is.

## Alternatives considered

- **Collect principles like a changelog.** The shape matches; the semantics
  don't. See above — deleted sources, no staleness detection, no version
  history.
- **Leave the document hand-maintained.** A lock and a drifting projection at
  once, which is exactly the pair [ADR-004](adr-004-generated-decision-index.md)
  removed from the decision index.
- **Keep the frontmatter in the rendered document.** Honest, and unreadable —
  the document's job is to be read start to finish. The metadata is rendered as
  one italic line per principle instead: version, backlinks, origin, and the
  status when it isn't `Active`.
- **A separate `luria principles` command.** A second command for the same
  operation, which is [DP-4](../design-principles.md)'s definition of a latent
  divergence. `luria index` regenerates every scheme's view, so a newly
  configured scheme is covered by the staleness check the moment it exists.

## Consequences

- Adding or revising a principle is one file, and the assembled document can
  never silently disagree with its sources.
- `link_base` had to learn a second kind of fragment: a document-rendered
  scheme's sources assemble into a file one directory up, so links written in
  them resolve from *there* — the same trap
  [ADR-005](adr-005-references-are-hyperlinks.md) records for changelog
  fragments, arriving from a direction nobody was watching. Two links in the
  first eight fragments were already wrong; the lint caught both.
- The docs-index check had to stop demanding index entries for scheme *sources*.
  A reader opens the view, not the fragments.
- `version` is hand-maintained, and therefore drifts by
  [DP-3](../design-principles.md)'s own argument. It is fail-loud rather than
  fail-stale — a stale version number is visible in the rendered line, right
  next to the text it describes — but it is a hand-maintained field and the
  honest thing is to say so here rather than pretend otherwise.
