### Added

- `luria unconcretize CODE [CODE ...]` gives each named document its number back as a fresh temporary code, drops its `number:`, and rewrites every whole occurrence of the code, its lower-case anchor spelling included, wherever `concretize` would. Run it on a branch whose number the trunk took first, before merging the trunk. It also renumbers a run of documents. No `formerly:` is recorded ([ADR-140](record/decisions.d/ADR-140.md)).

### Fixed

- `luria concretize` now rewrites `luria.yaml` too. A temporary code cited in a config comment or blurb used to survive concretization.
