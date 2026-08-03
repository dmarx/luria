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
| [`principles/`](design-principles.md) | standing **values**, numbered, cited as "DP-2" instead of re-argued | *have we re-derived this reasoning more than once?* |
| [`decisions/`](decisions/README.md) | a **choice among alternatives** at a point in time, one file each | *did we reject an alternative, or set a constraint a future edit could violate?* |
| `changelog.d/` fragments | **what changed**, operator-facing, terse | *would someone running or using this notice?* |
| `devlog.d/` fragments | **how it went** — including failed approaches and wrong theories, which are the reusable part | *will a future debugger want the narrative?* |

The traffic rules between them are [ADR-001](decisions/ADR-001.md):
principles are durable but **not sacred**; decisions are superseded by *adding*
a decision and flipping a status line, never by rewriting a body; a principle is
added on the *second* re-derivation of the same reasoning.

The top two layers are one file each, in `docs/principles/` and
`docs/decisions/`, with YAML frontmatter — `docs/design-principles.md` and the
decision index are both **generated** from them
([ADR-012](decisions/ADR-012.md)). A principle's
frontmatter carries a `version`, because principles are living documents: a
value first stated about one artifact is a value nobody applies to the next one,
so the honest move is to widen the wording and bump the version rather than
write a second principle. It also carries `influenced_by`, naming the decisions
whose experience produced it — the inverse of the usual direction, and the
evidence that stops a principle reading as taste.

**File in the same contribution as the work.** "Later" is a euphemism for never,
and a fact filed while its context is loaded costs a paragraph — re-derived
cold, it costs a session ([DP-8](design-principles.md#dp-8)).

---

## 2. Fragments and generated views

`CHANGELOG.md`, the decision index, the principles document and similar
assembled pages are **views**, built from fragments — never hand-edited, and the
lint refuses hand edits.

Two kinds, and the difference is *whether the sources survive*
([ADR-012](decisions/ADR-012.md)). A **collected**
view — the changelog, the devlog — consumes its fragments: they are deleted, the
view accumulates, and it can only ever be appended to. A **generated** view —
the decision index, the principles document — is a pure function of sources that
persist, rebuilt from scratch every time, which is the only reason a stale one
can be *detected*. Prefer generation where the data is derivable; there is then
no collection step to forget.

The reasoning is [DP-2](design-principles.md#dp-2): a file every contribution must
append to is a *lock*. Concurrent branches collide in it contentlessly, and
every hand-merge is a chance to drop someone's work. The fix is structural —
each contribution owns a file nobody else writes, and the shared artifact is
assembled on a cadence ([ADR-002](decisions/ADR-002.md)).

Practical consequences: the answer to "which file do I edit?" is always *a
fragment*; and generated pages can be linted against their sources, so drift is
caught instead of discovered.

---

## 3. The drift doctrine

The most-earned lesson, [DP-3](design-principles.md#dp-3): **a hand-maintained
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

The enforcement clause is [DP-6](design-principles.md#dp-6): **fire before
trusting.** Every guard gets one deliberate sabotage run to prove it catches.
Provisioned is not working.

---

## 4. The collaboration model, in the open

**Culture must be compiled** ([DP-5](design-principles.md#dp-5)). A stateless
collaborator can't be socialized, so a norm that exists only as prose is
followed probabilistically. Norms that matter get walked up the ladder *prose →
convention → mechanism → guarantee*. When you find yourself repeating a
correction, that is the signal to walk the norm up a rung.

**No private brains** ([DP-7](design-principles.md#dp-7)). Agent files are legitimate
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
- [ ] A principle only on the *second* re-derivation of the same reasoning —
      and when an existing one nearly covers it, **widen that one and bump its
      `version`** rather than adding a neighbour it will be confused with.
- [ ] In code, cite the record inline (`# ADR-004`, `# DP-3`): comments that
      name their justification survive refactors that arguments don't.
- [ ] If you built a guard or gate: note the sabotage run that fired it
      ([DP-6](design-principles.md#dp-6)).

## What keeps this true

- `luria lint` in CI: generated views match their sources, frontmatter conforms,
  references are followable.
- Deterministic assembly — same inputs, same view, so drift between record and
  view is mechanically checkable.
- The reports ([ADR-007](decisions/ADR-007.md)):
  what cites a retired decision, and what has been undecided for how long.
