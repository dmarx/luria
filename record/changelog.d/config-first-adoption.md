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

### Changed (review round)

- `luria new` stamps an unnamed fragment with its filing moment
  (`20260812-021035.md`), the identity the devlog already uses, instead of
  naming it after the git branch — which collided the first time a branch
  was restarted after a squash merge and refiled ([ADR-036](record/decisions.d/ADR-036.md), v2). `--name`
  remains the explicit override and still reopens rather than duplicates.
- Generated views are marked `linguist-generated` in `.gitattributes`, so
  PR review collapses them by default and a contribution's diff reads as
  its sources. The views stay committed; only review's rendering changes.

### Proposed

- [ADR-049](record/decisions.d/ADR-049.md): schemes gain an `allocate = "merge"` mode — `luria new` issues a
  temporary code (`ADR-tmp47fje`) that is first-class on its branch, and
  `luria concretize`, run where merges serialize, assigns real numbers in
  merge order and records the temporary code as a permanent `aka:` alias.
  Filed from the review discussion on [#76](https://github.com/dmarx/luria/issues/76); implementation to follow in its
  own PR.
