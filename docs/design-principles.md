# Design principles

Standing values that guide Luria — the things a project keeps re-deriving in
review, written down once so they can be cited by number ("per [DP-2](design-principles.md#dp-2)") instead of
re-argued.

These are **principles, not decisions.** A [decision](decisions/README.md)
records a choice among alternatives at a point in time; a principle is a value
that decisions *cite*.

**Principles are living documents.** Each carries a version, and a revised one
says so — [DP-2](design-principles.md) and [DP-3](design-principles.md) are both
at v2, because each was first written scoped too narrowly and failed to
generalize until the second instance forced it. That history is the argument for
the version field: a principle stated about one artifact is a principle nobody
applies to the next one.

Add a principle on the *second* re-derivation of the same reasoning — one
instance is a decision, a pattern is a principle.

<!-- GENERATED below this line by `luria index`, from the fragments in
     docs/principles/. Edit those, not this file. -->

---

<a name="dp-1"></a>

## 1. No silent refusal

A tool that explains its refusal teaches its own model. If a precondition isn't
met, the tool *says so* — it never quietly no-ops. A no-op with no feedback
reads as "broken", which reads as "useless", when the real answer is "not here,
and here's why".

Applied here: the fragment collector raises when its insert marker is missing
rather than guessing where entries belong; `luria` prints the command list when
given a name it doesn't know; a directive that names an unknown region is
reported, with the known vocabulary named, rather than ignored.

The corollary that costs the most to follow: **a suppression must not become a
silence.** An acknowledgement that hides a warning is counted in the report, and
one that has stopped applying is reported in its own right — otherwise the
mechanism for saying "this is fine" becomes the mechanism for never hearing
about it again.

*v1 · origin: The strata-g design-language review, where tools silently no-opped on inputs that didn't meet their preconditions*

<a name="dp-2"></a>

## 2. A file every contribution must touch is a lock — hand out fragments, generate the view

When contributing requires editing a file *everyone else* also edits, in the
same place, that file is a lock. Concurrent branches serialize on it: every pair
of contributions conflicts, every rebase re-conflicts, and the conflicts carry
no information — two changes that share nothing still collide because both
appended after the last thing.

That is **contention, not carelessness**, so "resolve them carefully" is not the
fix; each hand-resolution is another chance to silently drop somebody's
contribution.

The fix is structural: let each contribution own a file nobody else writes, and
*generate* the shared artifact from those on a cadence. The shared file stops
being a source and becomes a **view**. Better still, when the shared file's
content is derivable from the contributions themselves, generate it outright and
delete the hand-maintained copy — then there is no collection step to forget.

The tell is a file whose diff, in every single contribution, is "+N lines in the
same place". Notice it before the third instance.

*Version 2 exists because version 1 didn't generalize.* The mechanism was
written down as a decision about **one file**, so when the same conflicts
appeared on a second shared document months later, nobody recognized it. A value
stated about one artifact is a value nobody applies to the next one.

*v2 · shaped by [ADR-002](../record/decisions.d/ADR-002.md), [ADR-004](../record/decisions.d/ADR-004.md) · origin: Fragments assembled into a changelog; then, months later, the identical conflicts recurring on the narrative log; then the decision index*

<a name="dp-3"></a>

## 3. A hand-maintained projection of a source of truth will drift — derive it

No hand-maintained parallel copy of what an authoritative source already knows.
The copy is written carefully, by someone looking directly at the source, and it
drifts anyway: sooner or later an entry is missed, and a missed entry ships
silently. This is **not a risk but a rate** — when one project converted five
such lists, five out of five had already drifted.

Three remedies, in order of strength:

1. **Derive the projection from the source.** A registry query, a generated
   view. Drift becomes impossible; a new entry extends every projection with no
   edit.
