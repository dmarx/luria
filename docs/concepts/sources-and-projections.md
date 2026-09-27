# Concept: Sources and projections

A maintained record needs a clear direction of authority.

## Source

The source is where knowledge is authored.

Examples:

```text
record/decisions.d/ADR-019.md
record/literature.d/LIT-042.md
record/devlog.d/...
```

## Projection

A projection is derived from source knowledge.

Examples:

- indexes,
- concatenated documents,
- chain pages,
- status reports,
- published sites,
- SQLite exports.

The governing direction is:

```text
source
  ↓
projection
```

not:

```text
source ↔ projection
```

## Why this matters

A hand-maintained copy can become wrong without producing any signal.

[DP-3](../../record/principles.d/DP-003.md) states Luria's general rule: a projection of an authoritative source should be derived whenever possible ([DP-3](../../record/principles.d/DP-003.md)).

That is why:

```console
$ luria index
```

regenerates views rather than treating them as separately authored documents.

## Generated views and concurrency

[DP-2](../../record/principles.d/DP-002.md) adds another dimension: when a shared artifact must be generated, the writer belongs where merges serialize, not on every branch ([DP-2](../../record/principles.d/DP-002.md)).

This prevents “generated but still conflicted” artifacts from becoming a hidden shared-file lock.

## Chain pages

A chain page is a projection of local relation edges.

It intentionally renders history, including inactive or superseded steps. The page itself is not where lineage is authored.

## Sites

`luria site` stages the record for publication. Publishing should preserve source semantics rather than create a second resolver or a second authoritative representation.

## Exports

A SQLite export can make the record convenient to query analytically.

The database is still a projection.

The authoritative facts remain in the repository-native source record.
