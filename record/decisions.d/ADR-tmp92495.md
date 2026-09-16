---
status: Active
title: 'A field the project declares unique, checked across the scheme'
version: 1
tags:
- config
- contract
date: '2026-09-16'
issue: '#165'
summary: >-
  `unique: true` on a plain field, or once on a field group to say it of each
  field in it, and a lint violation when two documents hold one value. Every
  other check asks whether a pointer resolves; this asks the converse, whether
  two documents resolve to the same place, and nothing did. A duplicate
  retired naming its survivor is the resolution and not the finding, so the
  check clears on the pointer rather than on a status. Rejected: a bespoke
  `duplicate-source` finding, a warning class, pooling a group's values across
  its fields, and waiting on an alternative backend.
---

# ADR-tmp92495: A field the project declares unique, checked across the scheme

## Context

Repairing citations in a consumer, a note's `arxiv:` was corrected from an
identifier belonging to an unrelated paper to the right one. That identifier
was one another note had been carrying, correctly, the whole time. The record
then held two documents for one paper — two titles, two authors, two
statuses, two readings, two curation judgements — and `luria lint` printed
`docs lint clean`.

It is worth being exact about why nothing caught it. The lint's vocabulary is
about references: `retired-citations`, `unresolved-codes`, `broken-targets`,
`remote-drift`. Every one of them asks *does this pointer resolve?* and every
pointer here resolved. The question nobody asked is the converse — *do two
documents resolve to the same place?* `remote-drift` comes closest, since it
already reads `arxiv:` and `doi:` through the remotes, but it checks a
document against a remote and never documents against each other.

The shape of the failure matters more than the instance. **A citation repair
is the operation that creates this defect**, because a wrong identifier is by
construction the thing keeping two notes apart; correcting it is what
collides them. A record doing the repair pass that [ADR-009](ADR-009.md) makes
possible is walking into this with no guard at all, and a record large enough
to need the pass is too large to check by hand.

