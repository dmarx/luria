### Added

- **`narrow-titles`**, a warning class for a title that names one of the
  project's own concrete nouns in a scheme whose documents claim to transfer.
  A principle stated about the artifact it was first noticed on stays true,
  renders, and passes every other check — it simply stops being cited, and
  nothing could see that. Two config surfaces: `[luria.lint] narrow_terms` for
  the project's vocabulary, and `titles_generalize = true` per scheme for the
  opt-in. **Luria ships no vocabulary**, so an adopter who has not configured
  one sees nothing at all — the class is absent, not empty. A word used in
  another sense is acknowledged in-document with `broad-ok:`, through the same
  directive parser as `inactive-ok:`, rather than by shrinking the vocabulary
  and stopping it protecting every other document.

- A principle carried in from strata-g, luria's first consumer: **"It's not
  mine, but I'll pick it up anyway"** — fix the debt you encounter whether or
  not it belongs to the task you came for, bounded by *repair, don't redesign*
  and *say what you picked up*. Added to this record and to the `template/`
  starter set.

### Fixed

- The `DP` scheme now uses `allocate = "merge"`, which the decisions scheme has
  had since [ADR-049](record/decisions.d/ADR-049.md). Without it two concurrent
  branches each took "the next free principle number" and both got the same one
  — a collision that had already happened here. A scheme that renders as a
  document is no less prone to it than one that renders as an index.
