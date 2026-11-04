---
status: Proposed
title: 'luria unconcretize records the given-back code under formerly: by default, and --noformerly turns it off'
version: 1
tags:
- mechanism
date: '2026-11-04'
summary: >-
  [ADR-140](ADR-140.md) had `luria unconcretize` record no alias, because the number goes
  back to the pool. The owner reversed that. By default the old code is now
  recorded under the document's `formerly:`, as `concretize` records a
  temporary one, so a citation the rewrite cannot reach still finds the
  document once it is numbered again. `--noformerly` records none, which is
  what a collision wants. The alias is safe even then, because a code
  resolves by number before any alias, so a live document outranks one; the
  flag is about whose history the document carries, not about resolution.
  The rewrite now also leaves other documents' `formerly:` blocks alone.
  Rejected: keeping no alias by default, a config key in place of the flag,
  and refusing the alias when the code is held.
---
<!-- inactive-ok-file: ADR-140 — the decision this one supersedes -->

# ADR-tmpwkw5f: luria unconcretize records the given-back code under formerly: by default, and --noformerly turns it off

## Context

[ADR-140](ADR-140.md) added `luria unconcretize` and recorded no `formerly:`. Its reason
was the collision case: the trunk holds the old number, so "an alias would
claim a code that another document holds, or soon will".

The owner reversed the default. `formerly:` is how the record keeps an old
address resolving when the in-tree rewrite cannot reach every citation, and
`concretize` and `luria migrate` both write it. A renumbering has those
out-of-tree citations as much as a concretization does.

Two facts about the existing machinery decide whether the default is safe:

- **A code resolves by number first.** `doc_refs.resolve` looks the number
  up in `documents()`, and the alias map is consulted only for a spelling
  with no live document. So `formerly: [ADR-068]` on another document
  never takes [ADR-068](ADR-068.md) from the document that holds it.
  `test_a_live_document_outranks_the_alias` pins this.
- **A temporary document's `formerly:` is not in the alias map.**
  `aliases.alias_map` reads numbered documents only. The alias takes effect
  once `concretize` numbers the document, and that document then carries
  both its old number and its temporary tail.

## Decision

- **By default**, `luria unconcretize` appends the old code to the
  document's `formerly:`, with `concretize`'s own `_record_alias`.
- **`--noformerly`** records none. That is the documented choice for a
  collision: the old code is the trunk's, so the branch's document should
  not remember it as its own past.
- **The rewrite skips `formerly:` blocks** (`doc_refs.FORMERLY_RE`).
  Another document whose past address was the same code keeps it.
  Rewriting it would give that document a history it never had. This
  became necessary once the alias was the default, because a renumbering
  can meet a code some other document used to hold.

## Alternatives considered

- **Keep no alias by default** ([ADR-140](ADR-140.md)). A renumbering would then break
  every out-of-tree citation of the old numbers. That is the failure
  `formerly:` exists to prevent, and the default should not cause it.
- **A `repair:`-style config key** instead of a flag. Whether to alias is a
  choice about one run of the command, which depends on whether it is a
  collision or a renumbering. It is not the record's standing setting.
- **Refuse the alias when another document holds the code.** That would
  mean checking the trunk, which [ADR-140](ADR-140.md) kept out of the command at the
  owner's direction: the user names the documents, and the command does
  not judge.

## Consequences

- After a renumbering, a citation of an old number that nothing else
  claims resolves to the document that used to hold it.
- A collision fix should pass `--noformerly`. Forgetting it does not
  misresolve, but it leaves an alias that `formerly:` readers, such as the
  site or a future check, will show as part of the branch document's past.
- Verified by `tests/test_unconcretize.py`:
  - the alias is written by default and not under `--noformerly`;
  - `concretize` keeps both old spellings;
  - a live document outranks the alias;
  - another document's `formerly:` entry is untouched.
