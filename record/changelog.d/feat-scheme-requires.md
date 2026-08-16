### Added

- **`requires = [...]` on a scheme** — frontmatter fields it demands beyond the
  standard set. This is what makes a cross-scheme `luria migrate` move safe to
  automate ([ADR-040](record/decisions.d/ADR-040.md)): a document moved into a
  scheme whose template asks for fields the source never had cannot have them
  invented, so the move succeeds and the *lint* fails until a human supplies
  them. The machinery relocates a document; only a person vouches that it
  belongs.
