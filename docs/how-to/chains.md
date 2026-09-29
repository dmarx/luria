# How to define and publish a chain

A chain derives a longitudinal view from same-scheme relations.

## Minimal chain

Given an `RFC` scheme (for example from `luria init --schemes RFC`) whose table in `luria.yaml` declares the relation:

```yaml
schemes:
  RFC:
    # dir, output, fields … as scaffolded
    references:
      extends:
        scheme: RFC
        required: false
```

A reference field is required unless it says otherwise, and the first RFC in a line extends nothing — without `required: false` every root is a violation.

declare:

```yaml
chains:
  lineage:
    scheme: RFC
    relation: extends
    output: docs/lineage.md
    title: RFC lineage
```

`docs/lineage.md` is a new page in `docs/`, and every page there must be listed in the docs index, so add a line for it to `docs/README.md`:

```markdown
- [RFC lineage](lineage.md) — each line of RFCs that extend one another.
```

Then file entries that relate, and render:

```console
$ luria new rfc --title "Base" --tags record
record/rfcs.d/RFC-001.md
$ luria new rfc --title "Next" --tags record --extends RFC-001
record/rfcs.d/RFC-002.md
$ luria index
$ luria lint
```

The chain machinery is described in [ADR-083](../../record/decisions.d/ADR-083.md).

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

A chain invariant asserts shared structure across the line ([ADR-106](../../record/decisions.d/ADR-106.md)). When an
invariant is declared, the generated chain page is also organized by the
values that bind each line, with unbound lines called out separately
([ADR-113](../../record/decisions.d/ADR-113.md)).

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

Cross-scheme shared-field constraints belong on the reference invariant, not on a chain ([ADR-106](../../record/decisions.d/ADR-106.md)).

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
