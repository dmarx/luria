### Added

- `luria repair --prune_stale` removes the codes in `inactive-ok`,
  `unresolved-ok` and `mention-ok` directives that answer for no site, and
  deletes a directive left naming nothing. That includes the directives the
  default repair leaves because their citation may have moved. It re-scans
  after writing and restores every file if any finding changed. Opt-in; the
  default repair is unchanged ([ADR-tmp7ae7n](record/decisions.d/ADR-tmp7ae7n.md), [#385](https://github.com/dmarx/luria/issues/385)).
