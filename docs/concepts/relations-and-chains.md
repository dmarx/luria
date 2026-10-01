# Concept: Relations and chains

Relations and chains are two levels of structure:

```text
relation = a local semantic edge, stated by an author
chain    = a declared longitudinal interpretation of those edges, derived by Luria
```

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

A relation can also declare whether it is required, its cardinality, a converse, and an invariant. The keys and their defaults are in [Configuration](../configuration.md); [Model and add relations](../how-to/relations.md) walks through them, including the one that surprises people — a declared reference is required unless it says otherwise.

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

If `extends` and `extended_by` are declared as converses, the reverse edge is not a guess. It is the same relation read from the other endpoint ([ADR-084](../../record/decisions.d/ADR-084.md)).

```yaml
references:
  extends:          {scheme: RFC, many: true, converse: extended_by, required: false}
  extended_by:      {scheme: RFC, many: true, converse: extends, required: false}
  compared_against: {scheme: RFC, many: true, converse: compared_against, required: false}
```

A symmetric relation such as `compared_against` names itself as its converse.

Because the two fields are one relation, the converse belongs to the scheme whose codes the field holds — for a relation that crosses schemes, the target scheme ([ADR-097](../../record/decisions.d/ADR-097.md)). And because either side can be derived from the other, a document holding only one side is a mechanical gap, not a judgement call: the lint reports it and `luria link --fix` fills it. The rules a pair must satisfy are in [Model and add relations](../how-to/relations.md).

## Relation invariants

A reference can assert that both endpoints share a declared field value.

For example:

```yaml
extends:
  scheme: RFC
  invariant: tags
```

means the relation claims some shared subject vocabulary.

Relation invariants can cross schemes if both ends declare the invariant field ([ADR-106](../../record/decisions.d/ADR-106.md)).

An edge whose two ends share no value of the field is reported as `unbound-relations`: either a true value is missing from one end, or the edge is wrong.

## A relation is held twice: as data and as prose

Frontmatter says *that* a relation holds: `extends: [RFC-007]`. Only the
body can say *what* it amounts to, which part of `RFC-007` this one carries
on and what it changes. Both are the record's, and Luria keeps them from
drifting apart in both directions:

- **Up, from prose to frontmatter.** A relation stated where it is
  justified, with a `ref::` directive or the `[[extends::RFC-007]]`
  shorthand, belongs in the frontmatter too. A stated relation the
  frontmatter lacks is `unrecorded-relations`, and `luria link --fix`
  writes it, because the statement already says exactly what to write.
- **Down, from frontmatter to prose.** A reference declared `explain:` asks
  that the body account for every code the field holds. A code the body
  never explains is `unexplained-relations`, and nothing writes the
  explanation for you, because it is prose only a person can write.

What counts as an explanation is deliberately weak: a citation of the code
in the body, outside a reference entry ([ADR-123](../../record/decisions.d/ADR-123.md)). A bibliography line,
`Kingma et al. (2014), LIT-001 — ARXIV-1412.6980.`, names the work and says
nothing about it, so it does not count. That holds wherever the line sits,
because entries are recognised by their shape rather than by a heading. The
check can tell whether the body mentions the code. It cannot tell whether
the sentence says anything, and a sentence written to clear the finding
passes it and defeats it.

So treat an unexplained relation as a question about the relation, not only
about the prose. When reading the cited work turns up nothing to write
(the source never makes the claim, the comparison was never run, the
origin is older), the relation is what is wrong. Correct it rather than
writing a sentence for it. The [how-to](../how-to/relations.md#7-state-the-relation-where-you-explain-it) has
the syntax and the two strengths.

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

The chain does not erase that meaning, because it never owns it: the relations are unioned into one spine before the walk, so the chain page shows the order of the line, not which relation joined each step. The sign of each step stays in the fields of the documents it joins, where a reader of either document finds it.

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

This is a stronger claim than a relation invariant ([ADR-106](../../record/decisions.d/ADR-106.md)). A relation invariant is about each edge; a chain invariant is about the whole line — every member of a connected line holding one value in common. A line that shares nothing is reported as `unbound-lines`, a weaker signal than `unbound-relations`, since each step may share something with its neighbour while nothing runs the whole length. Read the line whole before acting on it.

Declaring `invariant` on a chain also shapes its page: the lines are grouped under each value they share, and the lines that share none get a section of their own ([ADR-113](../../record/decisions.d/ADR-113.md)).

A failure does not automatically mean “bad edge.”

It may indicate:

- an incorrect relation,
- incorrect metadata,
- an invariant too strong for the intended line,
- or an ontology that lacks the concept binding the lineage.

This is one of the places where a finding can be evidence about the ontology itself, not only about the documents.

## Chains are projections

The source truth remains the local relations.

```text
source edges
    ↓
chain derivation
    ↓
generated sequence
```

Do not hand-maintain the lineage in parallel. [DP-3](../../record/principles.d/DP-003.md) applies directly: derive the projection from the authoritative source.

> **Authors state the edges. Luria derives the line.**
