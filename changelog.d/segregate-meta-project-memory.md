### Changed

- **Luria's own project memory moved from `docs/` to `meta/`**
  ([ADR-021](meta/decisions/ADR-021.md), [#3](https://github.com/dmarx/luria/issues/3)).
  `docs/` is now what the package documents — doctrine, directives, adopting —
  and `meta/` holds the decisions, principles and development log this project
  accumulated building itself. A visitor meets the scaffold rather than our
  history; nothing about `luria init` changes, and an adopting project still
  keeps everything under `docs/`.
- `README.md`'s badge links are derived from `paths.decisions` instead of the
  hardcoded `docs/decisions/README.md` they defaulted to.

### Added

- **`paths.docs` accepts a list of documentation roots**, each indexed by its
  own `README.md`:

  ```toml
  [luria.paths]
  docs = ["docs", "meta"]
  ```

  The index check runs per root, so one audience's material can't satisfy the
  other's index. The plain string form is unchanged and remains the default.
- A scheme's directory is scanned for bare references on its own account rather
  than by sitting under a documentation root — a scheme configured anywhere
  else was previously invisible to the hyperlink lint.

### Fixed

- A journal's *source* directory is exempt from the docs-index check, like a
  scheme's. It holds entries, not pages to browse, and only became visible to
  that check once the record moved inside a documentation root.
