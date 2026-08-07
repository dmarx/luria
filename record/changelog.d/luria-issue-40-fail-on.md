### Changed

- **Status enforcement is a dial** ([ADR-035](record/decisions.d/ADR-035.md),
  [#40](https://github.com/dmarx/luria/issues/40)), superseding
  [ADR-007](record/decisions.d/ADR-007.md)'s "warnings, never able to fail a
  build": the warn-first posture stays the default, and `[luria.lint]
  fail_on` promotes named warning classes — `retired-citations`,
  `unresolved-codes`, `hand-written-urls`, `stale-directives`,
  `pending-documents`, `unlinted-files` — to lint failures. Only
  unacknowledged rows ever fail, so `inactive-ok:` and its siblings become
  the way to state a deliberate exception to a rule with teeth. An unknown
  class name in `fail_on` is itself a lint error naming the vocabulary. The
  scaffolded `luria.toml` documents the knob.
