### Changed

- **A declared family replaces the shipped default** ([ADR-047](record/decisions.d/ADR-047.md)). `schemes`,
  `fragments`, `journals` and `remotes` are now yours entirely the moment
  you declare them: a record of RFCs and specs has no phantom ADR scheme,
  and a declared scheme's omitted `output` is genuinely unset — the view
  renders beside its sources, as the docs always said it would. Settings
  tables (`paths`, `code`, `lint`, `site`) still merge per key.

**Upgrading:** a config that declared *part* of a family while relying on
the rest from the defaults — say `[luria.schemes.DP]` alone, expecting `ADR`
to persist — now owns the family it declared. Add the missing entries
explicitly; the shipped template always declared its families in full, so
records scaffolded by `luria init` are unaffected.

### Added

- **`luria init --config my.toml`** ([ADR-048](record/decisions.d/ADR-048.md)): write the `luria.toml` you
  want and init installs it and scaffolds exactly that shape — a directory,
  template and view stub per scheme, templates per journal and fragment
  directory, and a docs index listing the views your record actually
  renders. A project that already has a `luria.toml` now gets *its* shape
  scaffolded rather than the template's. `--config` against a project that
  already has one is a hard error, never a silent skip.

### Fixed

- An index-rendered scheme with no `README.stub` is titled after itself
  rather than `# Architecture decision records` — the same defect the
  document render had, fixed the same way.
- A fresh `luria init` → `luria index` → `luria lint` runs clean again: two
  bare references in the template (`LU-ADR-048` in the docs index prose,
  `DP-1` in the principles stub) became visible to the scheme-driven
  reference detection and would have made every new scaffold start red. The
  three-command adoption loop is now a CI-run test, so the class stays
  closed.
