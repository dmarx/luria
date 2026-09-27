# Tutorial: Build a governed RFC process

This tutorial starts from an empty repository and builds a small RFC record.

The model we build is illustrative:

```text
RFC → DECISION → IMPLEMENTATION
         ↑
       PROCESS
```

Your own process may collapse some of these objects, split them differently, or omit them. The point is to learn the mechanics and the modeling questions, not to prescribe a universal RFC ontology. Luria's [DP-14](../../record/principles.d/DP-014.md) explicitly favors meeting a project where it is over forcing one canonical shape ([DP-14](../../record/principles.d/DP-014.md)).

## 1. Install Luria

```console
$ pip install luria
$ mkdir example-rfcs
$ cd example-rfcs
$ git init
```

Do not create numbered RFC files or record directories by hand. First declare the record.

## 2. Write `luria.yaml`

Start with a single RFC scheme:

```yaml
vocabularies:
  rfc-status:
    Proposed:
      blurb: under review
    Accepted:
      blurb: the proposal currently stands
    Rejected:
      blurb: considered and not adopted
    Superseded:
      blurb: replaced by a later proposal

  area:
    runtime: {}
    storage: {}
    api: {}
    operations: {}

schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    active: Accepted
    fields:
      status:
        vocabulary: rfc-status
      tags:
        vocabulary: area
        many: true
        required: true
        closed: true
```

The desired record is declared before it is instantiated. `luria init` plans its scaffold from configuration ([ADR-048](../../record/decisions.d/ADR-048.md)).

## 3. Scaffold the record

Inspect the plan:

```console
$ luria init --dry-run
```

Then create it:

```console
$ luria init
```

Conceptually:

```text
luria.yaml

record/
  rfcs.d/

docs/
  rfcs/
```

If you later add another family or scheme, update `luria.yaml` and run `luria init` again rather than inventing a parallel layout manually.

## 4. Create the first RFC

```console
$ luria new RFC --title "Introduce durable background jobs"
```

`luria new` is configuration-driven: the configured record determines what entry kinds exist and where they are filed ([ADR-036](../../record/decisions.d/ADR-036.md)).

Fill the substantive fields and prose in the generated file:

```yaml
status: Proposed
tags:
  - runtime
```

```markdown
## Motivation

Some work must survive process restarts.

## Proposal

Persist submitted jobs before acknowledging them. Workers claim jobs,
execute them, and record successful completion.
```

Now check the record:

```console
$ luria lint
```

## 5. Generate the read view

```console
$ luria index
```

The source record is authoritative; `docs/rfcs/` is a projection.

```text
record/rfcs.d/
      ↓
docs/rfcs/
```

Edit the source and regenerate the view. Do not maintain both independently. That is the concrete application of [DP-3](../../record/principles.d/DP-003.md): hand-maintained projections drift ([DP-3](../../record/principles.d/DP-003.md)).

## 6. Change standing without erasing history

After review, the RFC may become:

```yaml
status: Accepted
```

or:

```yaml
status: Rejected
```

Keep rejected records. They may preserve alternatives, measurements, objections, or constraints.

Later, an accepted RFC may become:

```yaml
status: Superseded
```

The identity remains. Standing changes.

## 7. Decide whether proposal and decision need separate identities

Some processes treat an accepted RFC as the decision itself. That is valid.

Others benefit from distinguishing:

```text
proposal
```

from:

```text
commitment resulting from the proposal
```

Ask whether they can be cited, revised, or superseded independently. [DP-12](../../record/principles.d/DP-012.md)'s general principle is that independently meaningful citable things often deserve independently coherent identities ([DP-12](../../record/principles.d/DP-012.md)).

For this tutorial, add a decision scheme.

## 8. Add `DECISION`

Extend the config:

```yaml
vocabularies:
  # ...
  decision-status:
    Active: {}
    Superseded: {}

schemes:
  # RFC ...

  DECISION:
    dir: record/decisions.d
    output: docs/decisions
    active: Active

    references:
      rfc:
        scheme: RFC
        required: true
        label: Adopted RFC

    fields:
      status:
        vocabulary: decision-status
      tags:
        vocabulary: area
        many: true
        required: true
        closed: true
```

Then reconcile the declared shape:

```console
$ luria init --dry-run
$ luria init
```

Create the decision:

```console
$ luria new DECISION --title "Adopt durable background jobs"
```

Fill:

```yaml
status: Active
tags:
  - runtime
rfc: RFC-001
```

