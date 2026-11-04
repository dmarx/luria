### Added

- `luria repair --prune_stale` removes the codes in `inactive-ok`,
  `unresolved-ok` and `mention-ok` directives that answer for no site, and
  deletes a directive left naming nothing. That includes the directives the
  default repair leaves because their citation may have moved. It re-scans
  after writing and restores every file if any finding changed. Opt-in; the
  default repair is unchanged ([ADR-138](record/decisions.d/ADR-138.md), [#385](https://github.com/dmarx/luria/issues/385)).
- A `repair:` table in `luria.yaml` sets the standing value of every `luria
  repair` flag, so the CI repair uses it without the workflow passing it.
  All off by default; the command line overrides a key for one run. An
  unknown key or a non-boolean value is refused when the config loads.
