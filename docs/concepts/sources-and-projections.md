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

[DP-3](../../record/principles.d/DP-003.md) states Luria's general rule: a projection of an authoritative source should be derived whenever possible.

That is why projections are rebuilt by commands rather than edited:

```console
$ luria index      # scheme indexes and value pages, journal books, chain pages,
                   # status reports, the record and configuration pages
$ luria collect    # fragments into their shared file, such as CHANGELOG.md
$ luria site       # the record staged as a site
$ luria export     # the record as a SQLite file
```

`luria index` covers the committed views; the other three are separate commands with separate outputs. None of them treats its output as a separately authored document. See the [CLI reference](../cli.md).

## Generated views and concurrency

[DP-2](../../record/principles.d/DP-002.md) adds another dimension: when a shared artifact must be generated, the writer belongs where merges serialize, not on every branch.

This prevents “generated but still conflicted” artifacts from becoming a hidden shared-file lock.

## Chain pages

A chain page is a projection of local relation edges.

It intentionally renders history, including inactive or superseded steps. The page itself is not where lineage is authored.

## Sites

`luria site` stages the record for publication as a Quartz vault, under rules that keep it a projection ([ADR-042](../../record/decisions.d/ADR-042.md)):

- **paths are preserved**, so every relative link the fixer wrote keeps resolving and no second link resolver is needed;
- **a source that renders into a view is withheld** and the view is published — a journal entry appears in its book, a fragment in its collected file;
- **a link that leaves the published set goes to the repository** rather than being emitted dead;
- **frontmatter is surfaced**: each document's status and edges are rendered onto its page, so a superseded decision does not read as current on the web.

## Exports

`luria export` writes a SQLite file — documents, field values, typed edges, citations and journal entries — that makes the record convenient to query analytically ([ADR-116](../../record/decisions.d/ADR-116.md)).

The database is still a projection: rebuilt from scratch on every run through the same readers the lint uses, never written back to, and not committed.

The authoritative facts remain in the repository-native source record.
