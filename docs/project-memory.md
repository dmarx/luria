# Project memory: how a repo thinks

Half the collaborators on a modern codebase are stateless. They arrive with no
memory, read some pages, work, and vanish. Unwritten knowledge is therefore
re-derived at cost, per session, forever — the **rediscovery tax**.

Luria's answer is that **the project is its own memory**: the written record
isn't a description of the collaboration, it *is* the next collaborator's mind,
reconstituted from disk every session. That makes documentation quality
compound, and it makes this page the boot sector. An agent file should point
here; a session that reads only this page should file knowledge in the right
place on its first try.

---

## 1. The four layers

| layer | holds | one-line test |
|---|---|---|
| [`design-principles.md`](design-principles.md) | standing **values**, numbered, cited as "DP-2" instead of re-argued | *have we re-derived this reasoning more than once?* |
| [`decisions/`](decisions/README.md) | a **choice among alternatives** at a point in time, one file each | *did we reject an alternative, or set a constraint a future edit could violate?* |
| `changelog.d/` fragments | **what changed**, operator-facing, terse | *would someone running or using this notice?* |
| `devlog.d/` fragments | **how it went** — including failed approaches and wrong theories, which are the reusable part | *will a future debugger want the narrative?* |

The traffic rules between them are [ADR-001](decisions/adr-001-four-layers-of-record.md):
principles are durable but **not sacred**; decisions are superseded by *adding*
a decision and flipping a status line, never by rewriting a body; a principle is
added on the *second* re-derivation of the same reasoning.

**File in the same contribution as the work.** "Later" is a euphemism for never,
and a fact filed while its context is loaded costs a paragraph — re-derived
cold, it costs a session ([DP-8](design-principles.md)).

---

## 2. Fragments and generated views

`CHANGELOG.md`, the decision index and similar assembled pages are **views**,
generated from fragments — never hand-edited, and the lint refuses hand edits.

The reasoning is [DP-2](design-principles.md): a file every contribution must
append to is a *lock*. Concurrent branches collide in it contentlessly, and
every hand-merge is a chance to drop someone's work. The fix is structural —
each contribution owns a file nobody else writes, and the shared artifact is
assembled on a cadence ([ADR-002](decisions/adr-002-fragments-and-generated-views.md)).

Practical consequences: the answer to "which file do I edit?" is always *a
fragment*; and generated pages can be linted against their sources, so drift is
caught instead of discovered.

---

## 3. The drift doctrine

The most-earned lesson, [DP-3](design-principles.md): **a hand-maintained
projection of a source of truth will drift** — not as a risk but as a rate. The
remedy ladder:

1. **Derive the projection.** Indices are generated from frontmatter. Drift
   becomes impossible.
2. **Guard the property, not the list.** Where a projection must stay code, a
   test asserts the *invariant*, not the contents. A test that asserts "the list
   contains these names" is the drifting list in a costume.
3. **Choose the failure polarity** of any hand list that remains, and say so in
   a comment: *fail-safe* or *fail-loud*. *Fail-stale* — the miss ships as
   silently wrong behavior — is never acceptable, and it is the naive default.

The enforcement clause is [DP-6](design-principles.md): **fire before
trusting.** Every guard gets one deliberate sabotage run to prove it catches.
Provisioned is not working.

---

## 4. The collaboration model, in the open

**Culture must be compiled** ([DP-5](design-principles.md)). A stateless
collaborator can't be socialized, so a norm that exists only as prose is
followed probabilistically. Norms that matter get walked up the ladder *prose →
convention → mechanism → guarantee*. When you find yourself repeating a
correction, that is the signal to walk the norm up a rung.

**No private brains** ([DP-7](design-principles.md)). Agent files are legitimate
as **bootloaders** — pointers to the shared record, plus harness mechanics no
human needs — never as knowledge stores. The decision test: *would a new human
hire need this?* Then it belongs in the shared docs, and the agent file links to
it. This page is what the bootloader points at.

---

## 5. Leaving knowledge behind: the checklist

- [ ] `changelog.d/` fragment for anything an operator or user would notice.
- [ ] `devlog.d/` fragment if the work *taught* something — and record wrong
      theories with why they were wrong; the dead ends are what the next
      debugger needs most.
- [ ] A decision if you rejected an alternative, chose a constraint, or made
      something a future edit could silently violate. Cite principles by number.
- [ ] A design-principle edit only on the *second* re-derivation of the same
      reasoning.
- [ ] In code, cite the record inline (`# ADR-004`, `# DP-3`): comments that
      name their justification survive refactors that arguments don't.
- [ ] If you built a guard or gate: note the sabotage run that fired it
      ([DP-6](design-principles.md)).

## What keeps this true

- `luria lint` in CI: generated views match their sources, frontmatter conforms,
  references are followable.
- Deterministic assembly — same inputs, same view, so drift between record and
  view is mechanically checkable.
- The reports ([ADR-007](decisions/adr-007-status-is-reported-not-enforced.md)):
  what cites a retired decision, and what has been undecided for how long.
