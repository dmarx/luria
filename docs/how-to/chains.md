# How to define and publish a chain

A chain derives a longitudinal view from same-scheme relations.

## Minimal chain

Given:

```yaml
schemes:
  RFC:
    references:
      extends:
        scheme: RFC
```

declare:

```yaml
chains:
  lineage:
    scheme: RFC
    relation: extends
    output: docs/lineage.md
    title: RFC lineage
```

Then:

```console
$ luria index
```

## Multiple spine relations

Use a list when several different relations advance the same line:

```yaml
relation:
  - extends
  - corrects
```

This preserves semantic sign in source while composing both into one sequence.

## Sibling/rival relation

```yaml
sibling: compared_against
```

Use this for an edge that belongs in the lineage view but does not mean “next step.”

## Facets

```yaml
facet_by:
  - status
  - consensus
```

Every named facet must be a field the scheme actually declares.

Use facets for axes that change how a reader interprets each step.

## Invariant

```yaml
invariant: tags
```

A chain invariant asserts shared structure across the line.

When it fails, investigate:

1. Is the edge wrong?
2. Is the record metadata wrong?
3. Is the invariant too strong?
4. Is the vocabulary missing the concept the line shares?

## Constraints

A chain:

- names an existing scheme,
- walks declared reference fields,
- stays within that scheme,
- requires an output,
- names only declared facet/invariant fields.

Cross-scheme shared-field constraints belong on the reference invariant, not on a chain.

## Publishing

Chain output is generated.

Treat it exactly like other projections:

```text
source relations
      ↓
chain renderer
      ↓
published line
```

Do not hand-edit lineage facts into the output page.
