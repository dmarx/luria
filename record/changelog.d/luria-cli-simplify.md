### Changed

- **The CLI is a tiered eight commands instead of a flat eleven**
  ([ADR-030](record/decisions.d/ADR-030.md)): six for contributors (`lint`,
  `link`, `index`, `journal`, `remotes`, `init`) and two labelled as CI's
  (`reports`, `collect`) in `luria --help`, the README and the scaffolded
  CLAUDE.md. The surface had been one command per module — the package layout
  projected onto the interface — and three of the names claimed workflows
  nobody had.

### Removed

- **`luria badges`, `luria ref-status`, `luria pending`.** Each was already
  subsumed: `luria index` writes the badges and `luria lint` checks them
  ([ADR-029](record/decisions.d/ADR-029.md)); both status reports print as
  lint warnings and land in full in the `luria reports` artifact
  ([ADR-007](record/decisions.d/ADR-007.md), corrected to v2). Removed
  outright, not deprecated — a name that answers is a name that still
  exists, and there is no workflow to migrate. The modules keep their entry
  points (`python -m luria.ref_status --all` is still the interactive dig),
  and the `ref-status` and `pending` make targets are gone.
