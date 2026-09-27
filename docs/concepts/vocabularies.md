# Concept: Vocabularies and epistemic axes

A Luria vocabulary gives a field a declared language.

That language can serve several roles at once.

## 1. Classification

```yaml
vocabularies:
  area:
    runtime: {}
    storage: {}
    security: {}
```

A record can classify itself using terms whose meaning is shared across the corpus.

## 2. Constraint

A closed vocabulary turns misspellings and undeclared categories into visible findings rather than silently creating new concepts.

```text
runtme
```

can be caught instead of becoming a new accidental category.

But a closed vocabulary does **not** mean the ontology is infallible.

If a legitimate record fits none of the declared terms, the right repair may be:

```text
change the vocabulary
```

rather than:

```text
force reality into the least-wrong category
```

## 3. Interpretation

Vocabulary-backed fields can be rendered as facets in chains, indexes, reports, or sites.

For example:

```text
status     = what this record currently endorses
consensus  = what the broader field appears to believe
```

Those axes may vary independently.

A recommendation can be:

```text
status: Active
consensus: contested
```

without contradiction.

## Keep independent questions independent

Ask:

> Can these values change independently without inconsistency?

If yes, they may deserve separate axes.

Common examples:

- proposal standing,
- review state,
- implementation progress,
- confidence,
- consensus,
- evidence relevance.

Do not overload one `status` field simply because all of the answers sound like “state.”

## Groups and cardinality

Vocabulary terms can form constrained groups when the record needs an axis rather than a pile of labels.

Examples:

```text
exactly one
at most one
any
```

A group can also exclude another group.

These constraints make the ontology executable without pretending every semantic distinction is boolean.

## Field groups

Several alternative fields can collectively satisfy one requirement.

For example, a literature record might need **a source**, satisfied by at least one of:

```text
arxiv
doi
url
```

The semantic requirement is “has a citable source,” not “must have all three identifiers.”

## Vocabularies and chains

Chains reveal a particularly useful role for vocabularies.

A lineage can carry:

```yaml
facet_by:
  - status
  - consensus
```

and assert:

```yaml
invariant: tags
```

This makes vocabulary design part of longitudinal interpretation.

An invariant failure can even reveal that the vocabulary lacks a shared concept the line needs.

That is not merely validation. It is ontology feedback.
