### Added

- A scheme may name where its tag vocabulary lives — `tags = "record/topics.yaml"` —
  so two schemes can share one file instead of keeping a copy each.
- A tag may declare `primary_for: [LIT, SOTA]`, and a `tag_groups` entry that
  lists no tags derives its membership from those keys. One vocabulary file
  can now give two schemes different primaries without repeating the shared
  part.
- `[luria.schemes.X.references]` declares that a frontmatter field holds a
  code from a named scheme. Where `requires` checked only that a field was
  truthy, a declared reference checks that it is present, is a code, belongs
  to that scheme, and resolves.

### Changed

- A scheme's `_template.md` is no longer scanned for code references. It is a
  form the tool reads, not an entry in the record, so its example codes were
  reported as citations — a template with a realistic example produced a
  finding against itself. Link targets in templates are still checked.

### Fixed

- Nothing yet broken by this; all three additions are inert until declared.
