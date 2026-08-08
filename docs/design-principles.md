# Design principles

Standing values that guide Luria — the things a project keeps re-deriving in
review, written down once so they can be cited by number ("per DP-2") instead of
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

## 11. The ledger looks like the prey: exempt it structurally, not incidentally

A mechanism that rewrites, flags, or retires instances of a pattern usually
keeps a record of what it did — and that record is written in the pattern's
own spelling. A migration's `formerly:` field names the old codes. A
redirect map names the dead URLs. A suppression list names the warnings it
suppresses. To every hunter of that pattern, the ledger is
indistinguishable from prey.

The failure is not hypothetical and not singular. On the day the record's
first migration ran, three subsystems attacked the stamps it had just
written, independently, each through its own mouth:

- the **sweep** rewrote the `formerly:` values into the new spelling —
  erasing the map at its source, in the same operation that created it;
- the **fixer**'s modernize pass did the same from the other side, turning
  every alias into a self-reference on the live corpus;
- the **scan** counted each stamp as a citation of the old code — every
  migrated document warning about its own former name, forever.

Three mouths, three separate discoveries, one cause. That multiplicity is
the point: exempting the ledger in one place does not exempt it anywhere
else, because each consumer of the pattern matches it independently.

So the exemption must be **structural**: a mask the hunter applies by rule
(this span is the ledger, never touch it), stated where the hunting
happens, with a test that fires it — a guard is trusted only once it has
been seen to catch (GP-6). What does not count is **incidental**
protection: an execution order that happens to write the ledger after the
sweep, a file the glob happens to miss, a format the regex happens not to
match. Incidental protection is real protection today and gone after the
next refactor, and it fails silently — the ledger doesn't complain when
eaten; it just stops being true, and everything derived from it (an alias
map, a resolution table) degrades into self-reference.

The test, when building anything that hunts a pattern: *does this system
keep a record of the thing being hunted, and does that record spell the
pattern?* If yes, the mask is part of the hunter's definition — written,
tested, and named in the same breath as the hunt itself.

*v1 · shaped by [ADR-040](../record/decisions.d/ADR-040.md) · **Proposed** · origin: The DP→GP migration's first live day: three subsystems — the migration sweep, the fixer's modernize pass, and the reference scan — each independently attacked the `formerly:` stamps the migration had just written, because the record of an old spelling is spelled exactly like the stale reference each of them hunts*
