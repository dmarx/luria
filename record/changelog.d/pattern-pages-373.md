### Added

- **A path pattern can render a page of its matches** ([#373](https://github.com/dmarx/luria/issues/373)). Give a pattern
  an `output:`, and optionally a `title:`, and `luria index` writes one row
  per match there, one column per named node, each its document's code and
  title.
  - Any pattern renders, including ones a chain cannot walk: a single node
    with `WHERE NOT`, such as theses nothing objects to, or a path across
    schemes, such as arguments an Active claim undercuts.
  - The page is a view luria supplies, so `luria index --check` holds it
    fresh and the reference scan skips it, like any other view.
  - It is a list, never a lint finding. `report: true` still makes matches
    a warning class, a pattern may have both, and an acknowledged match
    stays on the page.
- `examples/argument-map` lists its unfinished steps on such a page.
- A view template may use the `cell` filter to escape `|` in a table cell.

### Changed

- Two renderers writing one path are refused at load, naming both: schemes,
  status reports, chains, views and pattern pages alike. Before, a chain or
  a view could silently overwrite another page.
- `match` in a view template lists two matches that differ only in an
  anonymous node once, since its rows cannot tell them apart.
