### Changed

- A journal's books are rendered from a template luria ships,
  `luria:journal-book.md.j2` (with its section and heading markup in
  `luria:journal-book-parts.md.j2`), instead of markup in Python. This is
  the first step of [ADR-tmpg4gc4](record/decisions.d/ADR-tmpg4gc4.md). The output is byte-identical to before on
  luria's, nucleation's, strata-g's and mantle's journals.
- luria's own templates are compiled once per process (`views.shipped`).
