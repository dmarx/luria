# Design principles

Standing values this project keeps re-deriving in review, written down once so
they can be cited by number ("per DP-1") instead of re-argued.

These are **principles, not decisions.** A [decision](decisions/README.md)
records a choice among alternatives at a point in time; a principle is a value
that decisions *cite*.

Principles are durable but not sacred — one can be revised or retired when we
learn better, with the reasoning captured wherever the change lands. Add one on
the *second* re-derivation of the same reasoning: one instance is a decision, a
pattern is a principle.

Each principle ends with an **origin note** naming the incident that earned it.
This is not decoration. A rule whose evidence is missing reads as taste, and
taste gets re-litigated by the next person with different taste.

---

## 1. A file every contribution must touch is a lock — hand out fragments, generate the view

When contributing requires editing a file *everyone else* also edits, in the
same place, that file is a lock. Concurrent branches serialize on it, and the
conflicts carry no information — two changes that share nothing still collide
because both appended after the last thing. That is contention, not
carelessness, so "resolve them carefully" is not the fix.

Let each contribution own a file nobody else writes, and *generate* the shared
artifact from those. When the shared file's content is derivable, generate it
outright — then there is no collection step to forget.

*Origin: seeded from Luria. Replace this note with your own first instance.*

## 2. A hand-maintained projection of a source of truth will drift — derive it

No hand-maintained parallel copy of what an authoritative source already knows.
The copy is written carefully and drifts anyway; a missed entry ships silently.

Remedies, strongest first: **derive** the projection; or **guard the property,
not the list** (a test asserting "the list contains these names" is the drifting
list in a costume); or, if a hand list must remain, **choose its failure
polarity** and say so in a comment. Fail-stale — the miss ships as silently
wrong behavior — is never acceptable, and is the naive default.

*Origin: seeded from Luria. Replace this note with your own first instance.*

## 3. Culture must be compiled

A stateless collaborator can't be socialized, so a norm that exists only as
prose is followed probabilistically. Norms that matter get walked up the ladder
*prose → convention → mechanism → guarantee*. When you find yourself repeating a
correction, that is the signal to walk the norm up a rung.

*Origin: seeded from Luria. Replace this note with your own first instance.*

## 4. Fire before trusting

Every guard, alert and CI gate gets one deliberate sabotage run to prove it
catches, before anyone relies on it. **Provisioned is not working.** Even a
fail-safe guard needs firing once, or it silently never delivers the benefit it
exists for. Say so in the record when you fire one.

*Origin: seeded from Luria. Replace this note with your own first instance.*

## 5. No private brains

Knowledge is shared across collaborators regardless of species. Agent files are
legitimate as **bootloaders** — pointers to the shared record — never as
knowledge stores. The test: *would a new human hire need this?* Then it belongs
in the shared docs.

*Origin: seeded from Luria. Replace this note with your own first instance.*
