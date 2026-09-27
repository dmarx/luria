# Contributing: Documenting Luria

Luria's documentation is part of the governed record it describes.

That implies a few authoring rules.

## 1. Separate four kinds of truth

A documentation claim should be identifiable as one of:

1. **current implementation contract** — belongs in reference,
2. **governing design choice** — cite an ADR,
3. **standing design principle** — cite a DP,
4. **illustrative modeling advice** — label it as an example, not a requirement.

Do not blur these categories.

## 2. Behavioral prose cites its governing record

Examples:

```text
"luria init plans the scaffold from configuration"
    → ADR-048
```

```text
"luria new derives kinds from configuration"
    → ADR-036
```

```text
"changed choice ≠ corrected rationale"
    → ADR-019
```

```text
"warnings can be promoted to enforcement"
    → ADR-035
```

In a page, write the bare code — [ADR-048](../../record/decisions.d/ADR-048.md) — and run `luria link --fix`; never hand-write the link target. Prose renders into views in other directories, so only the fixer knows the frame a target must resolve from. (The examples above sit in `text` fences, which mask codes: they illustrate the pattern and create no edges. A code in backticks is a mention, not a citation, for the same reason.)

These citations are dependency edges. When the cited ADR stops being in force, `luria lint` reports the citing page under `retired-citations`, so the prose becomes reviewable without anyone having edited it.

## 3. Do not duplicate rationale

Use this division:

```text
Tutorial   = how to learn the workflow
How-to     = how to accomplish a task
Concept    = how to understand the model
Reference  = exact current behavior
ADR / DP   = why the design exists
```

Do not copy an ADR's alternatives/rationale into every page that uses the behavior.

That would create hand-maintained projections of the design record, the exact failure [DP-3](../../record/principles.d/DP-003.md) warns about.

## 4. Normative language is earned

Use **must** when:

- the implementation actually enforces the property, or
- an explicitly cited governing rule makes it normative.

Otherwise prefer:

- can,
- may,
- often,
- consider,
- one useful model.

This matters especially for ontology advice. `RFC → DECISION → IMPLEMENTATION` is an example model, not Luria doctrine.

## 5. Tutorials use supported workflows

Do not teach manual creation of identities, scaffolds, or boilerplate that Luria owns.

Prefer:

```text
luria.yaml
luria init
luria new
luria relate
luria lint
luria repair
luria ack
luria index
```

as appropriate.

## 6. Never edit a generated file

Anything stamped `GENERATED` — [the configuration reference](../configuration.md), [the record](../record.md), the decision index and tag pages, [the design principles](../design-principles.md), the devlog books, the reports, and the README badge and site regions — is rebuilt by `luria index`. Edit the source (for the configuration reference, the dataclasses in `luria/config.py`) and rerun it.

The same goes for new reference material: CLI signatures, finding-class inventories and config-schema details drift fastest, so extend what is generated rather than writing a parallel hand-maintained list.

## 7. Every page is on the map

`luria lint` checks that every page under `docs/` (one directory level deep) is linked from [the docs map](../README.md). A new page — including a chain page or any other generated output you add to `docs/` — gets an entry there in the same change, or the lint fails.

## 8. Tag the decisions the docs depend on

A decision cited by a hand-written page (or by prose that renders into one) carries the `docs` tag, so whoever retires it can see that a page has to change with it. Add the tag in the same change that adds the citation. Nothing checks this yet; it is a convention.

## 9. Documentation changes lint cleanly

Before merging documentation:

```console
$ luria link --fix
$ luria lint
$ python -m pytest tests -q
```

Branches carry no regenerated views: `luria index` runs where merges serialize, in the generation job on the default branch, and `luria index --check` is asked there ([ADR-068](../../record/decisions.d/ADR-068.md)).

The documentation is dogfood: if its governing citation changes and nothing surfaces, either the dependency was not represented or the mechanism is not doing what the docs claim.
