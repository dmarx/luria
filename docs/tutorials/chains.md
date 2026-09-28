# Tutorial: Build a lineage with chains

A relation answers a local question:

```text
What does this record point to?
```

A chain answers a longitudinal one:

```text
What line of development is this record a step in?
```

Chains walk one or more same-scheme relations transitively and render the resulting sequences as generated views ([ADR-083](../../record/decisions.d/ADR-083.md)). They can add a sibling/rival relation, carry declared fields as facets, and assert a shared invariant across a line ([ADR-106](../../record/decisions.d/ADR-106.md), [ADR-113](../../record/decisions.d/ADR-113.md)).

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

All three references stay within the `RFC` scheme. That matters because a chain is a sequence within one scheme: a chain whose relation points at another scheme is refused when `luria.yaml` loads, and a cross-scheme invariant belongs on the reference itself (`references.<field>.invariant`, [ADR-106](../../record/decisions.d/ADR-106.md)).

Each reference says `required: false` on purpose. A declared reference is required unless it says otherwise, and the first step of a line has nothing to extend — without it, RFC-001 fails the lint with ``no `extends:` in frontmatter``.

## 2. Scaffold and create entries normally

```console
$ luria init
$ luria new rfc --title "Durable jobs with acknowledgements" --tags runtime
$ luria new rfc --title "Renewable leases for durable jobs" --tags runtime
$ luria new rfc --title "Lease recovery without global polling" --tags runtime
```

The kind is the scheme's prefix in lower case. `--tags runtime` replaces the template's `tags: [record]`, which the closed `area` vocabulary would reject; every entry starts at the template's `status: Proposed`.

## 3. Add semantic edges

Use the relation-authoring workflow rather than inventing a second lineage document.

For example:

```text
RFC-002 extends RFC-001
RFC-003 corrects RFC-002
```

`luria relate SOURCE FIELD TARGET` writes a declared relation into the source's frontmatter:

```console
$ luria relate RFC-002 extends RFC-001
record/rfcs.d/RFC-002.md: extends += RFC-001
$ luria relate RFC-003 corrects RFC-002
record/rfcs.d/RFC-003.md: corrects += RFC-002
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

`relation` can name one field or several. Several relations are unioned into one spine before the walk, so “builds on” and “corrects” both advance one historical line. The chain page does not say which field joined each step; that distinction stays in the source records, where `extends:` and `corrects:` remain different fields.

The `sibling` relation belongs to the line without advancing it.

The output is a page directly in `docs/`, so it must be linked from `docs/README.md` — otherwise `luria lint` fails with `docs/README.md: missing index entry for durable-jobs-lineage.md`. Add a line to the list there:

```markdown
- [Durable jobs lineage](durable-jobs-lineage.md) — the RFC line, generated from `extends:` and `corrects:`.
```

## 5. Generate the view

```console
$ luria index
```

The chain page is generated from declared edges. `docs/durable-jobs-lineage.md` nests each step under the one it follows:

```markdown
# Durable jobs lineage

1 line, walked from `extends:` and `corrects:` on RFC documents. Each step explains itself; this page is the order they came in.

## From Durable jobs with acknowledgements

- [RFC-001](../record/rfcs.d/RFC-001.md) — Durable jobs with acknowledgements *(Proposed)*
  - [RFC-002](../record/rfcs.d/RFC-002.md) — Renewable leases for durable jobs *(Proposed)*
    - [RFC-003](../record/rfcs.d/RFC-003.md) — Lease recovery without global polling *(Proposed)*
```

Do not hand-maintain that sequence elsewhere. The chain exists specifically to avoid a second prose lineage drifting from the source relations. That is [DP-3](../../record/principles.d/DP-003.md)'s source/projection principle applied to history.

## 6. Add vocabulary-backed facets

A chain is more useful when each step carries the axes needed to interpret it.

By default, each step shows its `status`. To show more, declare the field on the scheme first — `facet_by` naming an undeclared field stops `luria index` with `facet_by names 'consensus', which RFC does not declare`:

```yaml
vocabularies:
  # rfc-status, area ...
  consensus:
    emerging: {}
    contested: {}
    converged: {}

