---
status: Proposed
title: 'luria repair writes what the committed sources imply; link --fix writes what the working tree''s change implies'
version: 1
tags:
- process
- mechanism
date: '2026-10-30'
influenced_by:
- DP-002
- DP-004
summary: >-
  `luria repair` runs in CI on every pull request and on the default branch,
  and `luria link --fix` runs only where an author runs it, so a write that
  lives only in the second piles up wherever nobody runs it. Nucleation
  carried 812 one-sided converse pairs that way. The rule: a write belongs
  in `repair` when its answer is a function of the committed sources and the
  configuration alone, so any checkout of a commit computes the same edits, a
  second run computes none, and the lint can name `repair` as the remedy. It
  belongs only in `link --fix` when it needs what a checkout does not have,
  namely the author's uncommitted change against HEAD, which [ADR-084](ADR-084.md)'s
  completion reads. A judgement belongs in neither ([ADR-119](ADR-119.md)). `link --fix`
  may also run a repair, as it does the linking, but no repair waits on it.
  Applied here, [ADR-tmpwpas9](ADR-tmpwpas9.md)'s normalization of a directed pair is a repair.
  Rejected: everything mechanical into `repair` (it would run [ADR-084](ADR-084.md)'s
  HEAD-relative completion in CI, where HEAD is the tree), splitting by how
  often a write is needed, and a third command.
---
<!-- inactive-ok-file: ADR-084 — the completion rule whose HEAD baseline this decision turns on -->

# ADR-tmpu2wwj: luria repair writes what the committed sources imply; link --fix writes what the working tree's change implies

## Context

Two commands write sources, and nothing says which write goes in which.

**`luria repair`** ([ADR-068](ADR-068.md)) writes every mechanical source repair: a bare
code linked ([ADR-005](ADR-005.md)), `created:` filled from a journal entry's path,
`number:` from a filename, a status note moved into `status_note:` and
`superseded_by:`, a retired alias recorded in `formerly:`, an
already-concretized spelling upgraded. Its contract is in its docstring:
every repair is one the lint reports with `repair` as the remedy, and a
second run finds nothing to do. The generate action runs it on every pull
request and commits the result onto the branch, and runs it again on the
default branch after `luria concretize`. [ADR-119](ADR-119.md) drew its one boundary: a
write that needs a judgement, such as an acknowledgement's reason, cannot
meet that contract and stays out.

**`luria link --fix`** runs only where somebody types it. It writes the links
(the same `linkify_files` that `repair` calls), rewrites `<a name=>` anchors
that something links to, writes relations stated in prose into frontmatter
(`annotations.complete`), and completes declared converse pairs
(`relations.complete`, [ADR-084](ADR-084.md)).

The split was never stated, and its cost is measurable. Converse completion
lives only in `link --fix`. Nucleation's own guidance tells contributors not
to run repairs locally because CI does them. So the one repair
CI does not do never ran, and the record held 812 one-sided pairs. `luria
relate` had been telling users that `luria repair` writes the converse, which
was never true.

## Decision

**A write belongs in `luria repair` when its answer is a function of the
committed sources and the configuration alone.** Concretely:

- any checkout of the same commit computes the same edits, so CI on the
  pull request, CI on the default branch and an author's machine agree;
- a second run computes none ([ADR-068](ADR-068.md)'s idempotence, which the generate
  job relies on when it runs again on the commit it pushed);
- there is one right answer, so the lint can report the state and name
  `repair` as the remedy without a person choosing between readings.

**A write belongs only in `luria link --fix` when its answer needs something a
checkout does not have.** Today that means one thing: the author's
uncommitted change against HEAD. [ADR-084](ADR-084.md)'s completion decides whether a
one-sided pair is a fresh write or a stale deletion by comparing the working
tree with HEAD. In CI, HEAD is the tree. Every edge reads as "nothing
changed" and is written to both sides, so a deletion the author committed
is written back. That command cannot run where repairs run without changing
what it means.

**A judgement belongs in neither** ([ADR-119](ADR-119.md)). Its home is a command that asks
for the judgement, as `luria ack` asks for the reason.

**`link --fix` may also run repairs, but no repair waits on it.** It already
runs the linking `repair` runs, for an author who wants the result before
pushing. The reverse does not hold: nothing CI should converge on is allowed
to depend on someone having run `link --fix`.

The rule comes from the commands' existing contracts. [ADR-068](ADR-068.md) says a repair
is committed on the branch by the job, so it must mean the same thing on any
checkout. [ADR-119](ADR-119.md) says a repair has one right answer. [ADR-084](ADR-084.md) is the one
writer whose answer moves with the working tree. Whatever is not
HEAD-relative and not a judgement is a repair ([DP-004](../principles.d/DP-004.md): one implementation,
run where it converges).

### Applied

- **A directed converse pair's normalization** ([ADR-tmpwpas9](ADR-tmpwpas9.md)) is a repair. It
  reads the sources and the configuration's `derived:` marks, and nothing
  else. It moves or drops an entry filed on the derived side, and a second
  run finds nothing.
- **Converse completion for a symmetric pair or an undirected one** stays in
  `link --fix`, because it reads HEAD.
- **Two writes appear to qualify and are not moved here:** the anchor rewrite
  (`fix_anchors`) and the prose-to-frontmatter relation write
  (`annotations.complete`, which `unrecorded-relations` names `link --fix`
  for). Each reads only sources as far as this decision checked. Moving
  either is its own change, to be checked against its own edge cases first,
  rather than a side effect of this one.

## Alternatives considered

- **Everything mechanical goes in `repair`.** This is the obvious reading of
  "repair writes mechanical fixes", and it is wrong by one case. [ADR-084](ADR-084.md)'s
  completion is mechanical given a baseline, and the baseline is the author's
  working tree against HEAD. Run in CI, it writes back every deletion that
  reached a commit. The test is not "mechanical" but "the same answer on
  every checkout".
- **Split by how often a write is needed.** Rare cleanups in one command and
  everyday ones in the other. Frequency has nothing to do with whether CI can
  compute the answer, and Nucleation's pairs show that a write left to
  "whoever runs it" piles up regardless.
- **A third command for relation writes.** Another command nobody's CI runs.
  It reproduces the gap it would close.
- **Status quo: leave the boundary implicit.** This produced the 812 pending
  pairs and the false sentence in `luria relate`.

## Consequences

The question "where does this new write go?" now has a test someone can apply:
would CI on a fresh checkout compute the same edits? If yes, it goes in
`repair`, the lint names `repair`, and it converges on every pull request
without anyone remembering to run anything.

`link --fix` shrinks over time towards the HEAD-relative completion and the
local convenience of running the linking early. If [ADR-tmpwpas9](ADR-tmpwpas9.md)'s directed
pairs replace undirected ones everywhere, only symmetric relations keep it
busy.

The two candidates named above are follow-up work, recorded here so they are
not found again from scratch.
