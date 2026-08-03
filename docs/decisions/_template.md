---
# Copy this file to adr-<NNN>-<kebab-slug>.md — next number wins, numbering is
# sequential and carries information (it's the order decisions were made).
#
# This frontmatter is the ONLY place these facts live. The index and the per-tag
# pages are generated from it (ADR-004) — never edit them by hand; run
# `luria index`.

# Active | Proposed | Deferred | Superseded | Rejected, optionally " — <note>".
# Supersede rather than rewrite: when a decision is replaced, set the old one to
# "Superseded — by [ADR-NNN](adr-nnn-slug.md)" and leave its body intact.
status: Proposed

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
- record

date: '2026-01-01'

# Optional. The issue(s) this decision came from: '#123'.
issue: '#000'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain.
summary: >-
  One-paragraph description of the decision, the cost that motivated it, and the
  alternatives that lost. Written to be read in a table row.
---

# ADR-NNN: Decision, stated as the thing you did

## Context

What was true that made this a question. The forces: the cost being paid, the
constraint that can't move, the thing that broke. Enough that someone who wasn't
there can reconstruct why this needed deciding — and enough that a future reader
can tell whether the context still holds.

## Decision

What was decided, in the active voice. Then the non-obvious parts: the detail
that looks like an implementation choice but is load-bearing, the invariant a
future change must not break.

## Alternatives considered

- **The obvious one** — why it lost. This section is the record's highest-value
  part: it's what stops the decision being re-litigated, and what tells a future
  reader whether their new idea is actually new.
- **The one that looks right and isn't** — worth recording precisely because it
  looks right.
- **Status quo** — always a real alternative; say what doing nothing would cost.

## Consequences

What this buys, and what it costs. Include what is now harder, the follow-up it
implies, and anything it obliges future work to keep doing. Measured numbers
beat adjectives — if it was verified, say how.
