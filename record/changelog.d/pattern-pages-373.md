### Added

- **A path pattern can render a page of its matches** ([#373](https://github.com/dmarx/luria/issues/373)). Give a pattern
  an `output:`, and optionally a `title:`, and `luria index` writes one row
  per match there, one column per named node, each a link to its document.
  - Any pattern renders, including ones a chain cannot walk: a single node
    with `WHERE NOT`, such as theses nothing objects to, or a path across
    schemes, such as arguments an Active claim undercuts.
  - Rows are sorted. A pattern with no matches says "No matches".
  - The page is a report: it never fails the lint and is not scanned for
    citations.
  - An `output` that another view already renders to is refused at load.
- `examples/argument-map` lists its unfinished steps on such a page.

### Changed

- A pattern with a property map must be folded (`>-`) or quoted in YAML,
  since `{status: 'Active'}` puts `: ` inside the value. The configuration
  reference now says so.
