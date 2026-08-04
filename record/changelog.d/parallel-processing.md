### Added

- **Parallel execution** ([ADR-026](record/decisions.d/ADR-026.md),
  [#7](https://github.com/dmarx/luria/issues/7)): one ordered `pmap` over a
  thread pool, applied at three seams — render units in `luria index`
  (a scheme, a journal), per-file scans in the bare-reference lint, and
  per-URL probes in `luria remotes --check`. Results keep input order, so
  reports and rendered views are byte-identical at any width.
  `LURIA_JOBS=1` forces serial execution; `LURIA_JOBS=N` caps the pool.
  Measured: `remotes --check` 6.6s → 2.9s on this repo's citations; index
  and lint unchanged at today's cardinality (the seams there are structure
  for growth, as the issue asked).
