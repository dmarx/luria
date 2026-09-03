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
# `Superseded — by [ADR-tmphzwg9](ADR-tmphzwg9.md)` and leave its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Proposed'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmphzwg9:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'Generated views are committed on the default branch only; a pull request regenerates, checks, and commits nothing'

# Which revision of this decision's claim you are reading. Standard frontmatter
# for every scheme, and it moves rarely here: a decision that CHANGES is
# superseded by a new one, not edited. Bump it when the same choice is restated
# more broadly — scope widened, wording generalized — and say what changed in a
# `history:` entry. Shown in the index only when it is not 1.
version: 1

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
- mechanism
- process

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
  The generation job ran on pull requests too, committing regenerated
  views onto every branch — so any two concurrent branches that added a
  decision or a devlog entry diverged on the decision index, its tag pages
  and the devlog book, and the second to merge conflicted on files nobody
  wrote. Six times across one stack, resolved the same mechanical way each
  time. Generated views are now committed on the default branch only: a
  pull request regenerates in the working tree, lints the regenerated
  tree in the same job, and commits nothing. Amends [ADR-029](ADR-029.md), whose choice
  stands — a view is committed by something — while the somewhere moves.
  Rejected: a merge driver (the merge button does not run one), and a
  documented routine of regenerate-on-conflict.

---

# ADR-tmphzwg9: Generated views are committed on the default branch only; a pull request regenerates, checks, and commits nothing

## Context

[ADR-029](ADR-029.md) settled that a generated view is a committed
artifact and that a generation job is the better thing to commit it. The
job it shipped runs on every pull request as well as on push to `main`,
committing regenerated views onto the branch as the bot. That closed the
staleness gap and opened a different one.

Every branch that files a decision or a devlog entry regenerates the
decision index, the tag pages and the devlog book, and commits its own
copy. Two concurrent branches therefore carry two versions of the same
generated file, each correct for its own sources. When the first merges,
the second conflicts — on files no person wrote. Measured on the [#141](https://github.com/dmarx/luria/issues/141)
stack: six merges, each conflicting on the same three to five generated
views, each resolved the same way: take either side, run `luria index`,
commit. Never a judgement, always a chore, and one that a contributor
without the habit resolves by hand, which is how a generated file drifts
from its generator.

The sources never conflict; [ADR-002](ADR-002.md) saw to that with
fragments. The views conflict *because* they are committed where branches
live.

## Decision

**Generated views are committed on the default branch only.**

- **On push to the default branch**, the generation job runs as before —
  `luria concretize`, `luria link --fix`, `luria index` — commits the diff
  as the bot and pushes, and the lint job reads that commit through the
  `needs:` + SHA handoff. Nothing here changes.
- **On a pull request**, one job runs the generate action with
  `commit: "false"` and the lint action right after it: the views are
  regenerated in the working tree, the lint checks the regenerated tree,
  and nothing is committed. The default checkout is the merge commit, so
  the record is checked as it would land. A fork needs no write
  permission, and the fork-safe checkout gymnastics go away.

A branch never carries a regenerated view, so two branches cannot
conflict on one. The views on `main` stay committed, so
[ADR-032](ADR-032.md)'s reasons hold: the badges land on real pages and a
stale view on `main` still fails the lint.

**What [ADR-029](ADR-029.md) warned against is still wrong where it said
so.** A checking job on the default branch that regenerates and commits
nothing discards the output and compares the generator against itself.
On a pull request that is the shape by design: staleness is not a
property a branch has, because a branch does not carry the views. The
staleness remedy says which is which. [ADR-029](ADR-029.md) carries a `history:` entry;
its choice stands and the somewhere moves.

## Alternatives considered

- **A merge driver for generated files.** `.gitattributes` can name a
  driver that resolves a conflict by regenerating. The merge button on
  GitHub runs no driver, and neither does a contributor who has not
  configured one; the fix would work exactly where the problem is
  smallest.
- **Document the routine.** "A conflict in a generated file is resolved by
  regenerating, never by hand." True, cheap, and it keeps the chore. It
  is written down anyway, for the branches that predate this.
- **Stop committing views anywhere; render on demand.** Removes the class
  entirely and removes what [ADR-032](ADR-032.md) bought: the README
  badges and the status reports link to committed pages, and the
  staleness lint on `main` is what catches a generator that did not run.
- **Keep the bot on pull requests but push only source fixes** (the
  fixer's links) and not views. Halves the conflicts and keeps a bot
  pushing to branches, which races the author's own pushes
  ([ADR-002](ADR-002.md) names that hazard for the collector). Simpler to
  have the bot write to `main` only.
- **Status quo.** Six conflicts per stack, resolved by ritual.

## Consequences

A pull request's diff shows sources only, which is what review is for;
the generated diff was already collapsed. The regenerated views a reviewer
might want to see are one `luria index` away, and the site preview builds
from the same tree.

Branches that already committed regenerated views keep them until they
merge, and may still conflict with each other in the meantime; the routine
for those stays documented in CONTRIBUTING. New branches never carry them.

`luria link --fix` also runs on the pull request without committing, so a
bare code in a PR's sources passes the check there and is linked by the
bot on `main` after merge. A reviewer reads bare codes in a source diff;
the rendered record does not.

The scaffold's workflow changes shape with this repository's, as
[ADR-029](ADR-029.md) requires: adopters get the same three jobs.
