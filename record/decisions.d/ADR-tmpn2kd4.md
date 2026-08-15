---
status: Active
title: Prose frontmatter is what the generator renders, not what the author prefers
version: 1
tags:
- record
date: '2026-08-15'
summary: >-
  `summary:` was the single frontmatter key treated as prose — scanned for bare
  references, linked by the fixer, checked by the lint — while everything else
  was data read by value. `origin:` broke that split: it is rendered as
  markdown into a principle's metadata line, so a reference written there
  *should* be followable, but the machinery silently left it as literal text,
  which is the worst of both (it renders as a link if hand-written, and rots
  unchecked forever). Decision: a `PROSE_KEYS` set, currently `summary` and
  `origin`, and the membership rule is stated — a key is prose exactly when
  the generator renders its value as markdown somewhere. Rejected: making the
  set configurable, because a project cannot make a field prose by declaring
  it so; the rendering is what makes it true, and a config knob would let a
  project ask for links in a field that will display them as raw text.
---

# ADR-tmpn2kd4: Prose frontmatter is what the generator renders, not what the author prefers

## Context

[ADR-005](ADR-005.md) drew a line: frontmatter is *data* — read by value,
never rendered — with one exception, `summary:`, which the generator renders as
markdown into the index and the tag pages. So the summary may carry links, and
the reference machinery scans it; everything else stays plain, because a link
in a data field is just noise inside a value.

`origin:` did not fit that split. It is rendered — into a principle's metadata
line, beside the version and the `shaped by` backlinks — but it was not scanned.
A reference written there was in the worst of both worlds: a hand-written link
*displays* correctly, so an author is encouraged to write one, while the fixer
never maintains it and the lint never checks it. A rot with no alarm.

Downstream, this produced advice rather than a fix. strata-g moved every
principle's origin into frontmatter and then documented "keep it plain prose,
because only `summary:` is scanned" — a workaround written into a template, for
a limitation we own.

## Decision

**A key is prose exactly when the generator renders its value as markdown.**
`PROSE_KEYS = ("summary", "origin")`, and the reference machinery — the mask,
the skip list, the rewritability guard and the frontmatter-survival check —
reads that set rather than naming `summary` four times.

## Alternatives considered

- **Leave it, and tell authors to keep `origin:` plain.** What was happening.
  It asks every downstream project to remember a limitation instead of fixing
  it once, and the limitation is invisible until someone writes a reference and
  watches it never get linked.
- **Make the set configurable.** Tempting, and wrong in a way worth recording:
  a project cannot make a field prose by declaring it so. The rendering is what
  makes it true. A knob would let a project ask for links in a field that
  displays them as raw text — a promise the config cannot keep.
- **Scan all of frontmatter.** Puts links in `status:`, `tags:` and `issue:`,
  which are parsed by value; the survival check exists precisely because a
  rewrite can break YAML.

## Consequences

- Adding a prose key is a one-line change here, but the rule says when it is
  allowed: render it first, then add it.
- The frontmatter-survival check now compares every prose key rather than the
  summary alone, so a rewrite that damages an `origin:` block is declined the
  same way.
- Downstream guidance can drop the workaround: a reference in `origin:` is
  written bare and the fixer links it, like prose anywhere else.
