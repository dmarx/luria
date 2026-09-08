---
status: Proposed
title: 'A derived alias is kept; a former spelling is rewritten'
version: 1
tags:
- record
date: '2026-09-08'
issue: '#219'
summary: >-
  A scheme can render a second spelling from each document's frontmatter, and
  `luria link --fix` leaves it written — the opposite of what it does with a
  `formerly:` entry, which it rewrites away. Two kinds in one map, each
  carrying its kind, because the fixer's instruction differs and shape cannot
  tell them apart.
---

# ADR-tmp1643l: A derived alias is kept; a former spelling is rewritten

## Context

Adopting sequential codes costs a record the identifier a reader could
interpret. The consuming anthology's pre-migration ids were
`MLR-2014-Kingma001-0001` — prefix, year, first author, disambiguator — and
became `SOTA-001`.

[ADR-040](ADR-040.md) already had the resolution machinery for a second spelling: a
document names its past in `formerly:`, references written that way resolve,
and the fixer upgrades them. But that machinery exists to *retire* a
spelling, and what a readable identifier needs is the opposite.

## Decision

A scheme may declare a template rendered from each document's own
frontmatter:

    alias = "LIT-{first_author}-{published:.4}-{number}"

Both kinds live in one map and each entry carries its kind, because the
fixer's instruction differs and nothing in the shape of a spelling
distinguishes them:

- **Formerly** — a past spelling. `luria link --fix` rewrites it to the code.
- **Also known as** — rendered now. The fixer leaves it written, because
  canonicalizing it would erase the readable identifier on the first `--fix`,
  silently, which is the outcome this exists to prevent.

Three constraints fall out and are enforced:

- **The template must start with the scheme's prefix.** Every reference
  scanner finds a code by its prefix first, so a spelling without one is
  unreachable however well it resolves. Refused where the config is read.
- **Resolution decides what is a reference, never the pattern.** An alias
  tail is loose by necessity, so a widened pattern would match prose; a
  spelling absent from the map was never a reference. The rule `legacy_spellings`
  already states, applied to a case that makes it load-bearing.
- **A collision is a violation.** One spelling answering for two documents
  makes every citation through it ambiguous. Including `{number}` makes that
  impossible by construction.

## Alternatives considered

- **Auto-suffix a collision.** Rejected: an automatic `-002` is
  order-dependent and would silently renumber when a third document arrives.
  The template is the fix, and `{number}` is the version of it that cannot
  fail.
- **Canonicalize aliases in the fixer, like every other spelling.** The
  consistent choice, and it defeats the feature: the readable identifier
  would survive exactly until someone ran `luria link --fix`.
<!-- inactive-ok: ADR-087 — Proposed as step 1 of this same plan; the rule it states is what this decision rests on -->
- **Derive the code itself rather than an alias.** Rejected in [ADR-087](ADR-087.md):
  a value may participate in identity only if it is recomputed, and may only
  be recomputed if it is not identity.
- **A filter vocabulary for the template** (slugify, truncate). Deferred, and
  by measurement rather than taste: `str.format`'s own spec language already
  truncates a string, so `{published:.4}` yields the year and the motivating
  case needs no filters at all.

## Consequences

Resolution moved from an on-demand scan to the cached map. `alias_number`
used to read every document's frontmatter per lookup, and its docstring gave
the sound reason — the path only ran for temporary codes, which are rare. A
spelling people *choose* to cite is not rare, so that assumption expired the
moment this landed. The cache is now load-bearing for correctness too, since
resolution is what gates the loose pattern.

An alias is recomputed and therefore always true — until someone writes one
down. Correcting an author moves the spelling, so a superseded one has to
land in `formerly:` to keep resolving; that hand-off is what makes an alias
safe to cite durably, and it is the one part of this that still needs a
`luria repair` pass.

Fired on the real record: 218 literature notes rendered
`LIT-{first_author}-{published:.4}-{number}` with no collisions —
`LIT-Dao-2022-074` for FlashAttention, which is the pre-migration shape
recovered.
