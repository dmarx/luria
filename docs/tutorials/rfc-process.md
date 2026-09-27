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

`init` writes only what is missing and reports what it skipped. For this config it writes:

```text
.github/workflows/docs.yml     CI: repair, index and lint
.github/workflows/pages.yml    CI: publish the site
CLAUDE.md                      a short map for coding agents
docs/README.md                 the docs index
record/
  changelog.d/_template.md     default fragment directory
  devlog.d/_template.md        default journal
  rfcs.d/_template.md          the form `luria new rfc` copies
  rfcs.d/README.stub
```

The changelog and devlog come with every scaffold; `docs/rfcs/` is not scaffolded — `luria index` generates it.

Build the views once before the first lint, because the scaffolded `docs/README.md` links pages that only `luria index` writes:

```console
$ luria index
$ luria lint
```

A fresh scaffold passes (exit status 0). Two advisories are expected and do not fail the lint: `CLAUDE.md:4: docs/design-principles.md resolves to nothing` (the scaffolded `CLAUDE.md` points at a principles page this config never generates — edit that line to suit your project), and a note that two one-shot `luria upgrade` commands have nothing to do here.

If you later add another family or scheme, update `luria.yaml` and run `luria init` again rather than inventing a parallel layout manually.

## 4. Create the first RFC

```console
$ luria new rfc --title "Introduce durable background jobs" --tags runtime
record/rfcs.d/RFC-001.md
```

`luria new` is configuration-driven: the configured record determines what entry kinds exist and where they are filed, and a scheme's kind is its prefix in lower case ([ADR-036](../../record/decisions.d/ADR-036.md)).

The template stamps `status: Proposed` and `tags: [record]`. `Proposed` is in `rfc-status`; `record` is not in the closed `area` vocabulary, which is why the command passes `--tags runtime`. Without it, lint fails with `` `tags: record` is not in the `area` vocabulary ``, and you would edit the file to fix it. The generated frontmatter now reads:

```yaml
status: Proposed
tags:
- runtime
```

Write the prose in the body:

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

It passes, and adds one line: `pending decisions: 1 undecided document(s)`. A `Proposed` RFC is a document waiting for a decision, and the lint keeps count of them.

## 5. Generate the read view

```console
$ luria index
```

The source record is authoritative; `docs/rfcs/` is a projection: an index page, plus one page per `status` and per `tags` value.

```text
record/rfcs.d/
      ↓
docs/rfcs/
```

Edit the source and regenerate the view. Do not maintain both independently. A view directory carries its own generated index, so it needs no entry in `docs/README.md`; a page you write by hand directly in `docs/` does, or lint fails with `missing index entry`. That is the concrete application of [DP-3](../../record/principles.d/DP-003.md): hand-maintained projections drift ([DP-3](../../record/principles.d/DP-003.md)).

## 6. Change standing without erasing history

After review, edit `record/rfcs.d/RFC-001.md` and change `status:`. For this tutorial, accept it:

```yaml
status: Accepted
```

Other possible outcomes:

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
  # rfc-status, area ...
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
$ luria new decision --title "Adopt durable background jobs" --status Active --tags runtime
record/decisions.d/DECISION-001.md
$ luria relate DECISION-001 rfc RFC-001
record/decisions.d/DECISION-001.md: rfc += RFC-001
```

`--status Active` matters: the template stamps `Proposed`, which `decision-status` does not contain. `luria relate SOURCE FIELD TARGET` writes the reference into the frontmatter:

```yaml
rfc: RFC-001
```

Until it does, lint fails with ``no `rfc:` in frontmatter``, because a declared reference is required unless it says `required: false`. Lint also warns that `record/decisions.d/_template.md` does not scaffold `rfc:`; that is a note about the form, not a failure (see [placeholder codes](../importing.md#placeholder-codes-in-templates) if you want to add one).

You now have an explicit semantic edge, named by the field:

```text
DECISION-001 ──rfc──► RFC-001
```

A declared reference is stronger than a string field: Luria can check its shape, scheme, and resolution. Had RFC-001 still been `Proposed`, the lint would already say so: `RFC-001 is Proposed, cited 1× in 1 file(s)`.

## 9. Add implementation state only if it matters independently

If you need to ask:

> Is the active decision implemented?

then implementation state may deserve its own object.

Declare an `IMPLEMENTATION` scheme with its own status vocabulary and a typed `decision` reference:

```yaml
vocabularies:
  # ...
  implementation-status:
    Planned: {}
    Shipped: {}
    Abandoned: {}

schemes:
  # RFC, DECISION ...

  IMPLEMENTATION:
    dir: record/implementations.d
    output: docs/implementations
    active: Shipped

    references:
      decision:
        scheme: DECISION
        label: Implements

    fields:
      status:
        vocabulary: implementation-status
      tags:
        vocabulary: area
        many: true
        required: true
        closed: true
