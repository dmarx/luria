---
status: Active
tags:
- record
date: '2026-08-03'
summary: >-
  Four layers, each with a one-line test for what belongs in it: design
  principles hold standing values, decisions hold a choice among alternatives at
  a point in time, changelog fragments hold what an operator would notice,
  devlog fragments hold how it went — including the wrong theories, which are
  the reusable part. Separate files rather than one document because they have
  different lifecycles: a principle is revised, a decision is superseded but
  never rewritten, a fragment is collected and deleted. Rejected: one CHANGELOG
  holding all four (the layers' different write patterns collide, and the one
  that gets skipped is always the narrative), and inferring the narrative from
  git history (commit messages are written to a different audience, and the
  failed approaches — the expensive part — never appear in them).
---

# ADR-001: Four layers of record, each with a test for what belongs in it

## Context

Half the collaborators on a modern codebase are stateless: they arrive with no
memory, read some pages, work, and vanish. Unwritten knowledge is therefore
re-derived at cost, per session, forever — the **rediscovery tax**. The answer
this package encodes is that the project *is* its own memory: the written record
isn't a description of the collaboration, it's the next collaborator's mind,
reconstituted from disk.

That only works if "where does this go?" has a fast answer. A single `NOTES.md`
fails not because it can't hold the content but because nobody can tell what
belongs in it, so the entries that cost the most to re-derive — the failed
approaches — are the ones that never get written.

## Decision

**Four layers, each with a one-line test.**

| layer | holds | test |
|---|---|---|
| `design-principles.md` | standing **values**, numbered, cited as "DP-2" instead of re-argued | *have we re-derived this reasoning more than once?* |
| `decisions/` | a **choice among alternatives** at a point in time, one file each | *did we reject an alternative, or set a constraint a future edit could violate?* |
| `changelog.d/` | **what changed**, operator-facing, terse | *would someone running or using this notice?* |
| `devlog.d/` | **how it went**, including wrong theories | *will a future debugger want the narrative?* |

The traffic rules between them matter as much as the split:

- Principles are durable but **not sacred** — revised when we learn better, with
  the reasoning captured where the change lands.
- Decisions are superseded by **adding** a decision and flipping a status line,
  never by rewriting a body. A record you can rewrite can't be trusted about
  what you used to think. A decision with an empty "alternatives considered"
  usually wasn't a decision.
- A principle is added on the *second* re-derivation. One instance is a
  decision; a pattern is a principle.
- Fragments are one-file-per-contribution so parallel work never collides
  ([ADR-002](adr-002-fragments-and-generated-views.md)).

## Alternatives considered

- **One document for everything.** Simplest to explain, and it fails at the
  point of use: with no test for what belongs, the cheap entries get written and
  the expensive ones don't.
- **Infer the narrative from git history.** Free, and it captures the wrong
  thing — commit messages address a reviewer looking at a diff, not a debugger
  six months later, and the approach you abandoned on Tuesday leaves no commit
  at all.
- **Decisions only** (the plain ADR practice). The common baseline, and it has
  no home for a value that many decisions cite — so the value gets re-argued in
  each one, which is the cost [DP-2](../design-principles.md) names in a
  different domain.

## Consequences

- Four directories and one file, plus the collection cadence in
  [ADR-002](adr-002-fragments-and-generated-views.md).
- The tests are checkable by a stateless reader, which is the audience.
- "Which file do I edit?" has one answer for three of the four layers: *a
  fragment*. That is deliberate — see
  [ADR-002](adr-002-fragments-and-generated-views.md).
