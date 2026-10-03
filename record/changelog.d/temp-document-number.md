### Fixed

- `luria concretize` no longer writes a second `number:` key when a temporary document already carries a hand-written one such as `number: tmpabcde`. The writer replaced only an empty or numeric value, so it inserted `number: N` above the stale line, and the duplicate key then failed the lint on the trunk. `luria repair` populating a numbered document had the same gap ([#355](https://github.com/dmarx/luria/issues/355)).

### Added

- The lint now reports a `number:` on a temporary document as a violation. The number is assigned at merge ([ADR-049](record/decisions.d/ADR-049.md)), so the field is always wrong there, and the lint catches it on the branch instead of on the trunk after concretize. `luria repair` removes the line ([#355](https://github.com/dmarx/luria/issues/355)).
