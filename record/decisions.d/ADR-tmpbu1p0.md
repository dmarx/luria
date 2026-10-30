---
status: Active
title: 'luria repair removes an inactive-ok code whose document is in force'
version: 1
tags:
- record
- ci
date: '2026-10-30'
summary: >-
  When a document an `inactive-ok` names goes Active, `luria repair` removes
  that code from the directive. It keeps the reason and the other codes, and
  deletes the directive only when it names nothing else. The lint reports such
  a code even when the directive's other codes still excuse something, so the
  report and the repair agree on what counts. Rejected: repairing only the
  directives the lint already called stale, which leaves the dead codes
  Nucleation's hand trim removed; also removing a retired code that nothing
  cites any more, which may want moving rather than deleting; and leaving it
  to people, which cost Nucleation a throwaway script for one promotion pass.
---

# ADR-tmpbu1p0: luria repair removes an inactive-ok code whose document is in force

## Context

An `inactive-ok:` claims that a code it names is retired. When the document
goes Active the claim is false, and the acknowledgement logic cannot let the
code excuse anything: a citation of a document in force wants no excuse. ADR-119
already treats this state as wrong on arrival, since `luria ack` refuses to
write a directive over a document in force.

The lint reported it only per directive. A directive went into
`stale-directives` when it excused nothing at all. A directive with one Active
code among several retired ones that are still cited stayed silent, and the
dead code stayed in it.

Nucleation promoted 53 readings in one status pass. It cleared the fallout with
a throwaway script: it removed each newly Active code from its directive and
deleted any line left naming nothing. That came to 47 lines in 46 files. In
25 of those lines the directive still excused other codes, so the lint had not
reported them.

ADR-119 rejected putting `luria ack` in `luria repair`, because writing an
acknowledgement needs a reason only a person can give. Removing a code is the
converse. It has one correct answer and needs no sentence.

## Decision

**`luria repair` removes, from every `inactive-ok`, the codes whose documents
are in force** (`ack.trim_settled`). It keeps the reason, the remaining codes,
their separator and any `until` expiry. It deletes the directive only when no
code is left, and then deletes the line too if the comment was alone on it.
Markdown comments, YAML comments in frontmatter and `#` comments in code are
all handled.

**One reading decides which codes are settled**: `ref_status.settled_codes`. A
code is settled when it names a local document whose status is the scheme's
`active` value, the same test the lint already used to say "is Active now".
Both the lint row and the repair read this function (DP-004).

**The lint names a settled code even when the directive is still used.** That
case is a new `stale-directives` row, "no longer applies to X — Active now",
and its remedy is `luria repair`. Without this row the repair would write a
fix the report never asked for, and the two would disagree about what counts.

What it never touches:

- a malformed `inactive-ok`, since its problem is the finding;
- a retired code that nothing in scope cites any more;
- `unresolved-ok`, `mention-ok`, `target-ok` and `url-ok`;
- files the reference scan does not read, such as historical journals.

## Alternatives considered

- **Repair only the directives the lint already called stale.** This is the
  smallest change, and it would have missed over half of Nucleation's case.
  Of the 47 lines the hand trim changed, the lint had reported 21. Another 25
  were in directives whose other codes still excused something. Each of those
  was "used", so it was not reported, yet each carried a code vouching for a
  retirement that was over. The last one was in a file the scan does not
  read.
- **Also remove a retired code that nothing in scope cites.** The lint calls
  this directive stale too, but the cause is ambiguous. The citation may have
  moved a line, and then the directive should move with it. Deleting it would
  be a guess.
- **A separate command, such as `luria ack --prune`.** This keeps writing and
  removing directives side by side. But a fix with one correct answer is what
  `luria repair` exists to run, and CI already runs it on every pull request.
  A separate command is one more step for each contributor to remember.
- **Leave it to people.** The cost is measured: a throwaway script for one
  promotion pass in Nucleation, and about 1,400 more such directives that
  nobody had trimmed.

## Consequences

On Nucleation at `0d244a39d`, just before the hand trim, the lint reported
1476 stale-directive rows from the reference scan. The repair changed 1476
directive lines in 1336 files, rewriting 1001 and deleting 475. Afterwards 24
rows remain, all of them "nothing in scope cites", which need a person. A
second run changes nothing. Every code the repair removed names an Active
document. The repair made every removal the hand trim made in scanned files.
The one it skipped was in a workbench journal entry, which the scan treats as
historical.

A project that upgrades will see one large repair commit the first time CI runs
it. After that, each promotion clears its own directives on the branch that
promotes.
