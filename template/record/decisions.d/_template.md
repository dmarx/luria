---
# Don't copy this file by hand — run `luria new adr`, which assigns the
# identity and fills in the fields a machine can compute. WHICH identity
# depends on the scheme's `allocate` mode: `filing` (the default) takes the
# next free number on the spot, `merge` mints a temporary code that
# `luria concretize` numbers where merges serialize (FX-ADR-049). The kinds are the
# config: every scheme, fragment directory and journal in luria.toml is one, so
# `luria new <kind>` works for a scheme the moment it is declared.
#
# Numbering is sequential and carries information (it's the order decisions were
# made). The filename is the code and nothing else; the title goes in `title:`
# below, where correcting it costs an edit rather than a rename plus every link.
#   Why: LU-ADR-013.
#
# This frontmatter is the ONLY place these facts live. The index and the per-tag
# pages are generated from it — never edit them by hand; run `luria index`.
# Why: LU-ADR-004.

# Active | Proposed | Deferred | Superseded | Rejected, optionally " — <note>".
# Supersede when the CHOICE changes: set the old one to
# `Superseded — by [ADR-NNN](ADR-NNN.md)` and leave its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: Proposed

# What the index shows in place of the code. Repeat it as the body's `# ADR-NNN:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: Decision, stated as the thing you did

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
