### Changed

- `luria migrate` now carries pinned endorsements through a scheme rename
  ([#135](https://github.com/dmarx/luria/issues/135), [ADR-066](record/decisions.d/ADR-066.md) v2): for each remote claimed via `remotes = [...]`, a pin
  is re-keyed to the new spelling with both hashes intact — the endorsement
  is of content, which a rename does not change, and prune-and-re-endorse
  would have silently vouched for unreviewed upstream drift. The claimed
  remote's discovered filename map is dropped for re-discovery instead (its
  keys and values both spell the old world); `luria remotes --refresh`
  rebuilds it, and upstream's own rename later surfaces as ordinary
  `remote-drift` for review.
