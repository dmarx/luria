# Docs

- [Design principles](design-principles.md) — standing values, numbered.
- [Decisions](decisions/README.md) — choices, with their alternatives.

Both are **generated** — run `luria index`. Edit the fragments in
`principles/` and `decisions/`, never the assembled pages.

Every other page in this directory must be linked from here; `luria lint` fails
otherwise, because an index that silently stops covering the directory is worse
than no index. Scheme source directories are exempt: a reader opens the view,
not the fragments.
