### Fixed

- **`luria migrate`'s relink pass now stops where the hyperlink lint stops**
  ([#90](https://github.com/dmarx/luria/issues/90)). It walked every tracked
  file and linkified what it found there, while `luria link --fix` walks
  `doc_files()` — the fixer running wider than the linter checks, which is the
  disagreement `doc_refs` exists to prevent. The first real `move_doc`
  migration turned two moved documents into a 499-file working tree, 469 of
  them exactly `HEAD` plus markdown links written into Python comments,
  TypeScript comments and workflow YAML. The *sweep* still walks every tracked
  file, and should: "does this text spell a code that moved?" is a question a
  `.py` comment answers as truthfully as a document does. Only the linking half
  was scoped wrong.
- **A worded citation in a source file follows the move too.**
  [#89](https://github.com/dmarx/luria/pull/89) caught the prose-labelled form
  by the *address* it points at — which works in a document, where the citation
  is a link, and misses it entirely in code, where `(design-principles #17)` is
  normally unlinked: no code for the code swap, no address for the address
  swap. Eight of them survived the strata-g promotion, naming a document that
  had moved. The sweep now respells them using `find_refs`, the same recognizer
  that would have turned the phrase into a link in the first place, so the two
  cannot disagree about what counts as a reference.
- **A `formerly:` stamp is no longer reported as a dangling reference.** The
  reference scan is deliberately unmasked, so it read the alias the move had
  just written and reported `DP-017 resolves to no document` against the file
  the migration had created — one warning per moved document, every time, for
  the one construct whose entire purpose is to name a code that resolves to
  nothing. `sweep_text` already excluded `formerly:` blocks for the mirror
  reason (a later migration must not rewrite an earlier one's trail); the two
  exclusions now share `doc_refs.FORMERLY_RE`, because they are one exclusion.
