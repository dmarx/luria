### Added

- `luria export`'s `citations` table has a `standing` column, which is one
  of `in-force`, `acknowledged`, `sanctioned`, `unacknowledged` or
  `dangling`. It also has an `excused_by` column, which names the directive
  (`inactive-ok @ path:line`) or the `lint.inactive_ok[N]` rule that clears
  the site ([ADR-tmptj3j3](record/decisions.d/ADR-tmptj3j3.md)).

### Changed

- The export's `excused` column is 1 when a directive or a
  `lint.inactive_ok` rule clears the site. Before, it counted directives
  only, so a sanctioned citation exported 0 and looked like a warning.
