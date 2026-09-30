<p align="center">
  <img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg"
       alt="Luria — project memory" width="480">
</p>

<!-- luria:badges -->
[![needs decision: 6](https://img.shields.io/badge/needs%20decision-6-orange)](docs/reports/pending-decisions.md)
[![cited, not in force: 3](https://img.shields.io/badge/cited,%20not%20in%20force-3-orange)](docs/reports/reference-status.md)
<!-- /luria:badges -->

<!-- luria:site -->
📖 **[dmarx.github.io/luria](https://dmarx.github.io/luria/)** — this record, published by `luria site`.
<!-- /luria:site -->

# Luria

**Governed knowledge, kept coherent under change.**

Luria is a framework for maintaining bodies of knowledge whose meaning changes over time.

A Luria record can hold decisions, proposals, recommendations, evidence, policies, principles, incidents, standards, interpretations, observations, theories, or other claims that acquire relationships and standing as a corpus evolves.

The central idea is simple:

> **When one piece of knowledge changes, Luria helps expose what else may need reconsideration.**

A document can become stale without anyone editing it. A decision is superseded; an implementation still cites it. A paper remains historically important while a recommendation based on it is retired. A policy still points to authority that no longer applies. The strings continue to resolve, but the surrounding context has changed.

Luria makes more of that context explicit.

## The operating loop

A record begins with a declaration of the knowledge system you want:

```text
luria.yaml
    ↓
luria init
    ↓
luria new
    ↓
author
    ↓
luria lint
    ↓
luria index
```

`luria init` plans the scaffold from configuration rather than copying one universal tree ([ADR-048](record/decisions.d/ADR-048.md)). `luria new` derives the entry kinds it can create from that same configured record ([ADR-036](record/decisions.d/ADR-036.md)).

A minimal record might declare RFCs:

```yaml
vocabularies:
  rfc-status:
    Proposed: {}
    Accepted: {}
    Rejected: {}
    Superseded: {}

schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Accepted
    fields:
      status:
        vocabulary: rfc-status
```

Then:

```console
$ luria init
$ luria new rfc --title "Introduce durable background jobs"
$ luria lint
$ luria index
```

The important thing is not YAML or Markdown by themselves. It is that the repository now contains identifiable objects whose fields, relations, standing, and generated projections have declared semantics.

## Identity is not standing

An object may keep the same identity while its standing changes:

```text
RFC-017

Proposed → Accepted → Superseded
```

Historical existence and current authority are different properties.

Luria's own decision doctrine makes the same distinction at the level of change: if the choice changes, supersede it; if the choice stands but the recorded reason was wrong, correct the record visibly rather than manufacturing a false history ([ADR-019](record/decisions.d/ADR-019.md)).

## References are dependencies

A reference can mean more than “this string names another file.”

```text
IMPLEMENTATION-008
    ──implements──►
DECISION-014
```

If `DECISION-014` becomes superseded, the edge may still resolve while the use becomes questionable. Luria can surface that condition for review rather than pretending every consequence is mechanically decidable.

This is the truth-maintenance loop:

```text
premise changes
      ↓
dependent condition surfaces
      ↓
finding
      ↓
human review
```

## Findings are not all failures

Some suspicious conditions are legitimate. A retrospective may intentionally cite a superseded decision. A remote reference may be temporarily unavailable. A corpus may have a known backlog.

Luria distinguishes findings from enforcement. Warning classes are reported by default and can be promoted to failures ([ADR-035](record/decisions.d/ADR-035.md)), baselined, or explicitly acknowledged — without the acknowledgement disappearing from the accounting ([DP-1](record/principles.d/DP-001.md)).

The useful pattern is:

```text
lint discovers
     ↓
repair fixes what is mechanical
     ↓
ack records human judgment
```

## Relations compose into structures

Local relations can carry higher-order meaning.

Suppose records declare:

```text
A extends B
C corrects A
D compared_against C
```

A Luria **chain** can walk one or more same-scheme succession relations into a generated sequence, add sibling/rival edges, carry vocabulary-backed facets onto each step, and check an invariant across the line ([ADR-083](record/decisions.d/ADR-083.md), [ADR-106](record/decisions.d/ADR-106.md), [ADR-113](record/decisions.d/ADR-113.md)).

> **Authors state the edges. Luria derives the line.**

That supports decision succession, research lineages, evolving recommendations, standards families, policy histories, or explanatory theories without maintaining a second hand-written lineage that can drift.

See [Relations and chains](docs/concepts/relations-and-chains.md) and the [chains tutorial](docs/tutorials/chains.md).

## Different record families mean different things

Luria's major record families are semantically distinct:

| Family | Role |
|---|---|
| **Scheme** | identifiable objects with standing and relations |
| **Journal** | dated observations whose sources persist |
| **Fragment directory** | distributed contributions assembled into another artifact |
| **Remote** | identities or authorities owned elsewhere |

Generated indexes, chain pages, reports, sites, and exports are **projections**, not competing sources of truth. [DP-3](record/principles.d/DP-003.md) states the general rule: if a view can be derived from an authoritative source, derive it rather than maintaining a parallel copy.

## Vocabularies are more than labels

A vocabulary can classify records, constrain admissible values, and act as an interpretive axis in generated views.

For example:

```text
status     = what this record currently endorses
consensus  = what the field appears to believe
```

Those values can vary independently. On a chain, they can be rendered as facets so a converged trunk, a contested branch, and a provisional successor are not flattened into the same-looking sequence.

## A record can contain knowledge about itself

Some claims describe the subject:

```text
Use renewable leases for durable jobs.
```

Others govern how claims are represented and changed:

```text
Every superseded decision names its successor.
```

Call the subject-level record *R* and the governing knowledge *M*. The question Luria keeps asking is:

```text
M; R ⊢ x
```

That is: given the current record and the rules under which it operates, does this object or relation still make sense?

The distinction can remain conceptual, be tagged inside one record, use a separate scheme, or live in a dedicated meta-record. Luria meets the corpus where it is rather than requiring one canonical decomposition ([DP-14](record/principles.d/DP-014.md)).

## Documentation is part of the record

Luria's own documentation should depend on the decisions and principles that make its behavioral claims true.

This README says that `luria init` is configuration-driven, so it cites [ADR-048](record/decisions.d/ADR-048.md). It says `luria new` derives entry kinds from configuration, so it cites [ADR-036](record/decisions.d/ADR-036.md).

Those are maintenance edges, not decorative footnotes.

When a governing ADR stops being in force, the documentation that cites it becomes reviewable even though nobody edited the prose: `luria lint` reports the citation under the `retired-citations` warning class.

That is the product demonstrating its own thesis.

## Where to go next

- **New to Luria:** [Build a governed RFC process](docs/tutorials/rfc-process.md)
- **Want to see chains:** [Build a lineage with chains](docs/tutorials/chains.md)
- **Already have a corpus:** [Adopt Luria around an existing corpus](docs/tutorials/adopt-existing-corpus.md)
- **Understand the model:** [Concepts](docs/concepts.md)
- **Do a specific task:** [How-to guides](docs/README.md#how-to-guides)
- **Look up exact behavior:** [Reference](docs/README.md#reference)
- **Understand why Luria behaves this way:** follow the cited ADRs and DPs.

## Installation

Luria requires Python 3.11 or later.

```console
$ pip install luria
```

## License

MIT — see [LICENSE](LICENSE).

---

**Luria — governed knowledge, kept coherent under change.**
