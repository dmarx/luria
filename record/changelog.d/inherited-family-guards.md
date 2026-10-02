### Fixed

- `luria collect` no longer consumes a fragment directory `luria.yaml` never declared. With no `fragments:` block it refuses to delete files in the shipped default `record/changelog.d`, and names the lines to add ([#136](https://github.com/dmarx/luria/issues/136), [ADR-tmpky7q2](record/decisions.d/ADR-tmpky7q2.md)).

### Changed

- `docs/record.md` labels a schemes, journals or fragments table that comes from Luria's shipped default rather than `luria.yaml`, and says that `<family>: {}` declares none ([#136](https://github.com/dmarx/luria/issues/136)).
