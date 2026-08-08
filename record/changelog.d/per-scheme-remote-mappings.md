### Added

- **Per-scheme remote mappings**
  ([ADR-023](record/decisions.d/ADR-023.md),
  [#6](https://github.com/dmarx/luria/issues/6)): a remote's code families
  construct independently via `[luria.remotes.X.schemes.Y]` — `dir` for
  file-per-code schemes, `document` plus an `anchor` template for schemes
  whose documents are sections of one assembled page, or a `url` template.
  The anchor defaults to the stable shape Luria's document render emits
  (`dp-{number}`), so a remote on current conventions needs one `document`
  line: `SG-DP-18` now constructs to
  `…/docs/guiding-principles.md#dp-18` instead of a URL to a file that never
  existed.
- `luria remotes` labels which construction answered per code — "a document
  anchor, per the scheme" — alongside the existing rung labels.
- **uid remotes** ([ADR-024](record/decisions.d/ADR-024.md)): a remote can
  declare its references' shape outright — a `uid` regex, a configurable
  `delim`, and a `url` template that indexes the uid's capture groups by
  position — so `ARXIV-2403.05530` linkifies, lints and `url-ok`s like any
  foreign code. A uid is exact (never zero-padded), has exactly one
  resolution rung (the template; no lockfile, no convention), and an
  unconfigured prefix still never matches.

### Changed

- The lockfile's authority is scoped to what discovery can see: files. A
  document-scheme code absent from the lockfile still constructs — a section
  never appears in a directory listing, so its absence there is not evidence
  ([ADR-016](record/decisions.d/ADR-016.md) unchanged for file-per-code
  codes).
- The remote-level `dir` default moves from `docs/decisions` to
  `record/decisions.d`, following the read/write boundary
  ([ADR-021](record/decisions.d/ADR-021.md)) — defaults mirror Luria's own
  conventions. Remotes with an explicit `dir` are unaffected.
- The `url-ok` acknowledging `SG-DP-18` narrows to its residue: the
  construction now reaches the right document, and the annotation excuses
  only strata-g's legacy heading-derived anchor — the retirement loop
  [ADR-022](record/decisions.d/ADR-022.md) designed, exercised in tests in
  both directions.
