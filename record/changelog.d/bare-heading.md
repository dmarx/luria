### Changed

- A document's H1 may be the title alone, `# Title`, as well as
  `# CODE: Title` ([#405](https://github.com/dmarx/luria/issues/405)). The lint's title check, the index's title fallback,
  the assembled principles document and the site's duplicate-heading drop all
  accept both forms. Only a document's own code is stripped, so a title that
  starts like a code (`# GPT-4: …`) is compared whole.

### Fixed

- Four decisions (ADR-053, ADR-082, ADR-083, ADR-086) kept the scaffold's
  `# ADR-NNN:` placeholder in their heading. The old check stripped any
  code-shaped prefix and passed them; stripping only the document's own code
  found them, and the headings now carry their codes.
- The encoding tests passed their subprocess a scratch HOME, which hid the
  user site-packages. Where dependencies were installed there, `luria init`
  failed on `import jinja2` and the test reported an encoding crash. The
  subprocess now inherits the parent's import path.
