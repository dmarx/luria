### Changed

- **`origin:` is prose, like `summary:`** — references written there are linked
  by `luria link --fix` and checked by the lint. It was already *rendered* as
  markdown into a principle's metadata line, so a hand-written link displayed
  correctly while nothing maintained it: the worst of both, and a rot with no
  alarm. The reference machinery now reads a `PROSE_KEYS` set instead of naming
  `summary` in four places, and the membership rule is stated — a key is prose
  exactly when the generator renders its value as markdown. Deliberately not
  configurable: a project cannot make a field prose by declaring it so.
