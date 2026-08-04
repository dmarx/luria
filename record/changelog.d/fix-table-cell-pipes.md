### Fixed

- A literal `|` in a decision's `summary:` (or status note) no longer breaks its
  row in the generated index and tag pages — the renderer escapes cell content,
  and normalises an author's hand-escaped `\|` rather than double-escaping it
  ([#14](https://github.com/dmarx/luria/issues/14)).
