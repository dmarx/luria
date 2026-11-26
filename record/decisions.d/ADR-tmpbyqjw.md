---
status: Proposed
title: "A journal may be consumed into its books on the project's schedule, and consumption refuses entries a review still holds"
version: 1
tags:
- architecture
- record
date: '2026-11-26'
influenced_by:
- ADR-020
summary: >-
  Proposed. A journal that sets `consume:` has its entries folded into its
  existing period books by `luria collect --dir <journal dir>`, and then
  deleted. Folding keeps each entry's timestamp anchor and rewrites links
  that pointed at the entry. From then on the book is the entry's source:
  append-only, never regenerated. Only closed periods are consumed. A
  configurable hold keeps back entries a review still needs (for a record
  running retrospectives: `retro`-tagged entries filed after the latest
  accepted RETRO's coverage). Collection skips and names them, and the lint
  fails if a book holds one. When collection runs is the workflow's cron, not
  luria's configuration ([DP-tmpl4h6h](../principles.d/DP-tmpl4h6h.md)). Rejected: partitioned fragment targets (a
  second period mechanism), consuming open periods, and an unconditional
  consume.
---

# ADR-tmpbyqjw: A journal may be consumed into its books on the project's schedule, and consumption refuses entries a review still holds

## Context

[ADR-020](ADR-020.md) made a journal an append-only stream of dated entries that persist,
with books generated from them. A record that files several entries a day
accumulates thousands of files: nucleation's sources are 13,386 markdown
files. The owner wants entries folded into a smaller set of aggregate files
on a schedule, like the changelog's fragments.

The changelog's collector consumes into **one** file and orders by commit
time, which a rebase can change. A journal already has what that collector
lacks:

- **a stable order:** each entry carries its own timestamp;
- **a partition:** books by `granularity`;
- **a stable address per entry:** the `<a id="<timestamp>">` anchor every
  book already writes.

So consumption needs no new period mechanism. It needs the books to become
the source.

One hazard comes with it. A record that runs retrospectives (nucleation's
NU-[ADR-115](ADR-115.md), mantle's retrospective decision) finds a review's notes by tag among the
entries filed since the last review. Consuming a note before a review has
read it hides it in a book the review step doesn't search.

## Decision

*Proposed.*

```yaml
journals:
  devlog:
    dir: record/devlog.d
    output: docs/devlog
    granularity: month
    consume:
      hold:                        # optional
        tags: [retro]
        until_covered_by:
          scheme: RETRO
          field: covers_through    # a timestamp the review read up to
          status: Accepted
```

**`luria collect --dir record/devlog.d`:**

1. **It takes only closed periods.** It takes the entries whose book period
   has ended, so a book is consumed into once, whole.
2. **It applies the hold.** An entry matching `hold.tags` is held while its
   `created` is later than the greatest `covers_through` among the documents
   of `until_covered_by.scheme` with that `status`. Held entries are skipped
   and named in the output, never consumed silently ([DP-001](../principles.d/DP-001.md)).
3. **It folds each remaining entry into its period's book.** It writes the
   rendering the book already uses (anchor, heading, tags, body), in
   timestamp order, appending to a book that already holds consumed entries.
4. **It rewrites links.** Every link that pointed at an entry file is
   rewritten to `<book>#<timestamp>` through the one resolver, and the entry
   is deleted.
5. **With `--commit`, it commits** the books, the rewritten links and the
   deletions together.

**Afterwards:**

- **A consumed book is a source.** `luria index` no longer regenerates it.
  It keeps generating only the journal's index page, which lists books and
  any entries still pending.
- **A book is append-only.** The lint fails if a consumed entry's rendering
  changes, and if a book holds an entry the hold should have kept back. The
  second check needs no state: the entry's tags, its timestamp and the
  reviews' coverage are all in the tree.
- **The retro step reads both** pending entries and books. Consumed entries
  keep their tags in the book, so a search by tag finds them either way.

**Cadence is the project's CI.** Each consumed journal, and the changelog,
gets its own scheduled job (`luria collect --dir …`) at whatever cron suits
it. `luria.yaml` says what consuming means, and the workflow says when it
happens ([DP-tmpl4h6h](../principles.d/DP-tmpl4h6h.md)).

**The changelog is not changed by this decision.** It may later become a
consumed journal itself, which would give it periods and a stable order, but
that is a separate choice.

## Alternatives considered

- **Partitioned targets for fragment directories.** It would work, but it
  is a second period mechanism beside books, and fragments' order is still
  commit time.
- **Consume open periods too.** Then a month's book is written into by
  several collections, and a reader can't tell a complete book from a
  partial one.
- **Consume unconditionally, and let reviews read books.** That works only if
  every review remembers to look there. The hold makes "not yet reviewed" a
  property of the tree that the lint can check, which is the kind of rule
  luria exists to make cheap.
- **Make the hold a pattern instead of keys.** Patterns
  ([ADR-129](ADR-129.md)) select documents, and journal entries aren't scheme documents. If they
  become queryable, the hold can be restated as one.

## Consequences

- A record that consumes its journal goes from one file per entry to one
  file per period, while every entry stays addressable by its timestamp.
- RETRO schemes that want the hold gain a `covers_through` field. mantle's
  [ADR-002](ADR-002.md) and SOP-001 will name it when mantle adopts this.
- The changelog's `collect` job and a journal's consumption are separate
  jobs, so each can run on its own schedule.
