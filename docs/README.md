# Luria documentation

Luria keeps a record of what a project knows — decisions, principles, a
changelog, a devlog, or whatever families the project declares. Every entry
has a name something can cite, a standing that says whether it still holds,
and rules the lint enforces; every view is generated from those entries.

This page is the map, organized by what you are trying to do. (`luria lint`
checks that every page in `docs/` is listed here, so the map cannot
silently rot.)

**Already have a corpus?** You do not need to redesign it into a
Luria-shaped repository. Pick one distinction or dependency worth making
explicit, wrap Luria around it, and add governance as it earns its keep:
start with [Adopt Luria around an existing corpus](tutorials/adopt-existing-corpus.md),
then [Adopting Luria](adopting.md) and [Importing an existing corpus](importing.md).

## Tutorials

Learn Luria by building a working record, start to finish.

- [Quickstart](quickstart.md) — install, scaffold, file, lint: the whole
  loop in ten minutes, including breaking the record on purpose to see a
  finding.
- [Build a governed RFC process](tutorials/rfc-process.md) — declare
  schemes, vocabularies and typed references for RFCs, decisions and
  implementations, then watch a supersession surface.
- [Build a lineage with chains](tutorials/chains.md) — state succession
  edges between entries and let Luria derive the line, its siblings, facets
  and invariant.
- [Adopt Luria around an existing corpus](tutorials/adopt-existing-corpus.md)
  — put a record around material that already exists.

## Concepts

Understand the model and the distinctions Luria preserves. Read
[Concepts](concepts.md) first; go to a focused page when you need one
distinction in depth; go to [Designing a record](modeling.md) when you are
making modeling choices for your own record.

- [Concepts](concepts.md) — the shortest complete mental model: entries,
  citations, the status field everything hangs off, and what a finding is.
- [The record model](concepts/record-model.md) — what a record holds, and
  why the families mean different things.
- [Identity, standing, and history](concepts/identity-standing-history.md)
  — a name that persists while its standing changes; supersede vs. correct.
- [Relations and chains](concepts/relations-and-chains.md) — typed
  references, converses, and lines derived from succession edges.
- [Vocabularies](concepts/vocabularies.md) — closed value sets as
  constraints, classifications, and facets.
- [Findings and truth maintenance](concepts/findings.md) — violations,
  warning classes, and acknowledgements.
- [Sources and projections](concepts/sources-and-projections.md) — what is
  authored, what is derived, and which command derives it.
- [Record theory and self-governance](concepts/governance.md) — records
  whose subject includes their own rules.
- [External knowledge and remotes](concepts/remotes.md) — citing
  identities owned elsewhere.
- [Designing a record](modeling.md) — how to make modeling choices: what
  belongs in a record, which family fits which material, when two kinds of
  entry are two schemes, and what the schema can be made to refuse.
- [Project memory](project-memory.md) — one application of Luria, not its
  definition: a software project's decisions, principles, changelog and
  devlog, walked through the machine end to end (sources and views, the
  four families, statuses, constraints, references).

## How-to guides

Accomplish a concrete task.

- [Adopting Luria](adopting.md) — bringing the record to an existing
  project, the CI wiring, and the published site.
- [Importing an existing corpus](importing.md) — turning material that
  already exists as data into a record, and what that surfaces.
- [Model and add relations](how-to/relations.md)
- [Define and publish a chain](how-to/chains.md)
- [Resolve, repair, and acknowledge findings](how-to/findings.md)
- [Use merge-time identity allocation](how-to/merge-allocation.md)
- [Use journals and fragment directories](how-to/journals-fragments.md)
- [Reference remote knowledge](how-to/remotes.md)
- [Publish and export a record](how-to/publishing.md)
- [Run Luria in CI](how-to/ci.md)

## Reference

Exact current behavior. Design rationale lives in the decisions and
principles, and is cited rather than repeated.

- [CLI reference](cli.md) — every command, flag by flag.
- [Comment directives](directives.md) — acknowledging a lint finding where
  it happens, with the reason attached; also the fixture-code convention.
- [Configuration](configuration.md) — *generated* by `luria index` from the
  dataclasses that parse `luria.yaml`: every key, type, and default.
- [The record](record.md) — *generated*: the shape *this* project gave the
  machinery, what families exist, where entries are filed, and what to type
  to add one.

## This project's record

Luria's own memory, kept with the tool it ships:

- [Decisions](decisions/README.md) — every architectural choice, with
  status, tags, and alternatives.
- [Design principles](design-principles.md) — the standing values, one
  page, anchored for citation.
- [Development log](devlog/README.md) — the narrative: root causes, failed
  approaches, and the traps the next person would otherwise rediscover.
- Status reports — [pending decisions](reports/pending-decisions.md) and
  [reference status](reports/reference-status.md): what awaits a human eye.

## Contributing to the documentation

- [Documenting Luria](contributing/documentation.md) — how a page cites
  the record it depends on, and the house rules the lint enforces.
