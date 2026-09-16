---
status: Proposed
title: "A vocabulary's alert belongs to the set, like its blurb"
version: 1
tags:
- config
- contract
date: '2026-09-16'
issue: '#281'
summary: >-
  `alert` on a vocabulary moves from the field that names it to the central
  table, beside `label` and `blurb`. The rule it explains is a fact about the
  set, and a record whose three schemes name one vocabulary was otherwise
  writing the same sentence three times. The nested form's key list becomes a
  named constant, because the version that was spelled inline did not know
  about `alert` and refused the first record to use both features together.
---

# ADR-tmp7gsqp: A vocabulary's alert belongs to the set, like its blurb

## Context

Two features shipped in 0.25.0 and had never been used together.

`alert` ([#273](https://github.com/dmarx/luria/issues/273)) is the sentence a vocabulary prints when a closed-set
violation fires — *"closed so every tag is one somebody chose, not because
the list is finished"*. `label` and `blurb` ([#279](https://github.com/dmarx/luria/issues/279)) are what the vocabulary
is at rest, and [#279](https://github.com/dmarx/luria/issues/279) put them in the **central** `vocabularies:` table, on
the argument [ADR-098](ADR-098.md) had already settled: a set two schemes share is declared
once so the copies cannot drift.

`alert` was left on the **field**. That was not a decision; it is where the
`Vocabulary` object happens to be built, and [#273](https://github.com/dmarx/luria/issues/273)'s own docstring says the
opposite — *"attached to the vocabulary rather than the field so it rides the
one rule it describes"*.

The first record to adopt both found it. Writing the alert where the blurb
goes was refused with a message about a value named `values`, because the
nested form's discriminator was spelled inline:

    set(table) <= {"label", "blurb", "values"}

`alert` is not in that set. The message named three keys while the code
allowed three and the dataclass carried four, and the failure it produced
described a completely different fault.

## Decision

**`alert` is read from the central table**, beside `label` and `blurb`. A
vocabulary three schemes name carries one alert.

**`VOCABULARY_KEYS` is a named constant**, and both the discriminator and the
refusal message read it. The message now lists whatever the constant holds
rather than a hand-copied subset of it.

A `TagGroup`'s `alert` stays where it is. A group is declared inline, under
the field whose values it constrains, and there is no central table for it to
move to — the two are not inconsistent, they are different shapes of thing.

## Alternatives considered

- **Add `alert` to the inline key set and leave it on the field.** One
  character of the bug fixed and none of the cause. A vocabulary three
  schemes name would still need the sentence three times, which is the exact
  drift [ADR-098](ADR-098.md) centralised vocabularies to prevent and [#279](https://github.com/dmarx/luria/issues/279) cited when it
  moved `blurb`.
- **Honour both spellings, field-level overriding the set.** Two homes for
  one fact, which is what [ADR-089](ADR-089.md) argues against upstream and what this
  project keeps deciding against. Nothing has released a record using the
  field-level spelling — 0.25.0 is hours old — so there is nothing to keep
  working.
- **Derive the allowed keys from the dataclass** rather than naming a
  constant. Tempting and wrong here: `Vocabulary` also carries `many`,
  `required`, `closed`, `default` and `required_when`, all of which are
  declared per field and genuinely belong there. The set of keys a *table*
  may carry is a different set from the fields the object has, and writing it
  down is the honest way to say so.
- **Status quo.** The composition stays broken, and the message sends the
  next person looking for a value named `values`.

## Consequences

The example in `test_a_closed_vocabulary_can_print_its_own_advice` declares
its alert on the set now, which is also the first exercise of the nested form
outside the tests written for it.

Fired on the real case, as the working agreement asks. `anthology-of-the-sota`
declares `topics` with all three keys; the config loads, one declaration
reaches SOTA, LIT and THEORY, and a bad tag prints:

    record/practices.d/SOTA-001.md: `tags: kv-cache-paging` is not in the
    `topics` vocabulary — the values are training-optimization, …
        ↳ Closed so that every tag is one somebody chose and blurbed, NOT
          because the list is finished. If your document wants a word this
          vocabulary cannot say, add it — …

That is [#273](https://github.com/dmarx/luria/issues/273)'s whole purpose, reaching a real reader for the first time.

Left open: nothing here checks that a vocabulary's `alert` is only meaningful
where some field declares `closed: true`. An alert on an open vocabulary is
inert rather than wrong, and a finding for it would want to know which of the
naming fields is closed — worth a look if anyone writes one.
