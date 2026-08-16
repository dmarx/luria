### Added

- **`[luria.schemes.X.tag_groups]`** — a scheme can declare which of its tags
  combine, and `luria lint` enforces it. A group takes `tags`, an optional
  `require` (`any`, `at-most-one`, `exactly-one`), and an optional
  `excluded_by` naming tags that forbid the group. Opt-in per scheme, so a
  record declaring no group is unconstrained. `tags.yaml` has always said what
  a tag *means*; this says which may appear together, for vocabularies that are
  axes rather than piles.
