---
# Don't copy this file by hand — run `luria new adr`, which assigns the
# identity and fills in the fields a machine can compute. WHICH identity
# depends on the scheme's `allocate` mode: `filing` (the default) takes the
# next free number on the spot, `merge` mints a temporary code that
# `luria concretize` numbers where merges serialize (ADR-049). The kinds are the
# config: every scheme, fragment directory and journal in luria.toml is one, so
# `luria new <kind>` works for a scheme the moment it is declared.
#
# Numbering is sequential and carries information (it's the order decisions were
# made). The filename is the code and nothing else; the title goes in `title:`
# below, where correcting it costs an edit rather than a rename plus every link
# (ADR-013).
#
# This frontmatter is the ONLY place these facts live. The index and the per-tag
# pages are generated from it (ADR-004) — never edit them by hand; run
# `luria index`.

# Active | Proposed | Deferred | Superseded | Rejected, optionally " — <note>".
# Supersede when the CHOICE changes: set the old one to
# `Superseded — by [ADR-tmpcso13](ADR-tmpcso13.md)` and leave its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Proposed'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpcso13:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'A frontmatter field can be backed by a scheme-local controlled vocabulary'

# Which revision of this decision's claim you are reading. Standard frontmatter
# for every scheme, and it moves rarely here: a decision that CHANGES is
# superseded by a new one, not edited. Bump it when the same choice is restated
# more broadly — scope widened, wording generalized — and say what changed in a
# `history:` entry. Shown in the index only when it is not 1.
version: 1

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
- record
- mechanism

date: '2026-09-03'

# Optional. The issue(s) this decision came from: '#123'.
issue: '#141'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
summary: >-
  A downstream world-building record carries `worlds: [A, C]` on 37 of 75
  entries, drawn from six values, absent meaning B, with a view per value
  wanted — a field that is not a reference (the values are not codes),
  not a tag (it is a second axis, not the browsing pile) and not a status
  (closed and single). Proposed: a scheme declares the field under
  `[luria.schemes.X.vocabularies.NAME]` with `many`, `required` and
  `default`, the values live in `NAME.yaml` beside the records shaped like
  `tags.yaml`, the lint holds the field to the vocabulary, the default is
  an effective value that never rewrites the source, and `luria index`
  renders a page per value. `statuses.yaml` and `tags.yaml` become the
  first two instances of the shape rather than special cases. Considered
  and priced: tags plus a tag group, a scheme of six documents cited by a
  plural reference, inline values in TOML, and implicit `*.yaml` wiring.

---

# ADR-tmpcso13: A frontmatter field can be backed by a scheme-local controlled vocabulary

<!-- A Proposed decision on a draft pull request (ADR-052): merge flips it
     Active, close files it Rejected with the body intact. The writeup argues
     both directions; the open questions at the end are where the verdict is
     expected to land. -->

## Context

A record built for narrative world-building adopted Luria and reported the
first measured needs from outside the project's original domain. One of
them fits nothing the configuration can say.

Its scenes carry a field:

```yaml
worlds:
  - A
  - C
```

on 37 of 75 entries. The values come from a closed set of six trajectories.
An absent field means *world B*, by a convention every author knows and no
reader can discover. And the record has an immediate consumer waiting: a
view per world, the way the decision index has a page per tag.

Nothing in the record's vocabulary holds this field.

- **It is not a reference.** The values are not codes; there is no
  document for `A` to resolve to, and making one is the alternative priced
  below.
- **It is not a tag.** `tags:` is the browsing pile, open by design
  ([ADR-054](ADR-054.md) deferred even a `closed` flag), and the scenes already carry
  topical tags. Folding six world values into the same list makes one
  field mean two things, which is the smell the modeling guide names as
  the reason to split a scheme — and it cannot say *absent means B*.
- **It is not a status.** A status is one word from a closed set of five
  ([ADR-003](ADR-003.md)); this is a set of values from a closed set the project
  defines.

