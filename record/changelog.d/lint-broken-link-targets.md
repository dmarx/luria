### Added

- `broken-targets`: every relative markdown link target in record prose is
  resolved from where that prose *renders* — `link_base`, the same authority
  `luria link --fix` uses to write one — and reported when it does not exist.
  A warning by default, nameable in `[luria.lint] fail_on`.
- `target-ok:` acknowledges a target that deliberately resolves to nothing,
  such as a link into a build output that CI writes but does not commit. The
  first directive whose argument is a path rather than a code.

### Fixed

- The scaffolded decisions stub shipped two links that are dead in every
  project `luria init` creates: `[_template.md](_template.md)` and
  `[design-principles.md](../design-principles.md)`, both written relative to
  the stub's own directory rather than to `docs/decisions/`, where it renders.
- The scaffolded decision template wrote its supersession example as a link,
  `[ADR-NNN](ADR-NNN.md)`, so a placeholder read as a citation to a file nobody
  has. It is a code span now, matching the placeholder on the next line.

### Documentation

- `docs/directives.md` gains a `target-ok` section, and says why this one is
  about the path rather than the code every other directive governs.
