# Luria documentation

This documentation is organized by reader intent.

## Tutorials

Learn Luria by building a working record.

- [Build a governed RFC process](tutorials/rfc-process.md)
- [Build a lineage with chains](tutorials/chains.md)
- [Adopt Luria around an existing corpus](tutorials/adopt-existing-corpus.md)

Tutorials intentionally use only supported workflows: declare the record in `luria.yaml`, scaffold with `luria init`, create entries with `luria new`, add relations with the record/CLI mechanisms, inspect with `luria lint`, and derive views with `luria index`.

## Concepts

Understand the model and the distinctions Luria preserves.

- [The record model](concepts/record-model.md)
- [Identity, standing, and history](concepts/identity-standing-history.md)
- [Relations and chains](concepts/relations-and-chains.md)
- [Vocabularies and epistemic axes](concepts/vocabularies.md)
- [Findings and truth maintenance](concepts/findings.md)
- [Sources and projections](concepts/sources-and-projections.md)
- [Record theory and self-governance](concepts/governance.md)
- [External knowledge and remotes](concepts/remotes.md)

## How-to guides

Accomplish a concrete task.

- [Model and add relations](how-to/relations.md)
- [Define and publish a chain](how-to/chains.md)
- [Resolve, repair, and acknowledge findings](how-to/findings.md)
- [Use merge-time identity allocation](how-to/merge-allocation.md)
- [Use journals and fragment directories](how-to/journals-fragments.md)
- [Reference remote knowledge](how-to/remotes.md)
- [Publish and export a record](how-to/publishing.md)
- [Run Luria in CI](how-to/ci.md)

## Reference

Look up exact interfaces and configuration.

- [CLI reference](reference/cli.md)
- [Configuration reference](reference/configuration.md)
- [Findings and directives reference](reference/findings-and-directives.md)

Reference pages should describe current implementation contracts. Design rationale belongs in ADRs and DPs and is cited rather than duplicated.

## Contributing to the documentation

- [Documenting Luria](contributing/documentation.md)
- [Coverage matrix](coverage-matrix.md)

The documentation is itself a consumer of Luria's record. Behavioral claims should cite the ADRs/DPs they depend on so supersession can surface stale prose.
