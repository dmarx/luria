---
status: 'Active'
title: 'An undeclared family keeps the default, says so, and is never consumed'
version: 1
tags:
- mechanism
- docs
date: '2026-10-02'
issue: '#136'
summary: >-
  [ADR-047](ADR-047.md) stands: a family left out of `luria.yaml` keeps the shipped
  default. Two guards remove the harm that rule did silently. `docs/record.md`
  labels an inherited schemes, journals or fragments table as the shipped
  default and says how to declare "none". `luria collect`, which deletes
  what it reads, refuses to consume a fragment directory the config never
  declared, and names the lines to add. Rejected: making every undeclared
  family empty, and dropping only the fragments default.
influenced_by:
- ADR-047
---

# ADR-tmpky7q2: An undeclared family keeps the default, says so, and is never consumed

## Context

[ADR-047](ADR-047.md) split the merge rule: a family table (`schemes`, `fragments`,
`journals`, `remotes`, `chains`) is replaced whole once declared, and left
on the shipped default when not. [#136](https://github.com/dmarx/luria/issues/136) showed the cost of the second half.

- **`record.md` reported entries nobody wrote.** Its promise is that it is
  generated from the config and so cannot drift from it. The drift happened
  inside the config load: all seven example records listed a
  `record/changelog.d/` fragment directory that none of them declared or has
  on disk, and five listed a `devlog` journal they do not keep.
- **The destructive path was reachable from a config that never asked.**
  `luria collect` assembles a fragment directory and deletes the fragments.
  A project with a `record/changelog.d/` on disk for any other reason (a
  leftover from a migration, a half-adopted scaffold) would have it consumed
  by a collect it never configured.

`luria init` already writes every family explicitly, so new records were not
affected. Adopted records and hand-written configs were.

## Decision

**The default stays.** An undeclared family applies exactly as [ADR-047](ADR-047.md) says.

**The record page says where it came from.** `Config.inherited` names the
families `luria.yaml` left out. `record.md` adds a line under the schemes,
journals and fragments tables when the family is inherited, naming it as
Luria's shipped default and saying that `<family>: {}` declares none.

**Consuming needs a declaration.** `luria collect` refuses a fragment
directory when the fragments family is inherited and the directory holds
files. It names the directory, how many files collecting would delete, and
the `fragments:` lines to add. An empty directory stays quiet, so a
scheduled CI collect on a record with nothing to collect does not start
failing.

## Alternatives considered

- **Every undeclared family is empty when `luria.yaml` exists.** The
  config would be the whole truth, as [#136](https://github.com/dmarx/luria/issues/136) proposed. Rejected: it reverses
  [ADR-047](ADR-047.md)'s rule for every adopted record at once, and a record whose devlog
  lived in the default family would stop rendering it without a word.
- **Drop only the fragments default.** Removes the destructive path, but
  leaves the same drift for inherited schemes and journals, and makes one
  family behave unlike the others.
- **Status quo.** The page keeps documenting phantom directories, and
  collect keeps deleting files nobody declared as fragments.

## Consequences

- A record that relied on the inherited fragment directory and has
  fragments in it now has `luria collect` fail until it declares the
  family. That includes a CI job running `luria collect --commit`. The
  message gives the two lines to add.
- The example records' `record.md` pages now carry the label. Each example
  could declare the families it actually uses, which would remove the
  label; that is left to a follow-up.
- Other consumers of an inherited family (`luria new changelog`, the
  journal books, the decision index) are unchanged. Only deletion is
  guarded.
