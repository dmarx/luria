# Concept: Relations and chains

Relations and chains are two levels of structure.

## Relations are local semantic edges

A field such as:

```yaml
source:
  - LIT-042
```

becomes meaningfully stronger when the scheme declares:

```yaml
references:
  source:
    scheme: LIT
    many: true
```

The declaration allows Luria to check that the value:

1. is present when required,
2. has the shape of a code,
3. belongs to the intended scheme,
4. resolves to a document.

A relation can also declare a converse, cardinality, conditional requirement, label/blurb, and invariant.

The difference between:

```text
mentions
```

and:

```text
supports
implements
extends
corrects
supersedes
motivates
```

is knowledge. Preserve it when it matters.

## Converse relations

If `extends` and `extended_by` are declared as converses, the reverse edge is not a guess. It is the same relation read from the other endpoint.

A symmetric relation such as `compared_against` may name itself as its converse.

## Relation invariants

A reference can assert that both endpoints share a declared field value.

For example:

```yaml
extends:
  scheme: RFC
  invariant: tags
```

means the relation claims some shared subject vocabulary.

Relation invariants can cross schemes if both ends declare the invariant field.

## Chains are longitudinal interpretations

A chain walks one or more same-scheme relations transitively.

```yaml
chains:
  lineage:
    scheme: RFC
    relation:
      - extends
      - corrects
    sibling: compared_against
    output: docs/lineage.md
    title: RFC lineage
```

The spine relations advance the line.

The sibling relation associates a rival or peer without pretending it is the next step.

## Why multiple spine relations matter

Suppose:

```text
A extends B
C corrects A
```

Both relations continue one line, but they carry different signs:

- `extends` — builds on,
- `corrects` — exists because something earlier was wrong.

Flattening both into `parent` would discard meaning.

A chain composes them without erasing their local semantics.

## Facets

A chain can carry declared fields as facets:

```yaml
facet_by:
  - status
  - consensus
```

The line then becomes both structural and interpretive.

```text
A   Active      converged
B   Active      contested
C   Proposed    emerging
```

Vocabularies therefore do more than classify records; they can provide the axes through which a lineage is read.

## Chain invariants

A chain can assert an invariant across its line:

```yaml
invariant: tags
```

A failure does not automatically mean “bad edge.”

It may indicate:

- an incorrect relation,
- incorrect metadata,
- an invariant too strong for the intended line,
- or an ontology that lacks the concept binding the lineage.

This is one of the places where Luria can expose pressure on the ontology itself.

## Chains are projections

The source truth remains the local relations.

```text
source edges
    ↓
chain derivation
    ↓
generated sequence
```

Do not hand-maintain the lineage in parallel. DP-3 applies directly: derive the projection from the authoritative source ([DP-3](../../record/principles.d/DP-003.md)).

> **Authors state the edges. Luria derives the line.**
