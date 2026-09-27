# How to run Luria in CI

CI should enforce only guarantees the record has intentionally adopted.

## Core check

```console
$ luria lint
```

The CLI contract treats lint as the command that can fail the record check.

## Generated views

Use the current `luria index` check mode, if configured/supported in the version you run, to verify that committed projections are current without making every branch a writer.

[DP-2](../../record/principles.d/DP-002.md)'s rule is important here: generated shared artifacts should be written where merges serialize, not independently by every branch ([DP-2](../../record/principles.d/DP-002.md)).

## Merge-allocated identities

On a serialized trunk:

```console
$ luria concretize --check
```

ensures provisional identities do not remain where permanent order is supposed to be known ([ADR-049](../../record/decisions.d/ADR-049.md)).

## Reports

The CLI identifies `luria reports` as primarily a CI caller.

Use it to materialize status/finding summaries as artifacts.

## Fragment collection

The CLI likewise treats `luria collect` as primarily a CI/serialization-point operation.

That avoids consuming fragments locally before reviewers see the independent contributions.

## Remote verification

Choose the configured network policy deliberately.

A hermetic CI run and a network-required CI run make different guarantees.

## Enforcement policy

Do not make every new warning fatal by default.

Luria's [ADR-035](../../record/decisions.d/ADR-035.md) model supports:

- reported classes,
- `fail_on`,
- baselines,
- acknowledgements.

Promote a class when the project is ready to treat it as a guarantee.