```

Without the `status` field, the template's `Proposed` would be reported as unchecked. Reconcile and create one:

```console
$ luria init
$ luria new implementation --title "Durable worker queue" --status Shipped --tags runtime
$ luria relate IMPLEMENTATION-001 decision DECISION-001
$ luria index
$ luria lint
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

Create a successor RFC and decision:

```console
$ luria new rfc --title "Durable jobs with renewable leases" --status Accepted --tags runtime
$ luria new decision --title "Adopt lease-based durable jobs" --status Active --tags runtime
$ luria relate DECISION-002 rfc RFC-002
```

Then edit `record/decisions.d/DECISION-001.md` to mark the old decision:

```yaml
status: Superseded
```

Do not rewrite history to make the old choice disappear.

Luria's own decision doctrine distinguishes changed choices from corrected reasons: changed choices are superseded; a wrong recorded reason can be corrected visibly when the choice itself still stands ([ADR-019](../../record/decisions.d/ADR-019.md)).

Run `luria lint`. It fails:

```text
luria: 1 violation(s)
  record/decisions.d/DECISION-001.md: no `superseded_by:` in frontmatter — `superseded_by` names a document in any scheme, because `status: Superseded` (built in: `superseded_by` (ADR-071))
```

Every scheme has a built-in `superseded_by` reference, required exactly when `status` is `Superseded` (ADR-071). You do not declare it; declaring your own `superseded_by` in `references` replaces the built-in, and would be required on every entry unless it says `required: false`. Record the successor:

```console
$ luria relate DECISION-001 superseded_by DECISION-002
record/decisions.d/DECISION-001.md: superseded_by += DECISION-002
```

```text
DECISION-001 ──superseded_by──► DECISION-002
```

## 11. Observe contextual invalidation

`IMPLEMENTATION-001` still points at `DECISION-001`.

The target exists and the edge resolves, but its standing changed. Run `luria index`, then `luria lint`. It passes, and reports:

```text
luria: 1 warning(s) — retired documents cited unacknowledged from current docs/code (`luria reports` for the sites, `inactive-ok:` to acknowledge one)
  DECISION-001 is Superseded, cited 1× in 1 file(s) — Adopt durable background jobs
```

That is exactly the condition Luria is meant to expose:

```text
premise changes
      ↓
dependent use becomes inspectable
```

The correct response may be migration, historical acknowledgement, or no change at all. Luria surfaces the condition; humans decide what it means.

## 12. Findings are not automatically failures

A retrospective may intentionally cite a superseded decision.

Luria's lint model is warn-first. Warning classes can be promoted to failures with `lint.fail_on` ([ADR-035](../../record/decisions.d/ADR-035.md)), held to a standing count with `lint.baseline` (see [configuration](../configuration.md)), or explicitly acknowledged with a [comment directive](../directives.md); acknowledgements remain part of the accounting rather than becoming silence ([DP-1](../../record/principles.d/DP-001.md)).

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

If process rules themselves need history, standing, and citation, add a `PROCESS` scheme:

```yaml
schemes:
  # ...
  PROCESS:
    dir: record/process.d
    output: docs/process
    active: Active
    fields:
      status:
        vocabulary: decision-status
      tags:
        vocabulary: area
        many: true
        required: true
        closed: true
```

Then:

```console
$ luria init
$ luria new process --title "Superseded decisions identify their successors" --status Active --tags operations
```

The process record preserves rationale and standing. Configuration implements the mechanical part where it can. For this rule the machine already does: the built-in `superseded_by` is required whenever `status` is `Superseded` (step 10). A rule of your own takes a declared field or reference with `required_when` (see [configuration](../configuration.md)).

The prose explains **why**. The config expresses what the machine can actually check.

## 15. The documentation is also a dependent

This tutorial claims that:

- `luria init` is configuration-driven — [ADR-048](../../record/decisions.d/ADR-048.md).
- `luria new` is configuration-driven — [ADR-036](../../record/decisions.d/ADR-036.md).
- correction differs from supersession — [ADR-019](../../record/decisions.d/ADR-019.md).
- warnings and acknowledgements participate in configurable enforcement — [ADR-035](../../record/decisions.d/ADR-035.md).
- a superseded document names its successor in `superseded_by:` — ADR-071.

Those references are maintenance edges.

If a governing decision becomes inactive, the lint reports this page as citing it, even if nobody edited the tutorial.

That recursive property is deliberate: Luria's docs should demonstrate the same truth-maintenance behavior they teach.

## What you built

A possible final record:

```text
luria.yaml
CLAUDE.md
.github/workflows/

record/
  rfcs.d/
  decisions.d/
  implementations.d/
  process.d/
  changelog.d/
  devlog.d/

docs/
  README.md
  record.md
  rfcs/
  decisions/
  implementations/
  process/
  devlog/
  reports/
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