2. **When it must stay code, guard the property, not the list.** A test that
   asserts "the list contains these names" is the drifting list in a costume.
   Assert the invariant — *any change that alters the output must alter the
   projection* — and fire the guard once to prove it catches
   ([DP-6](design-principles.md#6-fire-before-trusting)).
3. **When a hand list must remain, choose its failure polarity** and say so in a
   comment. Fail-safe (the missed entry still works, suboptimally) and fail-loud
   (the miss is immediately visible) are both acceptable. **Fail-stale — the
   miss ships as silently wrong behavior — is never acceptable**, and it is the
   polarity a naive list has by default.

In this package, the decision index is rung 1 and the reference lint is rung 2.

*v2 · shaped by [ADR-004](../record/decisions.d/ADR-004.md), [ADR-005](../record/decisions.d/ADR-005.md) · origin: A hardcoded type union that had drifted to 13 of 21 keys; generalized by a later arc where every one of five converted projections was already wrong*

<a name="dp-4"></a>

## 4. One authoritative implementation, read the same way everywhere

The load-bearing logic of a thing lives in exactly one tested place, and every
consumer reads it identically. A second copy — or a fallback each consumer must
*remember* to prefer — is a latent bug: sooner or later one consumer diverges
and silently ships stale behavior.

The sharpest instance here: **the linter and the fixer share one scanner**, so
the linter can never demand a rewrite the fixer wouldn't make. Two
implementations of "what counts as a bare reference" would drift within a month,
and the failure mode is the worst kind — a CI failure whose suggested remedy
doesn't work.

The same reasoning rejected threading configuration through every entry point
([ADR-006](../record/decisions.d/ADR-006.md)): the
second caller forgets an argument, and the two checks quietly cover different
files.

"The new thing overrides the old at one site" is the smell; "the new thing
*replaces* the old everywhere" is the fix.

*v1 · shaped by [ADR-005](../record/decisions.d/ADR-005.md), [ADR-006](../record/decisions.d/ADR-006.md) · origin: A tool-icon migration whose bug was precisely a fallback that only one render site preferred, so every other site leaked the legacy value*

<a name="dp-5"></a>

## 5. Culture must be compiled

A stateless collaborator can't be socialized. Half the contributors to a modern
codebase arrive with no memory, read some pages, work, and vanish — so a norm
that exists only as prose is followed probabilistically, and the ones that
matter get walked up the ladder:

> prose → convention (file layout) → mechanism (a glob, a fragment directory) →
> guarantee (types, CI, a lint)

When you find yourself repeating a correction, that is the signal to walk the
norm up a rung. This package is one set of norms at rung four, and every check
in it started as a paragraph somebody kept having to repeat.

The demonstration is worth keeping: with the "cite by link" convention written
down but unguarded, one corpus drifted not toward *unlinked* but toward
**random** — the same reference linked sixty times and bare thirty more.
Randomness is worse than a uniform mistake, because a reader can't learn the
convention from the corpus and stops trying.

*v1 · shaped by [ADR-003](../record/decisions.d/ADR-003.md), [ADR-005](../record/decisions.d/ADR-005.md) · origin: The strata-g project-memory doctrine. The linked-versus-bare reference split was the demonstration: convention written down but unguarded, and the corpus drifted toward random rather than toward wrong*

<a name="dp-6"></a>

<!-- inactive-ok-file: ADR-007 — the evidence trail predates the supersession; ADR-035 carries the doctrine -->
# DP-006: Fire before trusting

Every guard, alert, and CI gate gets one deliberate sabotage run to prove it
catches, before anyone relies on it. **Provisioned is not working.**

One project has been bitten twice by mechanisms that sat green and inert: an
alert shape that could never fire, and a CI fast path whose *fail-safe* polarity
made a month of inertness invisible. Neither was found by the thing it guarded;
both were found by accident.

Even a fail-safe guard needs firing once, or it silently never delivers the
benefit it exists for.

**Say so in the record.** A devlog entry naming the sabotage run — what was
broken, what the guard printed, what it printed after the repair — is the
difference between a guard someone trusts and a guard someone re-tests from
scratch because they can't tell whether it works.

*v1 · shaped by [ADR-007](../record/decisions.d/ADR-007.md) · origin: Two inert mechanisms in strata-g — an alert shape that could never fire, and a CI fast path whose fail-safe polarity made a month of inertness invisible. Both were discovered by accident rather than by the thing they guarded*

<a name="dp-7"></a>

## 7. No private brains

Knowledge is shared across collaborators regardless of species. Agent files
(`CLAUDE.md` and kin) are legitimate as **bootloaders** — pointers to the shared
record, plus harness mechanics no human needs — never as knowledge stores.

A private memory is a document that skipped review: it conditions one class of
collaborator while drifting uncontested, and nobody can correct what they can't
see.

The decision test: *would a new human hire need this?* Then it belongs in the
shared docs, and the agent file links to it.

*v1 · origin: The strata-g project-memory doctrine*

<a name="dp-8"></a>

## 8. File it in the same contribution as the work

"Later" is a euphemism for never. A fact filed while its context is loaded costs
a paragraph; re-derived cold, it costs a session — the **rediscovery tax**, paid
per collaborator, forever.

This is why the paperwork loop has to be cheap: a fragment is one new file, the
index is generated, and the lint tells you exactly what is missing. Any friction
here is paid back in re-derivation, at a much worse rate.

The corollary that people skip: **record the wrong theories.** The approach that
failed on Tuesday leaves no commit, appears in no diff, and is the single most
expensive thing for the next person to rediscover.

*v1 · shaped by [ADR-002](../record/decisions.d/ADR-002.md) · origin: The reason the fragment convention exists at all — the changelog was being reconstructed retroactively from git log, badly*

<a name="dp-9"></a>

## 9. Structure is read before text — spend affordances deliberately

An artifact tree — a repository, a directory, a document set — is an interface,
and it is read before any file is opened. Names, placement, sort order,
prominence, a suffix: these reach a visitor ahead of every sentence, and they
are doing work whether or not anyone designed them. The only choice available
is *deliberate or accidental*.

Spent deliberately, affordances do three jobs:

**Shaping attention.** What wandering lands on is what gets read, so prominence
is a budget. Entrypoints and summaries belong front-and-center; archives,
machinery and ground truth belong a step removed, reachable on purpose. The
polarity runs both ways: burying an entrypoint quietly reclassifies it (a log
whose newest page sits two clicks deep reads as an archive, whatever it says),
and exposing internals taxes every visitor with a decision they shouldn't have
to make.

**Enabling discovery.** Structure answers *where would X be?* before anyone
greps. Consistent marks and mirrors make locations predictable — what you read
at one path, you file at its counterpart — and predictability compounds: a
rule expressible as a path convention is discoverable by every visitor,
human or stateless; a rule living only in prose is discoverable by whoever
happens to read that prose.

**Diagnosis.** Affordance inconsistency is a smell to *read*, not an
untidiness to tolerate. The same shape carrying opposite rules — one
`README.md` you must edit and another you must not; a marked container beside
an unmarked sibling doing the same job — says a rule has moved out of the tree
and into somebody's memory. A file whose neighbours are the wrong kind — an
authored `.stub` sitting beside the generated page it feeds — says something
is filed where it doesn't belong. When an affordance feels wrong, trust the
feeling and ask which boundary it is straddling; the discomfort is usually a
distinction the layout has stopped expressing.

Two disciplines keep the spend honest. **Structural beats documentary**: a
comment saying "GENERATED — do not edit" is read after landing in the wrong
place and enforces nothing; a directory name is read before, and a linter can
hold it. And where the structure encodes a checkable property, walk it up
[DP-5](design-principles.md#dp-5)'s ladder — the read/write boundary
([ADR-021](../record/decisions.d/ADR-021.md)) is this principle's worked
application, and its payoff rung is a lint: a view directory holds only what
the generator wrote, so a hand edit there fails with the polarity
[DP-3](design-principles.md#dp-3) demands.

<!-- url-ok-block: SG-DP-18 — the construction reaches the right document, but strata-g's legacy anchors are heading-derived and no template can produce the slug -->

The sibling claim, from the pilot:
[SG-DP-18](https://github.com/dmarx/strata-g/blob/main/docs/design-principles.md#18-the-affordance-is-the-contract),
"the affordance is the contract" — an affordance must not *lie*; what a
control suggests is what the action does, verified from the same inputs. That
principle binds affordances to the truth. This one is its complement about
*reach*: affordances are the widest channel an artifact has — spend them,
don't merely avoid falsifying them.

*v1 · shaped by [ADR-012](../record/decisions.d/ADR-012.md), [ADR-013](../record/decisions.d/ADR-013.md), [ADR-021](../record/decisions.d/ADR-021.md) · origin: An inventory of one repository's layout found the same rules expressed structurally in some places and not at all in others — two source containers marked `.d` and two unmarked, a generated document beside its own sources, an index buried under the things it indexes, and `README.md` meaning "edit me" in one directory and "never edit me" in the next. The layout had been shaping attention the whole time; nobody had been steering it*

<a name="dp-10"></a>

## 10. Defaults follow the failure mode: guards opt out, disclosures opt in

Every switch has a silent position — the behavior a project gets when nobody
reads the docs. The silent position should be the one whose failure is
cheapest, and the two families of feature fail in opposite directions:

**A guard that is off costs you what it would have caught.** Checks, lints,
staleness detection, reference resolution: their failure mode is *missing
something*, and the miss is silent by nature — nobody notices the warning
that didn't fire. So guards default **on**, and disabling one is opt-out:
sited, spelled out, and countable (`unresolved-ok:` on the line it excuses,
`unlinted-file` in the file it exempts). The escalation dial works the same
way — a new warning class arrives warning-by-default, and a project *opts
into* failing on it ([ADR-035](../record/decisions.d/ADR-035.md)) — because the
guard being visible is the default that costs nothing, while the guard
failing CI on day one costs adoption.

**A disclosure that is on costs you what it revealed.** Provenance
identifiers, session URLs, anything that couples the record to a system
beyond the repo or publishes more than the author reviewed: their failure
mode is *exposing or imposing something*, and that failure is irreversible
in a way a missed warning is not — a secret unshipped is recoverable, a
secret shipped is not. So disclosures default **off**, and enabling one is
opt-in: a config line that names what starts flowing.

The shared requirement is that the deviation is **written down where it
applies** — a directive comment at the site, a key in the config — never
ambient state, never a flag someone passed once. A default you departed
from silently is a trap for the next reader in either direction.

The test, when a new switch appears: *what does the silent position cost,
and who pays?* If the project pays in missed defects, on-by-default. If
the author pays in unwanted exposure, off-by-default. A switch where both
answers feel true is usually two switches wearing one name — split it.

*v1 · shaped by [ADR-035](../record/decisions.d/ADR-035.md)*

<a name="dp-11"></a>

## 11. It's not mine, but I'll pick it up anyway

When you encounter debt — a stale comment, a drifted convention, a dead test, a
number that collides, a guard nobody wired up — **fix it**, whether or not it
belongs to the thing you came here for. Leaving the shared space tidier than you
found it takes precedence over staying inside your task's boundary or worrying
about stepping on someone's toes.

The principle exists because the *default* is the opposite, and the default is
expensive. Debt survives not because anyone decided to keep it but because every
individual encounter with it was, reasonably, someone else's problem — so the
cost is paid over and over in small amounts by people who each correctly
concluded it wasn't theirs to fix. *If not me, then who? If not now, then when?*
is the whole argument, and the answers are usually *nobody* and *never*.

Two rules keep this from becoming license to sprawl:

- **Repair, don't redesign.** Picking up litter is not remodelling the building.
  If the tidy-up turns out to be a decision rather than a repair — it needs a
  decision record, or it changes behaviour someone relies on — stop and file it
  rather than smuggling it in. A drive-by refactor inside an unrelated change is
  its own kind of mess.
- **Say what you picked up.** An unexplained unrelated change in a diff reads as
  noise, or worse as a mistake. One line in the commit message turns it into a
  gift.

Applied here — three repairs, none of them the task at hand:

- Porting the migration machinery surfaced a `legacy-spellings` class that
  `status_sections` emitted but `FAILABLE` never listed, so the enforcement dial
  rejected a notch it was already reporting on ([#81](https://github.com/dmarx/luria/pull/81)). Nothing to do
  with migrations; one word, plus the test that should have caught it.
- Declaring a third scheme in a downstream project surfaced that every
  `_template.md` here still told the reader to copy it by hand, long after
  `luria new` replaced that workflow ([#82](https://github.com/dmarx/luria/pull/82)) — six files, across the
  shipped scaffold and this record both.
- Filing *this* principle surfaced that the `DP` scheme never took
  `allocate = "merge"` while the decisions did, so two concurrent branches could
  each claim the same principle number — precisely the collision
  [ADR-049](../record/decisions.d/ADR-049.md) exists to prevent, and one that had
  already happened. This document is the first filed under the fix.

The corollary, and the expensive half: a record's own machinery is both the
easiest place to apply this and the easiest place to over-apply it. Every repair
above arrived with a test or a measurement attached. None of them redesigned
anything, and that restraint is what keeps the licence worth having.

*v1 · origin: Carried in from strata-g, luria's first consumer, after a stretch in which almost every repair here was found by tripping over an unrelated one*

<a name="dp-12"></a>

## 12. One document, one thing

**A document with two unrelated halves is one nobody can cite half of.**

Bundling is always cheaper at writing time. One record, one review, one merge —
and the second half arrives free, because it was going to be written anyway.
The cost lands later and never goes away.

This was first written about decisions, and it is not about decisions. It holds
for any document a reader is expected to name: a decision, a principle, a
practice in a record of practices, a claim in an anthology. The unit is
whatever gets cited.

## What it costs

**The second half has no code.** A citation is how a record is used: an
argument names its premise, a module names the decision it implements, a lint
message names the rule it enforces. Half a document cannot be named, so the
half that was cheap to add is the half nothing can point at — and a rule
nothing points at is a rule nobody knows applies to them.

**Superseding withdraws more than intended.** A document that changes gets
superseded whole. If two things share a record, retiring the one that aged out
silently retires the one that did not, and the record now says nothing about a
question it had answered. That is the failure the status vocabulary exists to
prevent, reintroduced at a coarser grain.

**Alternatives stop being reconstructable.** For a decision, the alternatives
section is the highest-value part, and it only works when it is the
alternatives to *one* choice. Two choices produce a cross-product, or — far
more often — an alternatives section that silently covers whichever half the
author found more interesting.

## Two tests

**Could the halves have been decided differently?** If a project could adopt
one and reject the other, they are two documents, however naturally they
arrived together.

That one only fires while writing, and it depends on the author asking. Typed
edges ([ADR-071](../record/decisions.d/ADR-071.md), [ADR-060](../record/decisions.d/ADR-060.md))
make a second test possible, and this one fires afterwards, mechanically:

**Does an edge into this document have to name which *part* of it applies?**
If stating what a relation asserts requires pointing at one clause of its
target, the target is two documents.

Note what this test is not. An `overrides` edge already means *where both bear,
this one wins* — the overlap is decided by the two documents' contents, so an
edge is not over-claiming merely by being silent about scope. The tell is
narrower and shows up in the prose beside the edge: a body that has to explain
which sentence of the target it is arguing with.

The worked case is a record of an assistant's operating constitution, which
contains no decisions at all. A boundary — *never infer a person's pronouns
from their name* — declares that it `overrides` a practice titled *deliver the
whole requested scope; state assumptions rather than narrowing*. But the
boundary's body does not argue with delivering the whole scope. It argues with
a different claim the same document happens to carry: *make the routine
judgment call yourself rather than escalating it*. The override had to say so
in prose, because the code it names covers both.

Applying the first test confirms it. *Deliver the whole scope* and *make the
routine call yourself* could be adopted separately — a project could want one
and reject the other — so they were always two practices. They had simply
arrived in the same paragraph of the source. Splitting them let each override
name what it actually beats, and immediately exposed a second error: one of the
two edges, checked against the narrower practice, turned out not to hold at all.

That is the useful property. The a-priori test needs an author to stop and ask.
This one arrives as friction while writing something else, which is when a
granularity defect is cheapest to notice and most likely to be noticed at all.

## Why not just qualify the edge

Because a condition on a relation is unfalsifiable in exactly the way this
record's machinery exists to prevent. `overrides` is checked — the code must
resolve, to a document of the declared scheme, that actually exists. A `when:`
beside it is prose in a data field: nothing evaluates it, nothing notices when
it stops being true, and nothing tells a reader whether the qualifier or the
edge governs their case. It is escalating emphasis in a new costume, one level
up, and the graph it produces is worse than no graph because it looks checked.

This is why [#141](https://github.com/dmarx/luria/issues/141) puts `when`
expressions among its non-goals, and why it refuses precedence between
configuration surfaces — a conflict there is an error rather than something a
tie-break rule resolves. Same move: **decline the qualifier, and remove what
made it necessary.**

## What this is not

Not an argument for small documents. A document covering one thing can be long,
and usually should be — the context, the alternatives and the consequences of a
single claim are most of what makes a record worth keeping.

Nor is it an argument against related documents landing together. Ship them in
one contribution if that is honest; give them separate codes so each can be
cited, revisited, and retired on its own evidence.

And it is not a licence to split on sight. The second test is the discipline
that keeps it honest: split when something *points* at a part rather than the
whole, not whenever a document could conceivably be subdivided. A record of
maximally small documents has the same problem in reverse — every claim needs
five citations to state, and none of them means anything alone.

*v2 · shaped by [ADR-035](../record/decisions.d/ADR-035.md), [ADR-056](../record/decisions.d/ADR-056.md), [ADR-060](../record/decisions.d/ADR-060.md), [ADR-071](../record/decisions.d/ADR-071.md) · origin: Three splits in one session, each made for the same reason and none of them by rule: a lint check separated from the vocabulary it reads, two scheme audits written as two decisions rather than one, and a status feature split from the report that would have caught the bug motivating it. Then, in a record of practices rather than decisions, an `overrides` edge whose prose had to name which clause of its target it argued with — the same defect, arriving as a relation instead of as a bundle*

<a name="dp-13"></a>

## 13. Exempting a ledger from one matcher exempts it from none of the others

A mechanism that rewrites, flags or retires instances of a pattern usually
keeps a record of what it did, and that record is written in the pattern's own
spelling. A migration's `formerly:` field names the old codes. An
acknowledgement names the code it excuses. To anything matching that pattern,
the record is indistinguishable from an instance of it.

On the day this record's first migration ran, three subsystems ate the stamps
it had just written:

- the **sweep** rewrote the `formerly:` values into the new spelling, erasing
  the map at its source, in the same operation that created it;
- the **fixer**'s modernize pass did the same from the other side, turning
  every alias into a self-reference on the live corpus;
- the **scan** counted each stamp as a citation of the old code, so every
  migrated document warned about its own former name.

Three separate discoveries, and that is the part worth keeping. Each
subsystem matched the pattern on its own terms, so finding the first failure
taught nothing about the second, and fixing the first protected nothing
else. That is what makes this a principle
rather than a bug report: **an exemption is a property of the matcher, not of
the ledger**, and there is no place to put one where every matcher will see
it.

So the mask belongs to the matcher's definition — written where the matching
happens, and with a test that has seen it fire, because a guard is trusted
only once it has been caught working ([DP-6](design-principles.md#dp-6)).
What does not count is an execution order that happens to write the ledger
after the sweep, a glob that happens to miss the file, or a format the regex
happens not to match. Those are real protection today and gone after the next
refactor, and they fail quietly: a ledger does not complain when it is eaten.
It stops being true, and everything derived from it degrades into
self-reference.

Applied here, in a subsystem that got it right. The reference scan blanks the
span of any acknowledgement before counting citations, because
`inactive-ok: ADR-012` names the very code the retired-citation check looks
for —
without the mask an annotation would excuse itself, and could never go stale.
The mask matches the *shape* of a directive rather than the parsed directives,
so that an example of one in the documentation is covered too. A code inside a
URL gets the same treatment for the same reason. Three masks, one subsystem,
each written next to the match it protects.

The test, when building anything that matches a pattern: *does this system
keep a record of what it matched, and is that record spelled the same way?*
If so, the mask is part of the definition of the match — and if another
matcher for the same pattern already exists, it needs its own.

*v1 · shaped by [ADR-040](../record/decisions.d/ADR-040.md), [ADR-049](../record/decisions.d/ADR-049.md) · origin: The first migration's first live day: three subsystems attacked the `formerly:` stamps the migration had just written, independently, and each was found separately because fixing one taught nothing about the others*

<a name="dp-14"></a>

## 14. Meet the project where it is

Aim to be usable by whatever project has something worth remembering. It
picked its language, its operating system, its forge and its file layout for
reasons that had nothing to do with keeping a record, and it made those
choices long before this tool showed up. The record is the guest.

That is an aspiration rather than a rule, because it is never finished — but
it is a testable one, and here is where it has been tested so far:

- **Language.** Source files are scanned for references as text, with no
  parser and no list of languages. A code in a Rust comment is a claim about
  why that code is the way it is, and so is one in a Makefile; the scanner
  does not need to know which it is holding. Reaching a new language means
  adding a glob.
- **Operating system and terminal.** Files are UTF-8 everywhere, because a
  record gets cloned onto whatever machine the next reader has. The console is left at
  whatever encoding the platform gave it, and taught to degrade instead of
  raise.
- **Forge.** An issue URL is inferred from the origin remote for the hosts
  whose issue paths are known, and left empty for the rest, so a self-hosted
  instance gets a record that works and one field to fill in. The shipped CI
  is a convenience over plain Git.
- **Storage.** Markdown is what a record looks like today. Identity, standing,
  declared rules and generated views are the model, and none of them says
  anything about a file format.

The discipline that keeps this true is a pair:

> **Be explicit in what you write, and forgiving in what you assume.**

Files get an encoding named at every call site, because a file has a reader on
another machine and has to open there. The console gets `errors="replace"`,
because it has one reader and guessing wrong should cost a `?` rather than the
command. An unrecognised forge yields nothing rather than a plausible URL,
because a wrong guess would put a broken link on every entry that carries an
issue.

**The aspiration is easy to hold and easy to lose, because coupling rarely
arrives as a decision.** Nobody chose to require a UTF-8-capable console. The
package simply never said what it needed, and a hundred call sites inherited
whatever the platform preferred — which is invisible on the machine where the
code was written and a stack trace on somebody's first run. So the question
worth asking is not *which environments do we support*, which gets asked
during design and answered generously. It is *what have we assumed and never
written down*, which otherwise gets asked for the first time by a stranger.

What it costs is worth saying plainly, because the bill comes in capability.
No per-language parsers, so a comment marker inside a string literal is
matched anyway. No format-specific model, so nothing exploits what markdown
makes cheap. No guessing at an unknown forge, so a self-hosted instance gets
no inference at all. Each of those is precision given up in exchange for
reach — and reach is the point, because the projects that most need a memory
are rarely the ones that look like yours.

*v1 · shaped by [ADR-064](../record/decisions.d/ADR-064.md) · origin: A Windows user ran `luria init` and then `luria index`, and got a stack trace writing a check mark into a status report. Nothing about their project was unusual. The tool had required a UTF-8-capable platform without ever saying so*
