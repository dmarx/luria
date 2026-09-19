---
status: Active
title: "The record's sources may live in a database; the markdown tree is one export of it"
version: 1
tags:
- record
- mechanism
- load-bearing
date: '2026-09-19'
issue: '#110'
summary: >-
  `backend: {kind: sqlite, file: record.sqlite}` in `luria.yaml` and the
  record's sources are rows: `luria new` files one, the lint validates its
  fields, `luria index` renders the views from it, `luria export` refreshes
  the queryable tables in place and writes the markdown tree back out. The
  mechanism is one door — `luria/store.py` — through which every read and
  write of a source passes, routing by path, with a guard that no other
  module opens a file for itself. What a document *is* does not change:
  markdown with frontmatter, addressed by its path. Only where the bytes
  are kept does. Supersedes [ADR-116](ADR-116.md), which had made the database a view.
---

# ADR-tmpk52vs: The record's sources may live in a database; the markdown tree is one export of it

<!-- inactive-ok-file: ADR-116 — the decision this one supersedes; citing it retired is the point -->

## Context

[ADR-116](ADR-116.md) read [#110](https://github.com/dmarx/luria/issues/110) as a request to *ask the record questions* and answered
it with `luria export`: a SQLite view, generated from the files, never
written back to. It declined the other reading — the record itself in a
database — on the contribution model: one file per entry is what a
reviewer diffs, what branches never conflict on, what history attaches to.

The project's owner overruled the reading, not the reasoning. The
direction is that Luria's machinery should operate on the database
directly, so that a site can have a proper database behind it and the
markdown corpus can become an artifact exported *from* the record rather
than the other way round. The contribution-model costs [ADR-116](ADR-116.md) named are
real and are accepted for a record that chooses this backend; a record that
does not choose it keeps every property it had. This decision is about
making the choice possible without making the package know which one a
record made.

[ADR-116](ADR-116.md) also measured what the change would touch: about 150 filesystem
call sites in thirty modules, every writer doing text surgery on markdown,
every finding reported as `path:line`, every downstream consumer holding a
`Path` as a document's identity. That measurement is what shaped the
mechanism here — it said where *not* to cut.

## Decision

**A document is still markdown with frontmatter, addressed by its path.**
`record/decisions.d/ADR-012.md` remains the identity of a decision under
either backend: it is what a finding reports, what a link names, what the
fixer resolves a target from, and what every cache is keyed on. What moves
is only where the bytes behind that path are kept. That is what let the
change be a routing change rather than a rewrite: `field_edit` still edits
one frontmatter line and leaves the scaffold's comments alone, the lint
still reads a `status:` out of YAML, and a line number still means a line.

**One door.** `luria/store.py` is the only module that opens a path.
Every other module reads and writes through it — `store.read_text`,
`store.write_text`, `store.glob`, `store.rglob`, `store.exists`,
`store.unlink`, `store.move`, `store.revision` — and a test holds that
closed the way `test_one_reader` holds parsing: a module that opens a file
for itself would see the disk, and under the SQLite backend the disk is
not where the record is. It would read an empty directory and report a
clean record, which is the silent kind of wrong ([DP-001](../principles.d/DP-001.md)).

**Routing is by path, and only a source is routed.** A path under a
*source directory* — a scheme's `dir`, a journal's, a fragment
directory — goes to the configured backend. Everything else is a file
whichever backend is configured: docs pages, generated views, the code the
reference scan reads, `luria.yaml`, a staging directory. None of it is the
record. Under the SQLite backend a file that happens to sit on disk inside
a source directory is ignored entirely; two sources of truth is the one
thing a record must not have.

**The SQLite backend stores text.** One table, `sources`: the path, the
document as written, a revision counter that stands in for the mtime the
caches key on, and an autoincrement id that is the filing order the
fragment collector reads where it used to read `git log`. A directory's
revision is `(count, highest id, sum of revisions)`, because an id is never
reused and so two sets with the same count and highest id are the same
set — `(count, highest revision)`, the first cut, landed back on the same
key after an add-then-delete with a different member, and the listing
cache would have served the stale one.

**The store activates itself.** `config.current()` points it at the
loaded config's backend, and a store call that finds nothing active loads
the config to find out. Loading reads `luria.yaml` back through the store,
so a reentrancy flag makes that nested read see no backend and open the
file. Before any config, every path is a file, which is what `luria init`
needs.

**`luria export` converts in both directions.** The database it writes
holds `sources` beside the derived tables [ADR-116](ADR-116.md) introduced. Under the
files backend that is a copy of the tree; point `backend` at the file and
it *is* the record. Under the SQLite backend the default `--out` is the
record's own database, and the export refreshes the derived tables in
place with the sources untouched — the way `luria index` rewrites views
and never a source. `--markdown` writes every source as a file at its own
path, which is the tree a files backend would read: under SQLite, the
markdown corpus as an artifact of the record.

**Two states the lint refuses to be quiet about.** A SQLite backend whose
database is not there would read as an empty record and lint clean; it is
a violation naming the file and the export that makes one. A row under no
source directory is one nothing will ever list, because routing is by
path; it is a violation naming the row.

## Alternatives considered

- **A structured store** — frontmatter as columns, the body as one, every
  writer a structured update, the lint reading fields off rows. The
  "proper database" reading, and the one that turns the change into a
  rewrite of the product: every writer is deliberate text surgery so that
  the comments a scaffold ships survive a machine edit, and a directive is
  found by line. Columns are what the derived tables already are; making
  them the source too would need the text regenerated from them, and a
  regenerated document is one the author's comments are gone from. The
  text is canonical; the columns are derived from it on every export.
  Deferred rather than rejected: with the door in place, a structured
  backend is a third `kind`, and the text one would remain the reference.
- **A `Store` protocol with a `Document` that carries no `Path`.** The
  data-model refactor [ADR-116](ADR-116.md) declined. Still declined, on the same
  measurement: forty-nine consumers hold a `Path` as identity and none of
  them is wrong to. Routing by path kept every one of them, and the door
  is a module of functions rather than a class an implementation
  subclasses, because nothing needed the second shape.
- **Routing by an explicit flag at each call** — `store.read_text(path,
  source=True)`. Every one of the 150 sites would have to know which kind
  of path it held, which is the knowledge this decision exists to keep out
  of them. A path is a source or it is not, and the config says which.
- **Reading templates and stubs from disk under SQLite.** Tempting,
  because `_template.md` and `README.stub` are configuration rather than
  entries. But they live in the source directory, `luria new` reads them
  by path, and a rule that says "rows, except these names" is a second
  source of truth by another name. They are rows; `luria export` carries
  them across.
- **Status quo ([ADR-116](ADR-116.md)).** The view answers questions and nothing else.
  It does not let a site read from a database, and it leaves the markdown
  tree as the only thing the machinery can operate on, which is the
  constraint the owner asked to lift.

## Consequences

A record chooses its storage with two lines of config and every command
works on it: fired on a copy of this repository's record, converted and
with the tree deleted, `luria lint` reports the same sections, `luria
index` renders the same views (the record page gains exactly the row that
says `backend.kind`), `luria new` files a row, `luria export` refreshes
in place and `--markdown` writes 291 sources back out, and `luria site`
stages the vault. The equivalence is a test, over this record.

What it costs: the lint over this record takes about 4 seconds from the
database against about 3 from the tree — SQLite point lookups under a lock
where the file backend had the page cache. A record large enough to
notice has the derived tables to query instead. Two things git gave the
files backend for free do not exist for rows: `luria repair`'s alias
retirement reads a document's previous frontmatter from `git show`, and
so never fires under SQLite; and a migration's `.git-blame-ignore-revs`
entry has nothing to point at. Both are reported as absent rather than
faked.

What it obliges: every new reader or writer goes through the store, and
the boundary test says so if it does not. A third backend is a third
`kind` behind the same door.
