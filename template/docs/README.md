# Docs

- [Design principles](design-principles.md) — standing values, numbered.
- [Decisions](decisions/README.md) — choices, with their alternatives.
- [Development log](devlog/README.md) — the narrative, one book per month.

All three are **generated** — run `luria index`. Edit the sources in
`principles/`, `decisions/` and `devlog.d/`, never the assembled pages.

Every other page in this directory must be linked from here; `luria lint` fails
otherwise, because an index that silently stops covering the directory is worse
than no index. Scheme source directories and journal outputs are exempt: a
reader opens the view, not the sources, and a journal's own index covers its
books.
