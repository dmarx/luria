### Added

- **`luria repair` removes, from an `inactive-ok`, a code whose document is
  now in force** ([ADR-tmpbu1p0](record/decisions.d/ADR-tmpbu1p0.md)). It keeps the reason and the other codes, and
  deletes the directive only when it names nothing else. It never touches
  `unresolved-ok`, `mention-ok`, `target-ok` or `url-ok`, or a retired code
  that nothing cites any more.

### Changed

- `stale-directives` now reports an Active code in an `inactive-ok` even when
  the directive's other codes still excuse something, and names
  `luria repair` as the fix.
