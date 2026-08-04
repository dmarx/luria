### Changed

- **The repository layout now states the read/write boundary**
  ([ADR-021](record/decisions.d/ADR-021.md),
  [#3](https://github.com/dmarx/luria/issues/3)): `docs/` holds everything a
  reader browses — prose plus every generated view — and `record/` holds
  everything a contributor files, each container inside carrying the `.d`
  suffix (`record/decisions.d/`, `record/principles.d/`,
  `record/changelog.d/`, `record/devlog.d/`). What you read at `docs/X` you
  file at `record/X.d`. `CHANGELOG.md` stays at the root, where convention
  puts it.
- A scheme's `output` is now separate from its source `dir`: the decision
  index and its tag pages render into `docs/decisions/` while the ADR files
  stay in `record/decisions.d/`, with link rebasing derived from the actual
  paths. A scheme with no `output` keeps the old collocated layout unchanged,
  so existing projects upgrade without moving anything.
- `README.stub` and `tags.yaml` live with the sources; a stub's links resolve
  from where the index renders.
- The journal's front page now inlines the current book's contents, newest
  entry first, above the shelf of older books — the newest writing is one
  click from the entrypoint instead of two.
- `luria init` scaffolds the new layout; the template's `docs/README.md` and
  `CLAUDE.md` explain the boundary.

### Added

- **A view directory holds only what the generator wrote** — anything else in
  one is a lint violation naming the file and the remedy. This generalizes the
  old orphaned-tag-page check to every view directory, and also catches a
  journal book stranded by a granularity change.
- [DP-9](docs/design-principles.md#dp-9) — structure is read before text, so
  affordances are spent deliberately: on shaping attention, on making
  locations discoverable, and as smells to read when they turn inconsistent.
  A structural signal beats a documentary one; the read/write boundary is the
  worked application.

- A new comment directive, `url-ok` — a link whose label is a composed
  foreign code (`SG-DP-18`) but whose URL is hand-written rather than
  constructed is reported as a warning until acknowledged, because a hand URL
  is frozen at writing time. Same shape and scope rules as every other
  directive; stale acknowledgements report themselves.

### Fixed

- The README badges' link target is derived from configuration instead of a
  hardcoded `docs/decisions/README.md`.