That consumer found out three separate times. Three of its notes stop, in
their own bodies, to say that two documents could name one paper with the
build green throughout, and all three name [#165](https://github.com/dmarx/luria/issues/165). A fact a record writes
down three times in three places is one the tooling should be asserting.

## Decision

A field declares itself unique, and the lint checks it across the scheme:

    schemes:
      LIT:
        fields:
          arxiv: {unique: true}

        field_groups:
          source:
            fields: [arxiv, doi, url]
            require: at-least-one
            unique: true          # says it of each field in the group

Four things about that are load-bearing.

**Nothing is checked until something says `unique`**, for the reason
`invariant` is opt-in ([ADR-106](ADR-106.md)). [DP-010](../principles.d/DP-010.md) says a check defaults ON and
turning it off is a sited act, so this owes an answer, and the answer is that
the thing being defaulted is not the check but *which field identifies* —
which Luria cannot infer. Over every field, uniqueness would report a
`status` collision for every document in the corpus and a `date` collision
for most: not a guard somebody switched off, a guard with no target.
[DP-010](../principles.d/DP-010.md)'s own test is what the silent default costs and who pays it, and the
honest accounting is in *Alternatives* below — there is a shape that defaults
ON, and it is deferred rather than dismissed.

**`unique` types the field.** A table carrying nothing but `unique: true` is
a complete declaration, the same way `many: true` alone is: `many` says the
field holds a list, `unique` says its values identify. Declaring it over a
field drawn from a closed vocabulary is *refused at load* rather than
checked, because a vocabulary exists to be shared — `unique` over one caps
the scheme at one document per term, which nobody means, and a refusal says
so where a violation would leave the author guessing.

**A group says it once, and says it of each field separately.** The group is
sugar, deliberately: an `arxiv` and a `doi` that happen to be the same string
do not collide, because they are different namespaces and a match between
them is a coincidence. Recognising one paper under two *kinds* of identifier
is normalisation — the same class of feature as fuzzy title matching, which
[#165](https://github.com/dmarx/luria/issues/165) separates out and does not ask for.

**A violation, not a warning.** The line is where the finding comes from. The
warning classes are what Luria notices on its own, and they are warnings
because Luria might be wrong about what the record meant — citing a `Rejected`
decision is frequently correct. This is a constraint the *project* declared:
it said no two documents hold this value, and two do. There is nothing for
Luria to be tactful about. It is the same call `check_alias_collisions`
already makes for a rendered spelling, and for the same reason.

### The retirement is the resolution

The one subtlety, and the thing that decides whether this check is usable at
all. **Retire by changing status, never by deleting**: a duplicate that has
been dealt with correctly is still *there*, keeping its body and — this is
the point — keeping its identifier. A naive uniqueness check fires on every
pair a record has already answered, which would make the answer look like the
defect and force a directive onto work that is already complete and already
explained.

So the check clears on the **pointer**, not on a status: a document is
dropped from the group when it names a fellow holder in the field the scheme
already uses for succession (`successor`, [ADR-085](ADR-085.md) — `superseded_by:` by
default). If what remains is fewer than two documents, there is no finding.

Status is deliberately not consulted. In the consumer's third pair both
documents are `Rejected` — the survivor for its own unrelated reasons — and a
rule reading "exactly one live document per value" would report a pair whose
resolution is written into both bodies. What resolves a duplicate is that one
note *points at the other*, and that is what is read.

The negative gives the rule its edge: being retired does not excuse a
collision. A document retired naming something else is still a holder.

### What counts as one value

Compared case-folded and stripped. A DOI is case-insensitive by
specification, and a trailing space is nobody's intent; treating either as a
distinct identifier would let the duplicate through, which is the whole
failure. The report quotes the value **as written** — every distinct spelling
that matched, so a reader seeing two of them knows the comparison folded
something rather than wondering why the check fired. A folded value in a
report is a spelling nobody wrote and nobody can grep for.

## Alternatives considered

- **A bespoke `duplicate-source` finding**, which is what [#165](https://github.com/dmarx/luria/issues/165) originally
  proposed: group a scheme's documents by their resolved source and report
  any group with more than one member. It would have caught the case. It
  loses because it names the consumer's vocabulary in Luria's code — `source`
  is a field group one record happens to declare, and Luria ships one scheme
  on purpose ([ADR-006](ADR-006.md)). A record whose unique field is an ISBN, an internal
  ticket id or a URL slug gets nothing from a check spelled `source`. The
  generic constraint is the same amount of code and answers all of them.
- **A warning class with a `duplicate-source-ok:` directive**, also from
  [#165](https://github.com/dmarx/luria/issues/165), on the grounds that there is a real deliberate case. There is,
  and the deliberate case turned out to have a better answer than a
  directive: the pair is resolved by retiring one into the other, which the
  record wants to do anyway and which this check reads. Every deliberate
  duplicate in the consumer's corpus clears with **zero directives** — three
  acknowledgements that would have restated, in a comment, a retirement
  already written into two document bodies and one `superseded_by:` field.
- **Pooling a group's values across its fields**, so an `arxiv` and a `doi`
  holding one string collide. It sounds stricter and is mostly noise: the
  collision it adds is a coincidence between namespaces, and the collision it
  suggests it will catch — one paper filed once by arXiv id and once by DOI —
  it does not, because those are different strings. Wanting that is wanting
  normalisation, and half of it is worse than none.
- **Defaulting ON for fields a remote resolves.** The shape [DP-010](../principles.d/DP-010.md) asks
  for, and it exists: `remote-drift` already reads `arxiv:` and `doi:`
  through the declared remotes, so Luria *does* know which fields hold
  resolvable identifiers without being told. Uniqueness over exactly those
  would have caught [#165](https://github.com/dmarx/luria/issues/165)'s case with no config line at all. Deferred, not
  dismissed: it changes what a green build means for every existing record on
  upgrade, and a record that has carried a duplicate for a year would find
  out by a broken build it did not ask for. [#165](https://github.com/dmarx/luria/issues/165) asked for a declared
  constraint; shipping the declaration first gives records a way to opt in
  and gives this project the evidence to decide whether the default should
  follow. It is the obvious next decision.
- **Waiting on an alternative backend** ([#110](https://github.com/dmarx/luria/issues/110)), on the worry that
  constraints are how a record turns into a bespoke database. The worry is
  right about queries and wrong about this: a uniqueness constraint is one
  declared assertion checked by one pass over documents Luria already reads
  for every other check, and it needs no index, no query language and no
  storage. A database is what you reach for when you want to *ask*
  arbitrary questions; this is the record *stating* one. `unique` is also
  precisely the constraint a backend would need declared before it could
  enforce anything, so this is a prerequisite rather than a detour.
- **A guard inside `luria repair`** instead of the lint — refuse to write an
  identifier another document holds. Worth having eventually and not
  sufficient: it catches only the collisions Luria itself writes, and every
  one of the consumer's three arrived through a human edit. The check has to
  be over the corpus, not over the write.
- **Status quo.** The cost is measurable and was paid: three duplicate pairs,
  found by grep, one of them carrying a conflated reading into a practice that
  had to be split. The pairs are invisible for as long as nobody happens to
  grep, and the repair pass that creates them is a normal thing for a record
  to need.

## Consequences

A record can now assert that a field identifies, and find out when it stops
being true. Declaring it is one key; the consumer's `source` group took one
line and reported nothing, because its three known duplicates were already
resolved correctly — which is the outcome that makes the check trustworthy
rather than the outcome that makes it look useless.

Fired before trusting ([DP-006](../principles.d/DP-006.md)), on the corpus rather than on a fixture:
removing the `superseded_by:` pointer from one of those three retired notes,
leaving its `Rejected` status untouched, makes the check name that exact pair
—

    luria.yaml: schemes.LIT.field_groups.source declares `arxiv` unique, and
    `2302.06675` is held by LIT-090, LIT-105 — one value cannot identify 2
    documents; retire all but one, naming the survivor in `superseded_by:`

— and restoring the pointer clears it. A check that reports nothing on a
corpus is indistinguishable from a check that cannot report ([DP-015](../principles.d/DP-015.md)), and
this one reports nothing on that corpus by design, so the sabotage run is
the only thing separating the two.

`luria merge OLD NEW`, the other half of [#165](https://github.com/dmarx/luria/issues/165), is not in this decision and
is now the obvious follow-up: the finding says a duplicate exists, and
resolving one by hand is the mechanical multi-file edit the CLI exists to do.
Its parts are all written already — `concretize` rewrites every reference and
records the old spelling in `formerly:`, `aliases` resolves those, and
`repair` moves a document into `status_note:`/`successor`.

What this obliges: the skip rule reads `successor`, so a scheme that renames
that field ([ADR-085](ADR-085.md)) gets the new name for free, and a scheme that resolves
duplicates some other way gets no skip and will need directives. That is the
right default — succession is how this record retires things — but it is an
assumption rather than a law, and a project that trips over it is the signal
to generalise.
