### Changed

- **Both CLAUDE.mds are maps now, not copies**
  ([ADR-037](record/decisions.d/ADR-037.md), part of
  [#45](https://github.com/dmarx/luria/issues/45)): a short list of links to
  the authoritative docs, the invitation to run `luria --help` for the
  current API, and three one-line ground rules — plus the statement that
  when the file disagrees with the docs or the CLI, the file is the one
  that's wrong. The restated command block and doctrine walkthroughs are
  gone; they had drifted twice in one week, exactly as
  [DP-3](docs/design-principles.md#dp-3) predicts for hand-maintained
  copies. The scaffolded `template/CLAUDE.md` gets the same treatment,
  mapping an adopting project instead of this one.
