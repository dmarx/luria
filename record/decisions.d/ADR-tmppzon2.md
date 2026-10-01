---
status: Active
title: 'A vocabulary that needs to say more is promoted to a scheme, not enriched'
version: 1
tags:
- record
- mechanism
- load-bearing
- docs
date: '2026-10-01'
issue: '#298'
summary: >-
  A vocabulary is a shorthand for a tiny constrained scheme: named values with
  a label and a blurb. When a record needs a value to carry more — standing,
  history, relations of its own, a place in a hierarchy — that is a type
  error, and the repair is the long form. Vocabularies stay flat; a
  `promote_vocabulary` migration turns one into a scheme, one document per
  value, and every field that drew from it into a reference. A reference can
  now be grouped (`group: true`) or be a scheme's `axis`, so the views the
  vocabulary had survive as a page per target. Rejected: union vocabularies
  ([#298](https://github.com/dmarx/luria/issues/298)), and a `broader:` hierarchy inside vocabularies.
---

# ADR-tmppzon2: A vocabulary that needs to say more is promoted to a scheme, not enriched

## Context

[#298](https://github.com/dmarx/luria/issues/298) proposed building vocabularies as unions of sub-vocabularies
(`pets: union_of: [cats, dogs]`). Behind it was a larger question: whether
Luria can express a hierarchical ontology at all.

It could not, as a vocabulary. A field's `groups:` names a subset of its
values with a cardinality rule. That is one level deep, a group is not itself
a value anyone can tag with, and tagging with a member places a document
under nothing broader. A union would add composition (one field accepting a
cat or a dog). It would not add subsumption: "cat" is not a term, a Calico
note does not roll up under Cat, and nothing can say "exactly one value under
`species`".

It could, as records. A `TERM` scheme with a `broader`/`narrower` converse
pair, a chain walking `broader`, and notes citing terms through a `topic:`
reference rendered the hierarchy as a tree, refused a citation of a term that
does not exist, and gave every term standing and history — a term can be
retired with a named successor, which a vocabulary value cannot. Only two
things were missing. Nothing in the index grouped notes under the terms they
cite, as a vocabulary field's per-value pages did. And moving a vocabulary
there meant rewriting the config and every document by hand.

## Decision

**A vocabulary is a shorthand for a tiny constrained scheme, and stays
one.** Its values are named, labelled and described, and that is all.
Vocabularies get no hierarchy, no unions and no relations of their own.
A record that needs a value to carry more has outgrown the shorthand — a
type error, in the sense that the thing being stored is not the kind of
thing the field was typed as — and the repair is the long form.

**`promote_vocabulary` is the long form, as a migration operation**
([ADR-040](ADR-040.md)), so it is planned, dry-run, committed and blame-ignored like a
scheme rename:

```yaml
operations:
- op: promote_vocabulary
  vocabulary: area
  to: AREA
```

- One document per value, numbered in the vocabulary's order, then any value
  in use that an open vocabulary never declared, sorted. The value's `label`
  becomes the title, its `blurb` the summary and body, and its old spelling
  is kept as `slug:` — declared `unique`, because it was an identity.
- Every field drawing from the vocabulary becomes a reference to the new
  scheme with `group: true`. `required` is written out, because the two
  defaults differ: a reference is required unless it says otherwise, a
  vocabulary field was optional unless it said so.
- Documents now hold codes. Only that frontmatter field is rewritten. Prose
  is never swept for a value's spelling: a word in a sentence is not a
  citation of it.
- The vocabulary is removed. Its own `label` and `blurb`, if it had them,
  become the scheme's `title` and `blurb`. The new directory gets the
  `_template.md` and `README.stub` `luria init` would have written, so the
  next term is `luria new area`.

What a reference cannot carry is refused, not dropped: a `default`, value
`groups` or `primary_for`, a derivation, an `alert`. A migration that silently
loses a constraint reports success over a record that now checks less
([DP-1](../principles.d/DP-001.md)). A vocabulary behind a `status` field is refused too: standing is read
off those words, and they are not documents.

**A reference can be grouped like a vocabulary field.** `group: true` on a
reference, or naming it as the scheme's `axis`, gives each target document a
page under `<view>/<field>/<CODE>.md` listing the documents that cite it,
titled and described by the target itself and linked to it. A target nobody
cites still gets its page, as a declared value nobody uses does; a code that
resolves to nothing gets none, as a closed vocabulary's unknown value gets
none. Off by default, because most relations (`extends`, `superseded_by`)
are not taxonomies. This is what makes promotion lossless: without it, the
move a record should make would cost it its views, and the shorthand would
win by default.

A hierarchy, then, is a scheme of terms with a `broader` relation (and its
converse), cited through a grouped reference and drawn by a chain.

## Alternatives considered

- **Union vocabularies ([#298](https://github.com/dmarx/luria/issues/298)).** Composition without subsumption: the
  sub-vocabularies' names never become terms, so the hierarchy has no inner
  nodes anyone can tag with or query by. Worth having only for reusing
  independently maintained lists, which is a different need and not this
  one.
- **A `broader:` parent pointer on each vocabulary value.** The general
  hierarchy primitive, and the one closest to SKOS. Rejected because it
  rebuilds the scheme machinery — identity, relations, converses, chains —
  inside the config, second-class: an ontology change would be a config edit
  with no standing, no history and no successor, which is exactly what a
  record exists to give a claim. A term that matters enough to sit in a
  hierarchy matters enough to be a document.
- **Union plus a `specializes` relation** (`cats` specializes `pets.cat`).
  Gets most of the way, but attaches a whole list under one term, so every
  level of depth needs another named vocabulary — and it inherits the
  previous alternative's second-class standing.
- **A converse to list membership on each term.** No index change: promotion
  would declare `area` ↔ `rfcs` and `luria link --fix` would write each
  member's code into its term. Rejected because every tagged document would
  then edit its term's file, making popular terms merge-conflict hot spots —
  the opposite of [DP-2](../principles.d/DP-002.md)'s one artifact, one writer.
- **Promotion without reference grouping.** Smaller, and it makes the right
  move cost a record its per-value pages. A mechanism that punishes the
  repair teaches people not to make it.
- **A `luria promote` command.** It rewrites the config and documents
  mechanically, wants a dry run and a blame-ignore entry, and its spec is an
  audit trail worth keeping: that is a migration, and [ADR-040](ADR-040.md) already
  describes one.

## Consequences

- [#298](https://github.com/dmarx/luria/issues/298) is answered by this rather than implemented.
- Promotion is one-way. Demoting a scheme to a vocabulary would discard
  every term's standing, history and relations — the things that made it a
  scheme.
- A promoted field used as a chain's `facet_by` renders codes, not titles.
- The `luria new migration` scaffold is YAML now. It had stayed TOML after
  [ADR-098](ADR-098.md), and `luria migrate` reads specs with `yaml.safe_load`.
- A field that stops being grouped still leaves its old per-value pages
  behind with nothing reporting them. Promotion keeps the field grouped, so
  `luria index` replaces them, but the general gap remains.
- Not done here: invariants that hold at an ancestor term (a chain line of
  Tabby and Calico notes bound at Cat), and index pages that roll a term's
  narrower terms up into it. Both read the hierarchy this makes expressible;
  neither is needed to express it.
