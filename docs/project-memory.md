# Project memory: how a repository thinks

The doctrine behind the layout. What belongs in which layer, and why the layers
are separate.

## The problem

A repository's memory is not in its documentation. It is in:

- the arguments people had, and how they came out
- the alternatives that were rejected, and why
- the constraints discovered painfully and never written down
- the things that were tried and failed

None of that survives in code, and almost none of it survives in a README. It
lives in review threads, in chat scrollback, and in the heads of whoever was
there. When those people leave, the project loses the ability to explain itself
— and then re-litigates the same questions, badly, because the reasoning is gone
but the conclusions remain.

An AI agent joining the project has *none* of it, ever. It sees the conclusions
and nothing about why. That is why this matters more now than it did.

## Four layers

Each answers a different question, ages differently, and is written at a
different moment.

| Layer | Answers | Ages by | Written |
|---|---|---|---|
| **Principles** | what we value | revision | on the second re-derivation |
| **Decisions** | what we chose, and what we rejected | supersession | when the choice is made |
| **Changelog** | what changed, for a user | accumulation | per contribution |
| **Devlog** | what happened, for us | never — it is dated | when something went wrong |

They are separate because they age differently. A principle is a living document
that gets *revised*: widen the wording, bump the version. A decision is a
snapshot that gets *superseded*: the old one stays, intact and marked, because
its reasoning is the record of why the new one was needed. Collapsing them
produces a document that is either permanently stale or permanently
unattributable.

### Principles

Standing values the decisions cite. Written down once so they can be referenced
by number instead of re-argued.

**Add one on the second re-derivation of the same reasoning.** One instance is a
decision; a pattern is a principle. Writing them in advance produces a list of
platitudes nobody cites.

Each ends with an **origin note** naming the incident that earned it. This is
not decoration: a rule whose evidence is missing reads as taste, and taste gets
re-litigated by the next person with different taste.

### Decisions

A choice among alternatives at a point in time. Write one when you rejected an
alternative, chose a constraint, or made something a future edit could silently
violate.

The **alternatives considered** section is the highest-value part and the one
most often skipped. It is what stops the decision being re-litigated, and what
tells a future reader whether their new idea is actually new. A decision without
it is a note.

**One decision, one thing.** A record with two unrelated halves is one nobody
can cite half of: the second half has no code, so nothing can point at it, and
superseding the first silently retires reasoning nobody meant to withdraw.

**Supersede rather than edit** when the *choice* changes. Correct in place when
only a reason was wrong, and bump the version with a history entry. The rule
objects to silent revision, not to editing.

### Changelog

What changed, reader-facing. One **fragment** per contribution, collected into
the document on a cadence.

Fragments exist because a single file every contribution must touch is a lock:
every branch edits the same lines, every merge conflicts, and the conflict is
never interesting. Hand out fragments; generate the view.

### Devlog

What actually happened. The failed approach, the trap, the thing that looked
right for an hour. **The wrong theories are the point** — they are what stops
the next person spending the same hour.

A journal, not a scheme: entries are dated and historical, true about the day
they were written and never retroactively wrong. Nothing in a devlog is ever
superseded, because it was never a claim about the present.

This is the layer that survives contact with the future best, and the one most
often skipped because it feels like admitting things.

## The two surfaces

```
record/    WRITE — hand-edited sources, one file per record
docs/      READ  — indexes, tag pages, collected documents, reports
```

A source directory holds things a writer files. A view directory holds pages a
reader browses. The thing a reader opens is never the thing a writer edits, and
a stale view is a lint failure rather than a quiet divergence.

The exception that proves it: a **stub** is the hand-written prose introducing a
generated index. It lives on the write surface because it is written, and
renders into the read surface with everything else — which is why a link written
in a stub resolves from where the *index* lands.

## How the record is revised

Four moves, and picking correctly is most of the skill:

**Correct in place.** The choice stands, a reason was wrong. Bump `version:`,
add a `history:` entry saying what the previous version claimed. Editing is
fine; *silent* editing is not.

**Supersede.** The choice changed. Add a new record, mark the old one
`Superseded — by X`, leave its body intact. The old reasoning is why the new
decision exists.

**Reject.** It was wrong, and nothing replaces it. The body stays — a rejected
record with a good refutation is more valuable than one that was never written.

**Defer.** You cannot settle it yet and something specific will settle it. Say
what. `Deferred` is honest where `Proposed` forever is not.

What is never a move: **deleting a record**, or editing one so it says something
else. The point of a code is that a citation of it means something stable.

## The one-sentence version

Write down what you decided and why; cite it where it does work; and when you
change your mind, let the machine tell you what that costs.
