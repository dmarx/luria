# Docs

- [Design principles](design-principles.md) — standing values, numbered.
- [Decisions](decisions/README.md) — choices, with their alternatives.
- [Development log](devlog/README.md) — the narrative, one book per month.
- [Configuration](configuration.md) — every `luria.toml` key, generated from
  Luria's own schema. Read it before assuming this record can only hold
  decisions: schemes, journals, fragment directories and remotes are families
  *this* project names.

All four are **generated** — run `luria index`. This directory is for
*reading*; filing happens in `record/`, whose `.d`-suffixed containers hold
the sources ([LU-ADR-021](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-021.md)).
Never edit an assembled page — the lint refuses hand edits, and anything in a
view directory the generator didn't write is an error.

Every other page in this directory must be linked from here; `luria lint`
fails otherwise, because an index that silently stops covering the directory
is worse than no index. View directories are exempt: they carry their own
generated indexes.
