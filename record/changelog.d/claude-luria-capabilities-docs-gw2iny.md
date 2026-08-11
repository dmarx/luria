### Added

- `luria index` now renders `docs/configuration.md`, a reference for every
  `luria.toml` key generated from the config dataclasses themselves — prose
  from their docstrings, key tables from `dataclasses.fields()`. A key that
  exists in the schema is a documented row whether or not anyone remembered
  to describe it ([ADR-044](record/decisions.d/ADR-044.md)).

### Documentation

- The docs say what Luria can be configured *into*, not only what it ships
  as. `docs/adopting.md` gains "Shaping the record to your project" — worked
  examples for a second document family, a second journal, collocated views,
  fragment styles, `uid` remotes for citing things that are not Luria records
  (arXiv identifiers, ticket keys), and the `fail_on` enforcement dial.
- The README and the scaffolded `CLAUDE.md` now say plainly that the four
  shipped subsystems are a default rather than the machinery's fixed parts,
  and point at the configuration reference.
- Both documents state a limit rather than leaving it to be discovered:
  adding a scheme costs one table, but renaming one is still a manual pass
  ([ADR-040](record/decisions.d/ADR-040.md)).
