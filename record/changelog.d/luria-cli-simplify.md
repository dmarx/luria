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
  ([ADR-007](record/decisions.d/ADR-007.md), corrected to v2). A retired name
  exits 2 naming its successor rather than "unknown command"
  ([DP-1](docs/design-principles.md#dp-1)), and the modules keep their entry
  points — `python -m luria.ref_status --all` is still the interactive dig.
  The `ref-status` and `pending` make targets are gone with them.
