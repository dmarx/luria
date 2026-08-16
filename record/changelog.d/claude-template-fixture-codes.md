### Fixed

- **A scaffolded project no longer starts with dangling references.** Three
  illustrative codes in shipped templates came from the real sequence and
  resolved to nothing in a fresh scaffold (`ADR-049` in two `_template.md`
  files, `ADR-001` in `CLAUDE.md`); they now use the `FX-` fixture prefix.
  Three more in the scaffolded workflows cited Luria's own decisions bare, so
  they read as the adopting project's decisions — they now compose as `LU-`.
  A fresh `init` + `index` + `lint` went from 5 unresolved codes to none.
