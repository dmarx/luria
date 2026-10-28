### Added

- **Patterns can share a page.** Patterns naming the same `output:` render
  one outline of all their matches, merged by position. A claim, its
  arguments and their undercutters can be drawn at fixed depth from two
  patterns, `(c)<-[:concludes]-(g)` and `(c)<-[:concludes]-(g)<-[:undercuts]-(u)`,
  and an argument nothing undercuts is still listed.
- `facet_by` on a pattern with a page, as on a chain (default `[status]`).
- `layout: table` keeps the flat table, one row per match.

### Changed

- **A pattern page is an outline by default.** Matches nest by shared
  prefix, and each node is written as a chain step,
  `- [CODE](link) — title *(facets)*`, by the same renderer chain pages use.
  Chain pages are unchanged.
- `examples/argument-map` outlines its unfinished steps and adds a page of
  steps and the objections to them.
