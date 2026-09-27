# Concept: Vocabularies and independent dimensions

A Luria vocabulary gives a field a declared language.

That language can serve several roles at once.

## 1. Classification

A vocabulary is declared once, at the top of `luria.yaml`, and a scheme's field names it (ADR-076, ADR-098):

```yaml
vocabularies:
  area:
    runtime: {}
    storage: {}
    security: {}

schemes:
  RFC:
    fields:
      area:
        vocabulary: area
        many: true       # a list of values; default false, one value
        required: true   # default false; required + many means non-empty
```

Declaring the vocabulary centrally is what lets two schemes share one list without the lists drifting apart. A record can then classify itself using terms whose meaning is shared across the corpus.

## 2. Constraint

A vocabulary is closed by default: a value it does not list is a lint violation. `closed: false` on the field opens it — the declared values still carry their labels and pages, and other values are accepted unchecked.

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

Each value of a vocabulary-backed field gets a page in its scheme's generated index, and a chain can show vocabulary fields beside each step of a line (`facet_by`; see [Relations and chains](relations-and-chains.md#facets)).

A scheme's `axis` key is a narrower, real setting: it names the one field whose values head that scheme's index — `tags` in Luria's own record.

Status is a vocabulary like any other (ADR-085). A scheme names its status vocabulary under `fields.status.vocabulary`, and its `active:` key names the one word that means in force.

For example:

```text
status     = what this record currently endorses
consensus  = what the broader field appears to believe
```

Those dimensions may vary independently.

A recommendation can be:

```text
status: Active
consensus: contested
```

without contradiction.

## Keep independent questions independent

Ask:

> Can these values change independently without inconsistency?

If yes, they may deserve separate fields, each with its own vocabulary.

Common examples:

- proposal standing,
- review state,
- implementation progress,
- confidence,
- consensus,
- evidence relevance.

Do not overload one `status` field simply because all of the answers sound like “state.”

## Groups and cardinality

Values of one field can form constrained groups when the record needs a single answer rather than a pile of labels. A group is declared under the field it constrains, with one `require` rule:

```text
any            (the default — the group is a label)
at-most-one
exactly-one
```

A group can also list `excluded_by` values: values of the same field that rule the whole group out. Saying an argument is `sound` contradicts naming how it fails:

```yaml
fields:
  verdict:
    vocabulary: verdict
    many: true
    groups:
      failure-mode:
        tags: [circular, unfalsifiable]
        require: at-most-one
        excluded_by: [sound]
```

These constraints make the ontology executable without pretending every semantic distinction is boolean.

## Field groups

Several alternative fields can collectively satisfy one requirement (ADR-074).

For example, a literature record might need **a source**, satisfied by at least one of:

```yaml
field_groups:
  source:
    fields: [arxiv, doi, url]
    require: at-least-one     # or exactly-one, at-most-one
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

A chain's `invariant` says every member of a line holds one value of that field in common. A line that shares nothing is reported as `unbound-lines`, and the chain page is grouped by the invariant's values, with the lines that share none in a section of their own (ADR-113). This is distinct from an `invariant` on a relation, which asserts only that the two ends of each edge share a value, and is reported as `unbound-relations` (ADR-106).

This makes vocabulary design part of longitudinal interpretation.

An invariant failure can even reveal that the vocabulary lacks a shared concept the line needs.

That is not merely validation. It is ontology feedback.
