# Docs

{views}

Each of these is **generated** — run `luria index`. The list above is
[written by `luria init` from this project's own
`luria.toml`](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-048.md),
so it names the views this record actually renders; edit it freely
afterwards, it is yours. This directory is for
*reading*; filing happens in `record/`, whose `.d`-suffixed containers hold
the sources ([LU-ADR-021](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-021.md)).
Never edit an assembled page — the lint refuses hand edits, and anything in a
view directory the generator didn't write is an error.

Every other page in this directory must be linked from here; `luria lint`
fails otherwise, because an index that silently stops covering the directory
is worse than no index. View directories are exempt: they carry their own
generated indexes.
