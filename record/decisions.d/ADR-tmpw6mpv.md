---
status: Proposed
title: 'A whole-field derivation holds what its source holds'
version: 1
tags:
- config
- contract
date: '2026-09-16'
issue: '#276'
summary: >-
  `derive = "{tags}"` off a plural source derives a plural field. `many` says
  so and is checked against the source's scheme rather than inferred, because
  a followed derivation reads a scheme the loader has not finished assembling.
  Both directions of disagreement are refused eagerly — the one that was
  possible before was silent, emptying every tag page of the scheme with
  nothing failing. Rejected: inferring `many` from the template, and leaving
  the blanket refusal in place.
---

# ADR-tmpw6mpv: A whole-field derivation holds what its source holds

## Context

`derive` refused `many` on any field, with a message that was true of the
shape it was written for and false of another:

    `derive = "{tags}"` reads one value off a list, so the field holds one
    — drop `many`

`{tags[0]}` does read one value off a list. `{tags}` does not: `render()`
returns the value itself for a lone field, so the derived field resolves to
the source's whole list. The declaration said one and the value was many.

Nothing caught that, and the way it failed is the reason this is a decision
rather than a patch. `contract.values_of` reads a list on a scalar field as
`None` — "the shape contradicts the declaration" — and `effective_values`
passes the `None` through, so `vocabularies._listing` saw no values on any
document. A consumer that moved a scheme's `tags` onto a derivation lost
**every tag page of that scheme**: fourteen files, no longer written, no
failure, nothing in the lint. A directory that empties is [DP-15](../principles.d/DP-015.md)'s failure
exactly — nothing looks like current.

## Decision

**A template that is one whole field — no index, no attribute, no format
spec — holds what its source holds.** `derive.whole_field()` is that test:
`{tags}` yes, `{tags[0]}` no, `{published:.4}` no, `about {tags}` no.

`many` is **declared and checked**, not inferred:

    schemes:
      NOTE:
        fields:
          tags:
            derive: '{tags}'
            from: paper
            many: true

Two refusals, both eager, both naming the scheme the source lives on:

- the source holds a list and `many` is missing — *"so `tags` holds a list
  too — declare `many`"*, with what goes wrong if it does not;
- `many` is declared and the source holds one value — *"drop `many`"*.

The old blanket refusal survives for the shapes that genuinely render one
value, with a message that now says which shapes those are.

## Alternatives considered

- **Infer `many` from the template and the source, declaring nothing.** This
  is what `derive`'s own docstring argues for — *"the rule is the template's
  shape rather than a flag, so nothing has to be declared twice"* — and it is
  the right instinct for a same-document derivation, where the source's
  cardinality is known when the field is compiled. It loses on the case that
  motivated this: `from: paper` reads a field on **another scheme**, and
  `_fields` runs while that scheme may not exist yet. Inferring would mean
  either rebuilding compiled fields after the load loop, or resolving
  cardinality lazily at every read. Declaring it costs one line and makes
  both mistakes findings rather than one of them a silence.
- **Keep refusing `many` outright and teach `values_of` to tolerate a list on
  a scalar derived field.** Moves the contradiction from the config into the
  reader, where it becomes "a scalar field that is sometimes a list" — and
  `values_of` returning `None` for that shape is a deliberate guard against
  exactly the stringify-and-read-the-first-element behaviour [#141](https://github.com/dmarx/luria/issues/141) removed.
- **Status quo.** A derivation cannot carry a list, so a scheme whose axis is
  derived silently has no tag pages. The silence is the problem; a refusal
  would at least have said so.

## Consequences

`plural_fields(scheme)` is now one function rather than the same three-table
union written out in `_check_derivations`, and `_check_target_fields` takes
what the near scheme declared so it can compare against the far one.

Fired once on a real case before being trusted, as the working agreement
asks. In `anthology-of-the-sota`, moving `NOTE.tags` onto
`derive: '{tags}' from: paper`:

- without `many`, `luria index` deletes all fourteen `docs/notes/tags/*.md`
  and reports nothing — the failure this decision is about, reproduced;
- with `many`, twelve pages are written and two disappear for a real reason
  (no note carries `inference-optimization` or `model-stability` any more,
  because the notes that did were disagreeing with their papers);
- with `many` dropped from the config, the load now refuses and names the
  field, the source, its scheme and the consequence.

Left open: the same silence is reachable by any other route to a list on a
scalar field, and `values_of` still answers `None` without saying so. A
finding for a document whose written value contradicts its declared shape
would close that, and is not this change.
