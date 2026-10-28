---
status: Active
title: 'A record can make its blind spots lint findings: reported patterns, reliance, bounded acknowledgements'
version: 1
tags:
- mechanism
date: '2026-10-27'
summary: >-
  Three configuration-driven warning sources. A pattern declared
  `report: true` is a warning class named after the pattern, its rows the
  pattern's matches from the one clingo lowering chains and views already
  use, gated by `fail_on`, `baseline` and `mute`, and acknowledged by
  `pattern-ok:` in the match's first document. A top-level `reliance:` list
  of reference fields adds transitive dependents to the pending report and
  ranks by them; `load_bearing: N` makes a `load-bearing` class of undecided
  documents with at least N. With `reliance` set,
  `unbounded-acknowledgements` names an `inactive-ok` directive that excuses
  a retired document its own document depends on and carries no `until`.
  Rejected: a second matcher in Python, a `pattern:` prefix on class names,
  per-match acknowledgements naming codes, counting direct citations as
  reliance, and treating `Proposed` premises as retired.
influenced_by:
- ADR-035
- ADR-095
- ADR-127
- ADR-129
---

# ADR-tmpj2f7s: A record can make its blind spots lint findings: reported patterns, reliance, bounded acknowledgements

<!-- inactive-ok-file: ADR-127, ADR-129 — this builds on both while they await a decision; ADR-130 does the same -->

## Context

A downstream record ([nucleation's forcing-functions decision](https://github.com/dmarx/nucleation/blob/main/record/decisions.d/ADR-057.md#forcing-functions-making-the-backlog-visible-to-the-lint)) built a backlog of more than a
thousand undecided documents that luria never surfaced. Three blind spots,
each measured there:

- A reference checks that its target exists and is in force, and `Proposed`
  counts as in force. An Active claim resting on a Proposed one (49 edges
  there), or an Open question with an Active answer (37), was no finding.
  Which shapes are wrong is the record's own statement, so no built-in check
  could close this for every record.
- The pending report ranked by age and raw citation count. Nothing counted
  what *rests on* an undecided document, so the claims forty others depended
  on sorted beside stalled ideas.
- Claims leaning on Superseded terms carried `inactive-ok-file` directives
  ("the definition current when this claim was written"). True, and it
  silenced forever the one question that mattered: does the claim still hold
  in the successor's sense?

Patterns ([ADR-129](ADR-129.md)) already state shapes in a Cypher subset lowered to
clingo ([ADR-127](ADR-127.md)); directives already take `until <date>` ([ADR-095](ADR-095.md)); the
warning classes already have three dials ([ADR-035](ADR-035.md), [#307](https://github.com/dmarx/luria/issues/307)).

## Decision

**A reported pattern is a warning class.** `patterns.X.report: true` makes
every match a row of a class named `X`. The rows come from a fourth shown
predicate of the same lowering, `pattern_node(P, Match, I, X)` — positional,
so a match whose nodes are all anonymous is still a row — solved once for
every reported pattern. The class is in `lint.failable()` and
`lint.mutable()` for that record, so `fail_on`, `baseline` and `mute` take it
like a built-in class. A row names the first node's document; that document
acknowledges its rows with `pattern-ok: X` (any scope), and an acknowledgement
that answers for no match, or names no reported pattern, is reported under
`stale-directives`. A reported pattern named like a built-in class is refused
at load.

**Reliance is declared, and counted in clingo.** A top-level `reliance:` names
reference fields that carry dependence; each must be a reference some scheme
declares. `logic/reliance.lp` reads `held/4`, so a dependence stated on the
converse side counts, and derives each document's count of distinct
transitive dependents (a document is never its own). When set, every pending
row carries the count, the console and committed tables gain a column, and
the order is dependents descending with age as the tiebreak. Unset, the rows,
columns and order are exactly what they were. `load_bearing: N` (refused
without `reliance`, and below 1) adds the `load-bearing` class.

**An acknowledged retired premise needs a date.** With `reliance` set,
`unbounded-acknowledgements` names each `inactive-ok` directive that excuses,
in document A, a citation of a document B that A depends on directly through
a reliance field, where B is retired, and the directive has no `until`.
Retired means out of force and not undecided (`Proposed`, `Deferred`): a
`Proposed` premise is the pending report's business, ranked by
`load-bearing`.

## Alternatives considered

- **A second matcher for findings, in Python.** It would have to agree with
  the clingo lowering on converse sides, variable length and `WHERE NOT`, and
  would drift ([DP-004](../principles.d/DP-004.md)). The fourth predicate costs a few lines of lowering.
- **Class names prefixed `pattern:`.** Collision-free by construction, but
  `fail_on: [pattern:inverted_premise]` is a second spelling of a class to
  learn. The bare name, with collisions refused at load, reads like every
  other class.
- **An acknowledgement naming the other end's code.** Finer-grained, but a
  code in a `pattern-ok:` directive is read as a citation by the reference
  scan, which would need a fourth exemption. A pattern names no single site
  the way a citation does, so the first node's document answering for its
  own matches is the honest granularity.
- **Reliance as citation count.** That is the column the report already had,
  and the one that missed the backlog: a ledger citing a claim once is not a
  claim resting on it.
- **Counting `Proposed` targets as retired for the expiry check.** Every
  acknowledged citation of a draft would need a date; the draft's own
  urgency is what `load-bearing` measures.
- **Status quo.** The downstream maintains a `worklist.py` prototype beside
  luria, and every new blind spot is a luria release away from being a
  finding.

## Consequences

A blind spot found later is a pattern and a class, with no release. The
pending report changes shape only for a record that sets `reliance`.
`luria lint` reads every scheme document once more for `pattern-ok`
directives (a substring test skips the parse in files that carry none), and
solves `reliance.lp` only when `reliance` is set. A property map's `: ` is not
allowed in a plain YAML scalar, so a `match:` with a property map must be
quoted, which the configuration reference now shows.