What it *is* has two precedents in the scheme directory already.
`statuses.yaml` ([ADR-056](ADR-056.md)) is a closed single-valued vocabulary backing the
`status:` field; `tags.yaml` is an open multi-valued vocabulary backing
`tags:`. Each pairs a frontmatter field with a scheme-local YAML file that
says what the values mean, and each was built as a special case. The world
record is the third instance, and it is the one that shows the pattern.

The compiled contract ([#142](https://github.com/dmarx/luria/issues/142)) is where this lands. A `Field` today carries
`required`, a `reference` scheme or none, and since [ADR-tmp0sz8p](ADR-tmp0sz8p.md) a `many`
shape. A reviewer of that work observed that `reference: str | None` is a
type wearing a boolean's clothes: `Any`, `Ref[Scheme]`, and now a third
case. This decision adds the third case and names the type.

## Decision

**A scheme may declare a frontmatter field backed by a controlled
vocabulary.** The declaration is explicit, in the scheme's table, and
names the field:

```toml
[luria.schemes.SCENE.vocabularies.worlds]
many     = true          # a list of values; default false, one value
required = false         # default false; required + many means non-empty
default  = ["B"]         # the effective value when the field is absent
```

**The values live beside the records**, in `worlds.yaml` in the scheme's
directory, shaped exactly like `tags.yaml`:

```yaml
A:
  label: The unbroken line
  blurb: the trajectory where the treaty holds
B:
  label: The default
  blurb: where most scenes sit; an absent field means this
```

The file is the vocabulary; the TOML table is the wiring. That split is the
one [ADR-054](ADR-054.md) and [ADR-056](ADR-056.md) already draw — meanings in YAML with the records,
rules in `luria.toml` — and the placement rule from [#141](https://github.com/dmarx/luria/issues/141) says the same: a
value's label is explained by pointing at the value; `many` and `default`
are facts about the field.

**The vocabulary is closed.** A value not in the file is a lint finding,
naming the file. This is the `statuses.yaml` posture, not the `tags.yaml`
one: a controlled vocabulary that accepts unknown values is a pile of
labels, and the record has `tags:` for those.

**A default is an effective value, not a rewrite.** An absent `worlds:` is
read as `["B"]` by every consumer — the lint, the index, the graph — and
the source file is left absent. Two things follow. The convention becomes
discoverable where the contract renders: the record page's *what an entry
must carry* lists `worlds — one or more of A, B, C, D, E, F; absent means
B`, and a finding about the field cites the same line. And `default` is
distinct from `required = false`: optional means *no value is a meaningful
state*; default means *no value written is this value*.

**The compiled contract grows a type.** `Field.reference` becomes one case
of what a field holds:

```text
Field
  name
  required
  many
  holds:   Any | Ref[SCHEME] | Vocabulary[NAME]
  default: value | None
```

`requires` compiles to `Any`, `references` to `Ref`, and this table to
`Vocabulary`. The lint, the record page and the edge derivation read the
type; nothing else changes shape. No edges are derived from a vocabulary
field — its values are not nodes.

**The index renders a page per value.** For an index-rendered scheme,
`luria index` writes `<view>/worlds/A.md` beside the tag pages, listing the
entries whose effective value includes `A`, and the scheme's index links
the set the way it links the tag pages. This follows the existing axis
rather than adding a switch: declaring the vocabulary is the opt-in, and
the consumer is the reason the record declared it.

## Alternatives considered

- **Tags plus a tag group.** Put the six values in `tags.yaml`, declare
  `tag_groups.worlds` over them, and the tag pages are the per-world views
  for free. Everything works today except the two facts that matter: a
  group cannot say *absent means B*, and `tags:` now carries two axes in
  one list — a reader of a tag page cannot tell a world from a topic, and
  the world record has both. This is the cheapest option and it is the
  shape the record arrived in flight from.
- **A `WORLD` scheme, cited by a plural reference.** Six documents,
  `worlds = { scheme = "WORLD", many = true }`, and the typed edges'
  *Cited as `worlds` by* on each world page is the per-world view,
  unbuilt. It fails the record's own test for what deserves a code (the
  modeling guide's identity, standing, relation): a world has identity and
  relation but no standing. Six documents whose status never varies is
  exactly what `inert-status` ([ADR-057](ADR-057.md)) reports, and the values would spell
  as `WORLD-002` where the author writes `B`. It also cannot express the
  default.
- **Inline values in the TOML table** (`values = ["A", "B", …]`). One
  file, no sidecar. Rejected on the split above: the values want labels
  and blurbs, and those belong beside the records where every other
  vocabulary keeps them. An inline list is the vocabulary written once in
  TOML and again wherever it is described — the drift [DP-3](../../docs/design-principles.md#dp-3) names, and the
  exact duplication [ADR-060](ADR-060.md) removed for tags.
- **Implicit wiring: any `NAME.yaml` beside the records declares a field.**
  Zero configuration, and a stray file becomes a schema change nobody
  wrote down. The two existing files are recognised by name; a third
  convention should be declared, and the TOML path `vocabularies.worlds`
  tells a reader what kind of thing `worlds` is before they open the file.
- **A general `fields` table with `vocabulary = "worlds"` as one key among
  `reference = …` and others.** The reviewer's first spelling, and the
  more general one. Deferred rather than rejected: it is the shape the
  contract's type already has, and if a fourth kind of field arrives the
  three tables can be read as one. Today a table per kind matches the
  tables a reader already knows.
- **Write the default into the source.** `luria index` fills `worlds: [B]`
  into the 38 records that omit it, and the convention disappears. This is
  [ADR-031](ADR-031.md)'s move — populate what the tree states — and it does not apply:
  a default is not a fact the tree states, it is a convention the config
  states, and rewriting 38 files to carry it is the record constraining
  the project ([DP-14](../../docs/design-principles.md#dp-14)).
- **Status quo.** Thirty-seven records carry a field nothing validates and
  thirty-eight carry a convention nothing renders.

## Consequences

What this buys: a third axis with the same guarantees as the first two —
declared once, checked by the lint, explained on the record page, browsed
by value — and a contract whose `Field` is honest about what it holds.
`statuses.yaml` and `tags.yaml` stop being special cases in the reader's
model even if they stay special in the code for a while: a closed
single-valued vocabulary and an open multi-valued one are two settings of
the same thing.

What it costs: a third file kind in a scheme directory, a fourth table
under a scheme, and a `Field` type that every consumer has to switch on
where it used to test one attribute. The index grows a directory per
vocabulary; a scheme with three vocabularies has three, beside `tags/`.

The measured need is one record. The issue's own acceptance criterion asks
that a semantic addition improve at least two unrelated domains before it
is trusted; the anthology has not reported a facet, and this repository
has none. That is the strongest argument for the draft flag: the shape is
priced from one corpus, and the verdict should say whether one is enough.

## Open questions

Where the verdict is expected to land, with the draft's answer in each
case:

1. **Pages per value: automatic, or declared?** Draft: automatic, because
   tag pages are, and declaring the vocabulary is the opt-in. The other
   reading is that a rendering choice belongs to the consumer and wants a
   `render` key on the table.
2. **Closed, or open with a `closed` flag?** Draft: closed. An open
   controlled vocabulary is `tags:`.
3. **May a default be a list?** Draft: it takes the field's shape — a list
   for `many = true`, a scalar otherwise.
4. **Does the default render on the entry?** Draft: on the record page and
   in findings only; the site's record line shows written values, not
   effective ones, so a reader is never shown a field the file does not
   have. The alternative is *Worlds: B (default)* on every page.
5. **Sidecar path: fixed `NAME.yaml`, or a `file` key like `tags = …`?**
   Draft: fixed name, with a `file` key added the day two schemes share a
   vocabulary — the same sequence `tags.yaml` went through ([ADR-060](ADR-060.md)).
