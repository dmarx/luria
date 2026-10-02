### Added

- `forbidden_when` on a field, the mirror of `required_when`. It takes the same one-field condition, and a document carrying the field while the condition holds is a violation. Contradictory declarations are refused at load: always required, a value in both lists, or a field with a `default` ([#191](https://github.com/dmarx/luria/issues/191), [ADR-tmpt3gtr](record/decisions.d/ADR-tmpt3gtr.md)).

### Changed

- The built-in `superseded_by` is now forbidden while `status` is the scheme's `active` word. An in-force document that names its replacement fails `luria lint` in every record, with no config ([#191](https://github.com/dmarx/luria/issues/191)).
