# Tutorial: Build a lineage with chains

A relation answers a local question:

```text
What does this record point to?
```

A chain answers a longitudinal one:

```text
What line of development is this record a step in?
```

Chains walk one or more same-scheme relations transitively and render the resulting sequences as generated views. They can add a sibling/rival relation, carry declared fields as facets, and assert a shared invariant across a line.

This tutorial uses a small RFC lineage, but the same mechanism can represent research lineages, evolving practices, standards families, policy histories, or explanatory theories.

## 1. Start with a scheme that can relate to itself

Assume an RFC scheme with standing and an area vocabulary:

```yaml
vocabularies:
  rfc-status:
    Proposed: {}
    Accepted: {}
    Superseded: {}
    Rejected: {}

  area:
    runtime: {}
    storage: {}
    security: {}

schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Accepted

    references:
      extends:
        scheme: RFC
        required: false
        many: false
      corrects:
        scheme: RFC
        required: false
        many: false
      compared_against:
        scheme: RFC
        required: false
        many: true

    fields:
      status:
        vocabulary: rfc-status
      tags:
        vocabulary: area
        many: true
        required: true
        closed: true
```

All three references stay within the `RFC` scheme. That matters because a chain is a sequence within one scheme. Cross-scheme invariants belong on relations instead.

## 2. Scaffold and create entries normally

```console
$ luria init
$ luria new RFC --title "Durable jobs with acknowledgements"
$ luria new RFC --title "Renewable leases for durable jobs"
$ luria new RFC --title "Lease recovery without global polling"
```

Fill the records' status and tags normally.

## 3. Add semantic edges

Use the relation-authoring workflow rather than inventing a second lineage document.

For example:

```text
RFC-002 extends RFC-001
RFC-003 corrects RFC-002
```

`luria relate` is the CLI surface for writing declared relations into frontmatter. Check its current help for exact argument syntax:

```console
$ luria relate --help
```

The important result is local source truth:

```yaml
# RFC-002
extends: RFC-001
```

```yaml
# RFC-003
corrects: RFC-002
```

Authors state the edges. The chain will derive the line.

## 4. Declare the chain

Add:

```yaml
chains:
  durable-jobs:
    scheme: RFC
    relation:
      - extends
      - corrects
    sibling: compared_against
    output: docs/durable-jobs-lineage.md
    title: Durable jobs lineage
```

`relation` can name one field or several. Several relations are walked as one spine while preserving the sign of the transition in the source record: “builds on” and “corrects” can both advance one historical line without being flattened into the same semantic edge.

The `sibling` relation belongs to the line without advancing it.

## 5. Generate the view

```console
$ luria index
```

The chain page is generated from declared edges:

```text
RFC-001
   ↓ extends
RFC-002
   ↓ corrects
RFC-003
```

Do not hand-maintain that sequence elsewhere. The chain exists specifically to avoid a second prose lineage drifting from the source relations. That is DP-3's source/projection principle applied to history ([DP-3](../../record/principles.d/DP-003.md)).

## 6. Add vocabulary-backed facets

A chain is more useful when each step carries the axes needed to interpret it.

By default, `status` is the natural first facet. You can declare additional fields:

```yaml
chains:
  durable-jobs:
    scheme: RFC
    relation:
      - extends
      - corrects
    sibling: compared_against
    facet_by:
      - status
      - consensus
    output: docs/durable-jobs-lineage.md
    title: Durable jobs lineage
```

This assumes `consensus` is a declared field on the scheme, usually vocabulary-backed.

The distinction matters. A chain may contain:

```text
RFC-001   Accepted     converged
RFC-002   Accepted     contested
RFC-003   Proposed     emerging
```

The sequence is the same graph either way, but the interpretation is not.

Vocabularies therefore serve at least three roles:

1. classify records,
2. constrain admissible values,
3. facet higher-order views.

See [Vocabularies and epistemic axes](../concepts/vocabularies.md).

## 7. Add a chain invariant

Suppose every step in this lineage should share at least one `tags` value.

Declare:

```yaml
chains:
  durable-jobs:
    scheme: RFC
    relation:
      - extends
      - corrects
    invariant: tags
    output: docs/durable-jobs-lineage.md
```

Now the line itself asserts something:

> These records are not merely connected; they are steps in one subject lineage.

If a step shares no tag with the line, Luria can surface that as a finding.

## 8. Treat an invariant failure as diagnosis, not a verdict

Suppose:

```text
RFC-001 tags: [runtime]
RFC-002 tags: [runtime]
RFC-003 tags: [security]
```

but `RFC-003 corrects RFC-002`.

An invariant finding can mean several different things:

- the relation is wrong,
- the metadata is wrong,
- the line genuinely crosses subjects and the invariant is too strong,
- the vocabulary lacks a concept that all three records actually share.

The last possibility is important.

A linter normally sounds like it validates instances against a fixed ontology. A chain can instead reveal pressure on the ontology itself.

If the real shared concept is `job-lifecycle`, adding that vocabulary term may be the correct repair.

## 9. Add a sibling or rival branch

Suppose another RFC proposes an incompatible approach:

```text
RFC-004 compared_against RFC-002
```

A sibling relation allows the generated view to show that comparison without pretending `RFC-004` is the next successor.

This distinction keeps the graph semantically honest:

```text
succession ≠ rivalry
```

## 10. Understand the validation boundary

Luria validates chain declarations eagerly because a broken chain often renders *nothing*, and an empty generated page can look exactly like a correct empty result.

The configuration therefore requires:

- a declared scheme,
- declared reference fields for spine/sibling relations,
- same-scheme targets for chain-walked relations,
- declared facet fields,
- a declared invariant field,
- an output path.

This is an application of DP-15's concern with silent non-events: “nothing happened” should not be indistinguishable from “everything worked.”

## 11. Publish the chain

A chain's output is a generated projection and participates in the publishing surface like other views.

A published chain is especially useful because it answers questions that per-document pages cannot:

- Where did this line start?
- Which step corrected which predecessor?
- Where did a rival branch appear?
- Which parts are active, contested, or provisional?
- What subject invariant binds the line?

When site publishing is enabled, chain pages become longitudinal navigation over the same source relations already visible locally.

## What you learned

A relation stores a local semantic edge.

A chain derives a line from those edges:

```text
local relations
      ↓
transitive walk
      ↓
faceted sequence
      ↓
published view
```

The chain owns no independent lineage facts.

That asymmetry is the point.

> **Authors state the edges. Luria derives the line.**
