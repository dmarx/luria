# Design principles

Standing values that guide Luria — the things a project keeps re-deriving in
review, written down once so they can be cited by number ("per DP-2") instead
of re-argued.

These are **principles, not decisions.** An [ADR](decisions/README.md) records a
choice among alternatives at a point in time; a principle is a value that
decisions *cite*. The split is [ADR-003](decisions/adr-003-status-vocabulary-and-frontmatter.md).

Principles are durable but not sacred — one can be revised or retired when we
learn better, with the reasoning captured wherever the change lands. Add a
principle on the *second* re-derivation of the same reasoning: one instance is
an ADR, a pattern is a principle.

Every principle below was earned in [strata-g](https://github.com/dmarx/strata-g),
where this machinery was built before it was extracted. The origin notes name
the incident, because a principle whose evidence is missing reads as taste.

---

## 1. No silent refusal

A tool that explains its refusal teaches its own model. If a precondition isn't
met, the tool *says so* — it never quietly no-ops. A no-op with no feedback
reads as "broken", which reads as "useless", when the real answer is "not here,
and here's why".

Applied here: the fragment collector raises when its insert marker is missing
rather than guessing where entries belong; `luria` prints the command list when
given a name it doesn't know; a directive that names an unknown region is
reported rather than ignored.

*Origin: the strata-g design-language review, where tools silently no-opped on
graphs that didn't meet their preconditions.*

## 2. A file every contribution must touch is a lock — hand out fragments, generate the view

When contributing requires editing a file *everyone else* also edits, in the
same place, that file is a lock. Concurrent branches serialize on it: every pair
of contributions conflicts, every rebase re-conflicts, and the conflicts carry
no information — two changes that share nothing still collide because both
appended after the last thing. That is **contention, not carelessness**, so
"resolve them carefully" is not the fix; each hand-resolution is another chance
to silently drop somebody's work.

The fix is structural: let each contribution own a file nobody else writes, and
*generate* the shared artifact from those on a cadence. The shared file stops
being a source and becomes a **view**. Better still, when the shared file's
content is derivable from the contributions themselves, generate it outright and
delete the hand-maintained copy — then there is no collection step to forget.

The tell is a file whose diff, in every single contribution, is "+N lines in the
same place". Notice it before the third instance.

*Origin: `changelog.d/` fragments assembled into `CHANGELOG.md` — and, months
later, the same conflicts recurring on the devlog until it got the identical
treatment. That gap is why this is a principle rather than two decisions: the
mechanism existed and its reasoning was written down, but as a decision about
**one file** instead of a value about shared artifacts, so nobody generalized
it. The third instance was the decision index, which is now generated outright.*

## 3. A hand-maintained projection of a source of truth will drift — derive it

No hand-maintained parallel copy of what an authoritative source already knows.
The copy is written carefully, by someone looking directly at the source, and it
drifts anyway: sooner or later an entry is missed, and a missed entry ships
silently. This is not a risk but a rate — when strata-g converted five such
lists, **five out of five had already drifted**.

Three remedies, in order of strength:

1. **Derive the projection from the source** — a registry query, a generated
   view. Drift becomes impossible; a new entry extends every projection with no
   edit.
2. **When it must stay code, guard the property, not the list.** A test that
   asserts "the list contains these names" is the drifting list in a costume.
   Assert the invariant — *any change that alters the output must alter the
   projection* — and **fire the guard once** to prove it catches before trusting
   it.
3. **When a hand list must remain, choose its failure polarity** and say so in a
   comment. Fail-safe (the missed entry still works, suboptimally) and fail-loud
   (the miss is immediately visible) are both acceptable. **Fail-stale — the
   miss ships as silently wrong behavior — is never acceptable**, and it is the
   polarity a naive list has by default.

*Origin: a hardcoded type union that had drifted to 13 of 21 keys; generalized
by a later arc in which every one of five converted projections was already
wrong. The decision index in this repo is rung 1; the reference lint is rung 2.*

## 4. One authoritative implementation, read the same way everywhere

The load-bearing logic of a thing lives in exactly one tested place, and every
consumer reads it identically. A second copy — or a fallback each consumer must
*remember* to prefer — is a latent bug: sooner or later one consumer diverges
and silently ships stale behavior.

The sharpest instance here: the linter and the fixer share one scanner, so the
linter can never demand a rewrite the fixer wouldn't make. Two implementations
of "what counts as a bare reference" would drift within a month, and the failure
mode is the worst kind — a CI failure whose remedy doesn't work.

*Origin: a tool-icon migration whose bug was precisely a fallback that only one
render site preferred, so every other site leaked the legacy value.*

## 5. Culture must be compiled

A stateless collaborator can't be socialized. Half the contributors to a modern
codebase arrive with no memory, read some pages, work, and vanish — so a norm
that exists only as prose is followed probabilistically, and the ones that
matter get walked up the ladder:

> prose → convention (file layout) → mechanism (a glob, a fragment directory) →
> guarantee (types, CI, a lint)

When you find yourself repeating a correction, that is the signal to walk the
norm up a rung. This package is one norm at rung four, and every check in it
started as a paragraph somebody kept having to repeat.

*Origin: the strata-g project-memory doctrine. The linked-vs-bare reference
split was the demonstration: with the convention written down but unguarded, the
corpus drifted not toward "unlinked" but toward random, which is worse — a
reader can't learn which references are worth clicking.*

## 6. Fire before trusting

Every guard, alert, and CI gate gets one deliberate sabotage run to prove it
catches, before anyone relies on it. **Provisioned is not working.**

strata-g has been bitten twice by mechanisms that sat green and inert: an alert
shape that could never fire, and a CI fast path whose fail-safe polarity made a
month of inertness invisible. Even a fail-safe guard needs firing once, or it
silently never delivers the benefit it exists for.

Corollary: say so in the record. A devlog entry that names the sabotage run is
the difference between a guard someone trusts and a guard someone re-tests.

*Origin: two inert mechanisms, both discovered by accident rather than by the
thing they were guarding.*

## 7. No private brains

Knowledge is shared across collaborators regardless of species. Agent files
(`CLAUDE.md` and kin) are legitimate as **bootloaders** — pointers to the shared
record, plus harness mechanics no human needs — never as knowledge stores. A
private memory is a document that skipped review, conditioning one class of
collaborator while drifting uncontested.

The decision test: *would a new human hire need this?* Then it belongs in the
shared docs, and the agent file links to it.

*Origin: the strata-g project-memory doctrine.*

## 8. File it in the same contribution as the work

"Later" is a euphemism for never. A fact filed while its context is loaded costs
a paragraph; re-derived cold, it costs a session — the **rediscovery tax**, paid
per collaborator, forever.

This is why the paperwork loop has to be cheap: a fragment is one new file, the
index is generated, and the lint tells you exactly what is missing. Any friction
here is paid back in re-derivation, at a much worse rate.

*Origin: the reason the fragment convention exists at all — the changelog was
being written retroactively from git log, badly.*
