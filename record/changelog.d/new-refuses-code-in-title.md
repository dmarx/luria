### Changed

- `luria new` refuses a `--title` that cites a code, which the repair would
  link in the heading and not in `title:`, so the lint would fail after the
  first repair ([ADR-143](record/decisions.d/ADR-143.md)). A code in backticks is a mention and passes.
