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

These citations are dependency edges.

If the ADR becomes inactive, dependent prose should become reviewable.

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

That would create hand-maintained projections of the design record, the exact failure [DP-3](../../record/principles.d/DP-003.md) warns about ([DP-3](../../record/principles.d/DP-003.md)).

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

## 6. Generated reference should stay generated where practical

CLI signatures, finding-class inventories, and config-schema details are especially vulnerable to drift.

Prefer generated reference over duplicated hand-maintained lists.

## 7. Documentation changes lint cleanly

Before merging documentation:

```console
$ luria lint
```

and regenerate projections where the project workflow says they are written.

The documentation is dogfood: if its governing citation changes and nothing surfaces, either the dependency was not represented or the mechanism is not doing what the docs claim.
