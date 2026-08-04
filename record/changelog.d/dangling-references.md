### Added

- **A cited code that names no document is now reported** rather than silently
  dropped ([ADR-014](record/decisions.d/ADR-014.md)). It shows up in `luria lint`,
  `luria ref-status` and the CI artifact. A warning, never an error — a typo,
  another project's decision and an illustrative code look identical to a
  scanner, and only a human can tell them apart.
- **`unresolved-ok:`** retires a deliberate one, at the same three scopes as
  `inactive-ok:` and with the validity check inverted: it is malformed when it
  names a code that *does* resolve. Both counts are printed on a clean run, so
  "nothing to report" can never mean "everything was silenced".
- **Badges** on the README: CI status, Python version, licence, and links to
  the two generated views. Plus the `LICENSE` file `pyproject.toml` has been
  claiming all along.

### Fixed

- **Ten stale references to the ancestor project's numbering**, left in ported
  docstrings — `ADR-187`, `ADR-188`, `ADR-123` and `ADR-158` each cited a
  decision that says the right thing in the wrong repo. One was a *link* to
  `adr-123-adr-status-vocabulary-docs-lint.md`, a file that has never existed
  here; the reference lint skipped it because it was already a link. All found
  by the new report on its first run.
- **A code inside a URL is no longer read as a citation.** Linking out to
  another project's decision is the correct way to name a foreign document, and
  the URL contains its code — without this, the `luria init` template failed
  its own scaffolded lint the moment its comments pointed at Luria's docs.

### Changed

- **`pip install luria` → `pip install git+https://github.com/dmarx/luria`** in
  the README and the adoption guide. The package is not on PyPI, and a README
  that ships a command which 404s is the drift this repo is about.
