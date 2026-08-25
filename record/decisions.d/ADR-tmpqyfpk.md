---
status: Active
title: A suppressed build is branch protection's problem, not the lint's
version: 1
tags:
- mechanism
- process
date: '2026-08-25'
summary: >-
  A commit message describing the CI skip marker contains it, and so stops
  its own build. A checker was written for this and measured backwards: it
  cannot fire in the case that does harm, and does fire on commits that
  caused none. Required status checks answer the question that matters —
  does the commit being merged have a green check of its own — and no
  mechanism here can. Rejected: shipping the checker, and a commit-msg hook.
---

# ADR-tmpqyfpk: A suppressed build is branch protection's problem, not the lint's

## Context

GitHub skips a workflow run when the head commit's message carries a skip
marker. This package depends on that: the generate action marks its own
commits so a bot push opens no run.

The convention has no escape sequence. A message *describing* the marker
contains the marker, so writing about it suppresses the build for the commit
that writes about it. It happened twice in one session:

- A downstream project adopting the recommended workflow explained the
  convention in the commit that adopted it. Every workflow on that commit was
  skipped. The author had read the caution in the scaffolded `docs.yml` header
  first.
- This repository's own generate action pushed a marked commit that became a
  branch tip. No run fired on the tip, and the pull request went on showing
  the previous commit's checks.

What makes it expensive is the shape of the failure. A suppressed run is not
a red build; it is **no** build, and the most recent checks that exist still
belong to the previous commit. Silence is indistinguishable from success
unless someone asks which commit the green belongs to, and nobody asks that
on a pull request that looks passing.

A checker was written for it: report commits carrying a marker in the message
*body*, on the theory that a deliberate skip goes in the subject or a trailer
and prose lands in the middle. Wired into the lint action as a warning.

Measured against the two incidents and a direct test, it is backwards.

**It cannot fire in the case that does harm.** When the marker is on a commit
that is the tip and stays the tip, no workflow runs — so nothing exists to run
the check inside. Both incidents above were that shape. The checker would have
been silent for both.

**It fires when nothing is wrong.** A probe pushed two commits together: the
first mentioning the marker in its body, the second clean and at the head. The
runs fired normally. GitHub reads the head commit only, so a marker anywhere
else is inert — and the checker would have reported that commit anyway. Its
own message had to hedge (*"if this commit was ever the tip of a push"*),
which is a warning admitting it does not know.

Silent on harm, noisy on non-harm. This module already carries the note about
why the second half alone is disqualifying: a warning that is usually noise
trains readers to skip warnings.

## Decision

Do not ship it. **Require status checks in branch protection instead.**

A required check asks the only question that matters — does the commit about
to be merged have a passing check *of its own* — and it is indifferent to why
one is missing. A skip marker, a bot push, a workflow that never queued, a
runner outage: all the same answer. Nothing this package can ship reaches that
question, because every mechanism here runs *inside* a workflow, and the
failure is the workflow not running.

The half of the work that was worth keeping already landed: `adopting.md`
documents the hazard with the detail that makes it findable — the failure
presents as no build rather than a red one — and says to name the marker in
prose rather than writing it.

## Alternatives considered

- **Ship the checker as a warning.** What this decision rejects, on the
  measurements above. It is not that the check is imprecise; it is aimed at
  the wrong event. Detection that runs inside the thing that did not run
  cannot report that it did not run.
- **A `commit-msg` hook that refuses a marker in a body.** Prevention rather
  than detection, and it does reach the moment that matters. Rejected for now
  on two counts: it is bypassable by exactly the automation most likely to
  trip the hazard, and scaffolding git hooks into somebody's repository is
  intrusive in a way writing files is not. Worth revisiting if `luria init`
  ever grows a hooks story for other reasons.
- **Have `docs-lint` assert that the SHA it checked out is the pull request
  head.** Narrower and genuinely inside our reach: it catches a tip left
  unchecked because generation moved it, without guessing at anybody's
  intent. It does not catch the suppressed-tip case either, for the same
  structural reason. Not rejected so much as unbuilt — it addresses the
  adjacent hazard (two committers, [LU-ADR-029](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-029.md)'s handoff defeated from
  outside), and belongs with that if it is built.
- **Stop using the marker in the generate action.** Removes the hazard by
  removing the convention, and reintroduces the loop it exists to break: the
  bot's push opens a run, whose generate step pushes again.

## Consequences

The hazard remains, mitigated by documentation rather than by machinery,
which is a posture this record is usually suspicious of — a convention that
matters gets walked up to a mechanism ([DP-5](../../docs/design-principles.md#dp-5)). The exception is stated
plainly: the mechanism that would catch it is not ours to ship. It is a
repository setting, and adopting projects have to turn it on themselves.

`luria init` cannot set branch protection either, so the scaffold can only
recommend it. That is a real gap between what the record says and what the
tooling can guarantee, and naming it here is the point of writing this down
rather than closing a pull request quietly.
