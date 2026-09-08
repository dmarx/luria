---
status: Proposed
title: 'Identity is a field; the filename is a projection of it'
version: 1
tags:
- record
date: '2026-09-08'
issue: '#219'
summary: >-
  A scheme document carries `uid:`, and its filename is derived from it —
  the model journals have always used for `created:`, applied to schemes.
  Identity in the filesystem was the obstacle to expressive filenames and
  aliases, because anything the name encoded became load-bearing. A counter
  rather than a UUID: the sequence carries the order documents were filed,
  and merge-safety is already solved by temporary codes.
---

# ADR-tmp9ljfi: Identity is a field; the filename is a projection of it

## Context

Journals and schemes disagreed about where identity lives, and neither said
why. A journal entry's path derives from its `created:` frontmatter, and
`luria lint` checks the two agree — stated in `check_journals` as: *"the
ordering the whole scheme rests on says one thing and the frontmatter says
another."* A scheme document had no such field. Its number was parsed out of
the filename, so the name on disk *was* the identity.

That is what blocked expressive filenames and derived aliases. Any
information a filename carries becomes load-bearing the moment the filename
is the identity, so a slug cannot be added without making the slug part of
what a citation resolves through. The consuming record had paid this: its
pre-migration identifiers (`MLR-2014-Kingma001-0001`, plus a `topic_id`
slug) were readable without a lookup, and became `SOTA-001` and nothing.

## Decision

A scheme document carries `uid:`, an integer, and the filename is a
projection of it.

- `Scheme.uid_of()` reads the field, falling back to the filename.
- `luria lint` reports a document whose field and filename disagree.
- `luria repair` writes the field from the path where it is absent.
- `luria new` writes it for a scheme that allocates on filing; `luria
  concretize` writes it for a merge-allocated one, at the moment it assigns
  a number at all ([ADR-049](ADR-049.md)).

The fallback is what makes this introducible without a migration anyone has
to run: a record written before the field existed reads exactly as it did,
and acquires the field the next time `luria repair` runs.

**A counter, not a UUID.** The number carries the order documents were filed
— the scaffold says so in as many words — and a UUID would discard that to
buy merge-safety that temporary codes already provide.

## Alternatives considered

- **Leave identity in the filename.** The status quo, and the thing that
  makes every downstream ask impossible: a filename that carries meaning and
  also carries identity cannot have the meaning corrected.
- **A UUID or URI per document.** Genuinely more robust against collision,
  and it discards ordering to solve a problem [ADR-049](ADR-049.md) closed. Rejected for
  paying information to buy nothing new.
- **Derive the code from frontmatter at allocation** — evaluate a template
  once in `luria concretize` and freeze the result. Technically safe:
  identity never moves afterwards. Rejected because a seeded code *looks*
  derived and is not, so correcting an author leaves a code reading the old
  name forever, correctly-by-design, and every future reader has to be told.
  A number makes no claim that can rot. The rule this settles: a derived
  value may participate in identity only if it is recomputed, and it may only
  be recomputed if it is not identity.
- **Rename the file automatically when the two disagree.** Rejected: which of
  the two is right is a question only the author can answer, and renaming on
  a guess moves a document's identity and orphans the links to it. An
  *absent* field is the mechanical case, and that one is repaired.

## Consequences

`Scheme.documents()` goes from a directory glob to a glob plus a frontmatter
read. Cached on the file's `(mtime, size)` rather than reset by hand, so a
writer that forgets to invalidate cannot serve a stale identity. That it is
one function to change at all is owed to [DP-4](../../docs/design-principles.md#dp-4): five copies of that glob had
accumulated and were consolidated for unrelated reasons.

A disagreement between field and filename is now a way to break reference
resolution that did not previously exist — `documents()` reads the field
while a link target is written from the code — which is why the check is a
violation rather than a report.

Verified on both records before landing: 436 documents in the consuming
anthology and 103 here acquired the field, `luria lint` held its exact
baseline in both, and **every generated view was byte-identical** except the
reference report, whose line numbers shift by one because the field adds one
line. The guard was fired on a real document too, not only a fixture.
