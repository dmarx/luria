### Added

- `generated()` in a view template: everything `luria index` writes, each
  with a label and a root-relative path. This repository's `CLAUDE.md`
  uses it, so its "never edit a generated file" list is derived.

### Changed

- `Config.is_generated` is now one question asked of
  `Config.generated()`, the list of what the generator writes, so what
  the fixer and the reference report skip is the same list a template
  prints ([DP-004](record/principles.d/DP-004.md)). Behaviour is unchanged. A test holds that every file
  `luria index` renders is covered by some target.