You now have an explicit semantic edge:

```text
DECISION-001 ──adopts──► RFC-001
```

A declared reference is stronger than a string field: Luria can check its shape, scheme, and resolution.

## 9. Add implementation state only if it matters independently

If you need to ask:

> Is the active decision implemented?

then implementation state may deserve its own object.

Declare an `IMPLEMENTATION` scheme with a typed `decision` reference, reconcile with `luria init`, and create one with:

```console
$ luria new IMPLEMENTATION --title "Durable worker queue"
```

Now:

```text
RFC-001
   ↓
DECISION-001
   ↓
IMPLEMENTATION-001
```

represents proposal, commitment, and realization as independently evolving knowledge.

## 10. Supersede a decision

Create a successor RFC and decision using `luria new`.

Then mark the old decision:

```yaml
status: Superseded
```

Do not rewrite history to make the old choice disappear.

Luria's own decision doctrine distinguishes changed choices from corrected reasons: changed choices are superseded; a wrong recorded reason can be corrected visibly when the choice itself still stands ([ADR-019](../../record/decisions.d/ADR-019.md)).

If successor lineage matters, declare a `superseded_by` reference and record:

```text
DECISION-001 ──superseded_by──► DECISION-002
```

## 11. Observe contextual invalidation

Suppose `IMPLEMENTATION-001` still points at `DECISION-001`.

The target exists and the edge resolves, but its standing changed.

That is exactly the condition Luria is meant to expose:

```text
premise changes
      ↓
dependent use becomes inspectable
```

The correct response may be migration, historical acknowledgement, or no change at all. Luria should surface the condition; humans decide what it means.

## 12. Findings are not automatically failures

A retrospective may intentionally cite a superseded decision.

Luria's lint model is warn-first. Warning classes can be promoted to failures, baselined, or explicitly acknowledged; acknowledgements remain part of the accounting rather than becoming silence ([ADR-035](../../record/decisions.d/ADR-035.md); [DP-1](../../record/principles.d/DP-001.md)).

The working loop becomes:

```text
luria lint
   ↓
mechanical? → luria repair
judgment?   → luria ack
```

See [Resolve findings](../how-to/findings.md).

## 13. Introduce process knowledge when it is useful

Process rules can arise from many sources:

- an incident,
- a near miss,
- a foreseeable vulnerability,
- repeated review friction,
- prior experience,
- or a deliberate policy adopted proactively.

There is no required chronology.

For example:

> Every superseded decision identifies its successor.

may be adopted before the first supersession because the ambiguity is obvious, or afterward because an incident exposed it.

The important movement is:

```text
important norm
    ↓
explicit process knowledge
    ↓
mechanism where useful
```

[DP-5](../../record/principles.d/DP-005.md) describes the general ladder from prose to convention to mechanism to guarantee ([DP-5](../../record/principles.d/DP-005.md)).

## 14. Give process rules identities when that helps

If process rules themselves need history, standing, and citation, add a `PROCESS` scheme.

Then:

```console
$ luria init
$ luria new PROCESS --title "Superseded decisions identify their successors"
```

The process record preserves rationale and standing. Configuration can implement the mechanical part, for example making `superseded_by` conditionally required.

The prose explains **why**. The config expresses what the machine can actually check.

## 15. The documentation is also a dependent

This tutorial claims that:

- `luria init` is configuration-driven — [ADR-048](../../record/decisions.d/ADR-048.md).
- `luria new` is configuration-driven — [ADR-036](../../record/decisions.d/ADR-036.md).
- correction differs from supersession — [ADR-019](../../record/decisions.d/ADR-019.md).
- warnings and acknowledgements participate in configurable enforcement — [ADR-035](../../record/decisions.d/ADR-035.md).

Those references are maintenance edges.

If a governing decision becomes inactive, this prose should become a candidate for review even if nobody edited the tutorial.

That recursive property is deliberate: Luria's docs should demonstrate the same truth-maintenance behavior they teach.

## What you built

A possible final record:

```text
luria.yaml

record/
  rfcs.d/
  decisions.d/
  implementations.d/
  process.d/

docs/
  rfcs/
  decisions/
  implementations/
  process/
```

The important structure is semantic:

```text
          PROCESS
             │
             ▼
RFC ───► DECISION ───► IMPLEMENTATION
            │
            └──superseded_by──► DECISION
```

The next tutorial adds a different capability: deriving longitudinal structure from local relations.

Continue with [Build a lineage with chains](chains.md).
