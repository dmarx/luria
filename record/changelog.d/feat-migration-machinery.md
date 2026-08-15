### Added

- **`luria migrate`** — execute a migration spec from `record/migrations.d/`,
  renaming a scheme or moving documents between schemes without losing the
  record's memory ([ADR-040](record/decisions.d/ADR-040.md), now Active). Two
  operations:
  - `rename_scheme` rewrites a whole code family, following the scheme's view,
    the remotes that mirror this project, and any extra config files named in
    the spec.
  - `move_doc` relocates one document to another scheme, auto-numbered in the
    target. With `strategy = "supersede"` it *copies* instead: the source stays
    where it is, tombstoned as `Superseded — by <new code>`, and is deliberately
    left out of the rewrite mapping so existing citations keep resolving to the
    original. That is the shape a promotion wants — the old document is still a
    true record of what happened, and only its *output* moved.

  `--dry-run` prints the plan and changes nothing; `--commit` commits and
  appends the migration to `.git-blame-ignore-revs` so blame reads through it.
  The sweep is mapping-driven, never prefix-driven: only enumerated pairs are
  rewritten, foreign composed codes (`SG-DP-4`) are masked because another
  project's namespace is theirs, and the spec file itself is never swept —
  its mapping is written in old spellings on purpose.

- **`luria new migration`** scaffolds a numbered spec, because execution order
  is information: a move can depend on a rename.

- **`luria/aliases.py`** — the alias map that migrations resolve through,
  derived fresh from `formerly:` frontmatter rather than hand-kept. Complements
  the concretization-flavoured alias resolution already in `doc_refs`: that one
  answers for temporary codes, this one for any renamed code.
