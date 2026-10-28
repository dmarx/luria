### Added

- **A path pattern can render a page of its matches** ([#373](https://github.com/dmarx/luria/issues/373)). Give it an
  `output:`, and optionally a `title:`, and `luria index` writes one row per
  match there, one column per named node, including patterns no chain can
  walk. The page is a view luria supplies and a list, never a lint finding;
  `report: true` still makes a lint class, and a pattern may have both.
- `examples/argument-map` lists its unfinished steps on such a page.

### Changed

- Two renderers writing one path are refused at load, naming both.
- A view's `match` lists matches differing only in an anonymous node once.
