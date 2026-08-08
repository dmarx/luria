### Added

- **A hand-filed journal entry heals itself** ([ADR-031](record/decisions.d/ADR-031.md),
  [#33](https://github.com/dmarx/luria/issues/33)): `luria index` populates an
  empty `created:` from the entry's path — the path is derived from the
  timestamp, so it is the one witness left — and the lint error names that
  remedy instead of asking a human to retype what the tree already states. A
  field that *disagrees* with the path is still an error: two witnesses in
  conflict is a judgement, not a mechanical fix.

### Changed

- **The status reports are committed views, and the README badges land on
  them** ([ADR-032](record/decisions.d/ADR-032.md),
  [#35](https://github.com/dmarx/luria/issues/35)): `luria index` renders
  `docs/reports/pending-decisions.md` and `docs/reports/reference-status.md`
  with every other view, the lint fails when they are stale, and each badge
  links to the report that explains its number. Everything a report names is
  a link — the flagged decision, every citing line, every pending code. The
  reports carry no clock (ages read "open since <date>"), because a committed
  view that embeds today's date goes stale at midnight on every branch at
  once ([GP-2](docs/guiding-principles.md#gp-2)). The default `reports` path
  moves from `build/doc-reports` to `docs/reports`; `luria reports` still
  writes them standalone for the CI artifact.
