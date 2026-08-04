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
| [`principles/`](../meta/design-principles.md) | standing **values**, numbered, cited as "DP-2" instead of re-argued | *have we re-derived this reasoning more than once?* |
| [`decisions/`](../meta/decisions/README.md) | a **choice among alternatives** at a point in time, one file each | *did we reject an alternative, or set a constraint a future edit could violate?* |
| `changelog.d/` fragments | **what changed**, operator-facing, terse | *would someone running or using this notice?* |
| `devlog.d/` entries | **how it went** — including failed approaches and wrong theories, which are the reusable part | *will a future debugger want the narrative?* |

The traffic rules between them are [ADR-001](../meta/decisions/ADR-001.md): principles
are durable but **not sacred**; a decision whose *choice* changes is superseded
by adding a decision rather than by rewriting its body; a principle is added on
the *second* re-derivation of the same reasoning.

The top two layers are one file each, in `docs/principles/` and
`docs/decisions/`, with YAML frontmatter — `docs/design-principles.md` and the
decision index are both **generated** from them
([ADR-012](../meta/decisions/ADR-012.md)). A principle's
frontmatter carries a `version`, because principles are living documents: a
value first stated about one artifact is a value nobody applies to the next one,
so the honest move is to widen the wording and bump the version rather than
write a second principle. It also carries `influenced_by`, naming the decisions
whose experience produced it — the inverse of the usual direction, and the
evidence that stops a principle reading as taste.