schemes:
  RFC:
    # ...
    fields:
      # status, tags ...
      consensus:
        vocabulary: consensus
```

A declared field is optional unless it says `required: true`. Then name it in the chain:

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

Set `status:` and `consensus:` in each RFC's frontmatter (RFC-001 and RFC-002 `Accepted`, `converged` and `contested`; RFC-003 stays `Proposed`, `emerging`) and run `luria index`. Each step now carries both facets:

```markdown
- [RFC-001](../record/rfcs.d/RFC-001.md) — Durable jobs with acknowledgements *(Accepted, converged)*
  - [RFC-002](../record/rfcs.d/RFC-002.md) — Renewable leases for durable jobs *(Accepted, contested)*
    - [RFC-003](../record/rfcs.d/RFC-003.md) — Lease recovery without global polling *(Proposed, emerging)*
```

The sequence is the same graph either way, but the interpretation is not.

Vocabularies therefore serve at least three roles:

1. classify records,
2. constrain admissible values,
3. facet higher-order views.

See [Vocabularies and independent dimensions](../concepts/vocabularies.md).

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
    sibling: compared_against
    invariant: tags
    facet_by:
      - status
      - consensus
    output: docs/durable-jobs-lineage.md
    title: Durable jobs lineage
```

Now the line itself asserts something:

> These records are not merely connected; they are steps in one subject lineage.

A chain's invariant asserts each edge it walks and the line as a whole ([ADR-106](../../record/decisions.d/ADR-106.md)). The page is also organized by it: after `luria index`, the line appears under a `## runtime` heading, the value its members share ([ADR-113](../../record/decisions.d/ADR-113.md)). If a step shares no tag with the line, `luria lint` reports it.

## 8. Treat an invariant failure as diagnosis, not a verdict

Suppose:

```text
RFC-001 tags: [runtime]
RFC-002 tags: [runtime]
RFC-003 tags: [security]
```

but `RFC-003 corrects RFC-002`. Change RFC-003's tag to `security` and run `luria index` and `luria lint`. The lint still passes — these are warnings — and reports:

```text
luria: 1 relation(s) assert an invariant neither end holds — either the field is missing a value that is true, or the relation is wrong (`luria reports` for the table)
  RFC-002 ↔ RFC-003 share no `tags` (durable-jobs; each holds: runtime / security)
luria: 1 sequence(s) share no value across every member, though each step may — the weaker signal, to read whole before acting on
  RFC-001, RFC-002, RFC-003 share no `tags` across the whole line (durable-jobs)
```

The chain page moves the line under a `` ## Sharing no `tags` `` heading.

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

```console
$ luria new rfc --title "Durable jobs on an external broker" --tags runtime
$ luria relate RFC-004 compared_against RFC-002
$ luria index
```

A sibling relation allows the generated view to show that comparison without pretending `RFC-004` is the next successor. It joins the line as an `alongside:` entry, not a nested step:

```markdown
- [RFC-001](../record/rfcs.d/RFC-001.md) — Durable jobs with acknowledgements *(Accepted, converged)*
  - [RFC-002](../record/rfcs.d/RFC-002.md) — Renewable leases for durable jobs *(Accepted, contested)*
    - [RFC-003](../record/rfcs.d/RFC-003.md) — Lease recovery without global polling *(Proposed, emerging)*
- alongside: [RFC-004](../record/rfcs.d/RFC-004.md) — Durable jobs on an external broker *(Proposed)*
```

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

This is an application of [DP-15](../../record/principles.d/DP-015.md)'s concern with silent non-events: “nothing happened” should not be indistinguishable from “everything worked.”

## 11. Publish the chain

A chain's output is a generated projection and participates in the publishing surface like other views.

A published chain is especially useful because it answers questions that per-document pages cannot:

- Where did this line start?
- Which step followed which predecessor?
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
