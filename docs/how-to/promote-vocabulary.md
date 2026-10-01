# How to promote a vocabulary to a scheme

A vocabulary is a shorthand for a tiny scheme: named values, each with a
label and a blurb, and nothing else. Reach for this guide when a value needs
to say more than that:

- it needs a **parent** or children, because the values form a hierarchy;
- it needs **standing**, because a value can be retired and replaced;
- it needs **relations** of its own, or a **history** worth keeping;
- you are about to ask for a richer vocabulary feature.

Each of these means the field is typed as the wrong kind of thing. The
repair is to promote the vocabulary to a scheme: one document per value, and
every field that drew from it becomes a reference ([ADR-tmppzon2](../../record/decisions.d/ADR-tmppzon2.md)). The
reasoning is in [Vocabularies](../concepts/vocabularies.md#when-a-vocabulary-is-not-enough).

The examples below start from this record:

```yaml
vocabularies:
  statuses:
    Active: {}
    Superseded: {}
  area:
    runtime:
      label: Runtime
      blurb: the execution engine
    storage: {}
    queues: {}
schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    axis: area
    fields:
      status: {vocabulary: statuses}
      area: {vocabulary: area, many: true}
```

## 1. Write the migration spec

Promotion is a migration ([ADR-040](../../record/decisions.d/ADR-040.md)): it rewrites the config and documents
mechanically, so it is planned, dry-run and committed like a scheme rename.

```console
$ luria new migration --title "Areas become a scheme"
record/migrations.d/0001-areas-become-a-scheme.yaml
```

Uncomment the `promote_vocabulary` example, or replace the file with:

```yaml
title: "Areas become a scheme"
issue: ""

operations:
- op: promote_vocabulary
  vocabulary: area
  to: AREA
```

`dir:` and `output:` are optional and default from the prefix
(`record/areas.d`, `docs/areas`). The new scheme's `status` uses the
`statuses` vocabulary when one is declared; name another with
`status_vocabulary:`, and its in-force word with `active:`.

## 2. Read the plan

```console
$ luria migrate 0001 --dry-run
migration: Areas become a scheme
  promote vocabulary area -> AREA (record/areas.d, docs/areas)
  runtime -> AREA-001
  storage -> AREA-002
  queues -> AREA-003
  RFC.area: vocabulary -> grouped reference to AREA
  would sweep 0 file(s)
```

The values are numbered in the vocabulary's order. An open vocabulary's
values that are in use but never declared come last, alphabetically: a
reference is closed, so every value in use needs a document to point at.

## 3. Run it

```console
$ luria migrate 0001 --commit
migrated: 0 move(s), 0 cop(y/ies), 2 rewrite(s) in 2 file(s)
promoted: vocabulary area -> scheme AREA, 3 document(s) filed, 1 field(s) now reference it
committed 1fa348f699a4 and appended it to .git-blame-ignore-revs
$ luria index
$ luria lint
```

What changed:

- `record/areas.d/` holds one document per value. A value's `label` became
  the title and its `blurb` the summary and body. Its old spelling is kept as
  `slug:`, declared `unique`. The directory also gets the `_template.md` and
  `README.stub` a declared scheme starts with, so the next term is
  `luria new area`.
- The field became a reference:

  ```yaml
  references:
    area:
      scheme: AREA
      many: true
      required: false
      group: true
  ```

  `required` is written out because the defaults differ: a reference is
  required unless it says otherwise. `group: true`, or the field being the
  scheme's `axis` as here, keeps the views: each term gets a page listing
  the RFCs that cite it, at `docs/rfcs/area/AREA-001.md`.
- The documents hold codes (`area: [AREA-001, AREA-003]`). Only that
  frontmatter field is rewritten; prose is never swept for a value's
  spelling.
- The `area` vocabulary is gone. If it described itself (the nested
  `label`/`blurb`/`terms` form), that description became the scheme's
  `title` and `blurb`.

## 4. Give the terms what the vocabulary could not

The promotion is the point of entry, not the point. A hierarchy, for
example, is a converse pair on the new scheme and a chain to draw it:

```yaml
schemes:
  AREA:
    references:
      broader: {scheme: AREA, many: true, required: false, converse: narrower}
      narrower: {scheme: AREA, many: true, required: false, converse: broader}
chains:
  area-tree:
    scheme: AREA
    relation: broader
    output: docs/area-tree.md
    title: Areas, broadest first
```

```console
$ luria relate AREA-003 broader AREA-001
record/areas.d/AREA-003.md: broader += AREA-001
$ luria link --fix
wrote 1 back-reference(s) in 1 file(s)
```

`luria link --fix` writes the converse (`narrower: [AREA-003]` on AREA-001).
List the chain page in `docs/README.md`, as every page in `docs/` must be,
then `luria index` renders the tree:

```markdown
## From Runtime

- [AREA-001](../record/areas.d/AREA-001.md) — Runtime *(Active)*
  - [AREA-003](../record/areas.d/AREA-003.md) — queues *(Active)*
```

A term with no `broader` or `narrower` edge is in no line, so `storage`
does not appear on the tree page; it still has its own document and its
page under `docs/rfcs/area/`.

## What is refused

Promotion refuses rather than dropping what a reference cannot carry, so
the record never silently checks less ([DP-1](../../record/principles.d/DP-001.md)):

- a vocabulary behind a `status` field: standing is read off those words;
- a field with a `default`, `groups`, a `derive`, an `alert`, or any other
  key a reference does not have;
- a value declaring `primary_for`;
- a target prefix that already names a scheme.

Each refusal names the field and the key. Remove it, or carry it into the
new scheme by hand, then run the migration again.