**File in the same contribution as the work.** "Later" is a euphemism for never,
and a fact filed while its context is loaded costs a paragraph — re-derived
cold, it costs a session ([DP-8](../meta/design-principles.md#dp-8)).

---

## 2. Nothing here is immutable — only un-silently revisable

The rule that gets over-read is "never rewrite a decision's body". Read as
*documents are frozen*, it makes the record brittle: a wrong sentence stays
wrong because fixing it looks like tampering, and a decision gets retired over a
bad paragraph.

What the rule is actually protecting is narrower and more useful. **The
objection is to *silent* revision** — to a record that can quietly change what
it says it used to think. A change that announces itself is not that. So every
layer is revisable, and each has a shape for saying so:

| what happened | remedy | how a reader sees it |
|---|---|---|
| the **choice** changed | supersede: add a decision, retire the old one | two documents, and when the second replaced the first |
| a **reason** was wrong, the choice stands | correct in place; bump `version`, add `history:` | one document at `v2`, and what `v1` got wrong |
| a **value** widened or was reworded | same: `version` + `history:` | the principle, versioned, with what changed |
| a **consequence** stopped being true | a later document records the new state | both, and the order they happened in |

The rule of thumb for the ambiguous case: *would a reader who acted on the old
version have done something different?* If yes, the choice changed — supersede.
If they would have done the same thing for a worse reason, correct in place.
That split is [ADR-019](../meta/decisions/ADR-019.md).

<!-- inactive-ok-file: ADR-010, ADR-015 — this page names them as the supersession examples -->

### Luria's own record is the worked example

None of this is hypothetical here. Every row above has already happened in this
repository, which is the point of the dogfooding clause in
[ADR-009](../meta/decisions/ADR-009.md) — a rule the project has never had to apply to
itself is a rule nobody has tested:

- **Choice changed.** [ADR-010](../meta/decisions/ADR-010.md) named the project
  `chester`; [ADR-011](../meta/decisions/ADR-011.md) replaced it. Later,
  [ADR-015](../meta/decisions/ADR-015.md) was superseded by
  [ADR-016](../meta/decisions/ADR-016.md) *within hours* — a decision that lasted an
  afternoon is exactly the kind whose reversal is worth being able to see.
- **Reason wrong, choice stands.** [ADR-018](../meta/decisions/ADR-018.md) is at `v2`.
  It rejected an alternative by citing a decision that didn't apply; the
  rejection survives on a better argument, and `history:` records both.
- **Value reworded.** [DP-2](../meta/design-principles.md#dp-2) and
  [DP-3](../meta/design-principles.md#dp-3) are both at `v2`. Each was first written
  about a single artifact and failed to generalize until a second instance
  forced it — which is the most useful thing either of them teaches, and it
  only survives because the version is on the document.
- **Consequence falsified.** [ADR-016](../meta/decisions/ADR-016.md) states as a
  consequence that a certain project's decisions are no longer cited anywhere.
  [ADR-017](../meta/decisions/ADR-017.md) made that false. [ADR-016](../meta/decisions/ADR-016.md)'s body stands as
  written and [ADR-017](../meta/decisions/ADR-017.md) is where a reader learns the state changed back —
  a consequence is an observation, and observations expire.

The failure mode to avoid is not editing. It is editing **without leaving a
trace**: a `history:` entry that doesn't say what the previous version claimed
is a correction wearing an improvement's clothes.

---

## 3. Fragments and generated views

`CHANGELOG.md`, the decision index, the principles document and similar
assembled pages are **views**, built from fragments — never hand-edited, and the
lint refuses hand edits.

Two kinds, and the difference is *whether the sources survive*
([ADR-012](../meta/decisions/ADR-012.md)). A **collected**
view — the changelog — consumes its fragments: they are deleted, the view
accumulates, and it can only ever be appended to. A **generated** view — the
decision index, the principles document, the devlog — is a pure function of
sources that persist, rebuilt from scratch every time, which is the only reason
a stale one can be *detected*. Prefer generation where the data is derivable;
there is then no collection step to forget.

The devlog is the case where that choice was got wrong first and corrected
([ADR-020](../meta/decisions/ADR-020.md)). It looked like a changelog and was collected
like one, but a changelog entry is a claim about a release and a devlog entry is
a **dated observation** — true when written, and still true. Consuming it throws
away the only copy of something that never expires. So the devlog is a
**journal**: entries are filed at their authoring timestamp
(`devlog.d/2026/08/03/211926.md`) with `luria journal new "A title"`, they
persist, and `docs/devlog/` is one generated book per month with a contents
list built from the titles. The timestamp is also the ordering, so what the log
says happened first is a property of the record rather than of the order the
branches landed.

The reasoning is [DP-2](../meta/design-principles.md#dp-2): a file every contribution must
append to is a *lock*. Concurrent branches collide in it contentlessly, and
every hand-merge is a chance to drop someone's work. The fix is structural —
each contribution owns a file nobody else writes, and the shared artifact is
assembled on a cadence ([ADR-002](../meta/decisions/ADR-002.md)).

Practical consequences: the answer to "which file do I edit?" is always *a
fragment*; and generated pages can be linted against their sources, so drift is
caught instead of discovered.

---

## 4. The drift doctrine

The most-earned lesson, [DP-3](../meta/design-principles.md#dp-3): **a hand-maintained
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

The enforcement clause is [DP-6](../meta/design-principles.md#dp-6): **fire before
trusting.** Every guard gets one deliberate sabotage run to prove it catches.
Provisioned is not working.

---

## 5. The collaboration model, in the open

**Culture must be compiled** ([DP-5](../meta/design-principles.md#dp-5)). A stateless
collaborator can't be socialized, so a norm that exists only as prose is
followed probabilistically. Norms that matter get walked up the ladder *prose →
convention → mechanism → guarantee*. When you find yourself repeating a
correction, that is the signal to walk the norm up a rung.

**No private brains** ([DP-7](../meta/design-principles.md#dp-7)). Agent files are legitimate
as **bootloaders** — pointers to the shared record, plus harness mechanics no
human needs — never as knowledge stores. The decision test: *would a new human
hire need this?* Then it belongs in the shared docs, and the agent file links to
it. This page is what the bootloader points at.

---

## 6. Leaving knowledge behind: the checklist

- [ ] `changelog.d/` fragment for anything an operator or user would notice.
- [ ] `luria journal new "…"` if the work *taught* something — and record wrong
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
      ([DP-6](../meta/design-principles.md#dp-6)).

## What keeps this true

- `luria lint` in CI: generated views match their sources, frontmatter conforms,
  references are followable.
- Deterministic assembly — same inputs, same view, so drift between record and
  view is mechanically checkable.
- The reports ([ADR-007](../meta/decisions/ADR-007.md)):
  what cites a retired decision, and what has been undecided for how long.
