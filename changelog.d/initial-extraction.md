### Added

- **Luria: the project-memory machinery, extracted from
  [strata-g](https://github.com/dmarx/strata-g) as a reusable package.** The four
  layers ([ADR-001](docs/decisions/adr-001-four-layers-of-record.md)), the
  fragment convention ([ADR-002](docs/decisions/adr-002-fragments-and-generated-views.md)),
  the generated decision index
  ([ADR-004](docs/decisions/adr-004-generated-decision-index.md)), the
  reference-hyperlink lint
  ([ADR-005](docs/decisions/adr-005-references-are-hyperlinks.md)), the
  retired-document and pending-decision reports
  ([ADR-007](docs/decisions/adr-007-status-is-reported-not-enforced.md)), and the
  `inactive-ok` / `unexempt` directive vocabulary
  ([ADR-008](docs/decisions/adr-008-directive-vocabulary.md)).
- **`luria` CLI** — `lint`, `link`, `index`, `ref-status`, `pending`, `reports`,
  `collect`, `init`. `luria lint` is the only one that can fail.
- **`luria init`** scaffolds the record into a project that has none, and never
  overwrites: a scaffolder that clobbers is one nobody dares re-run.
- **Everything project-specific is configuration**
  ([ADR-006](docs/decisions/adr-006-reference-schemes-are-configured.md)): paths,
  issue URL, code globs, fragment directories, and reference schemes. A second
  scheme (RFC, SPEC) is a `luria.toml` entry and a directory.

### Documentation

- **The name.** The package was very nearly `chester`, after Chesterton's Fence;
  [ADR-010](docs/decisions/adr-010-name-the-project-chester.md) records that
  reasoning and [ADR-011](docs/decisions/adr-011-name-the-project-luria.md)
  supersedes it — Luria, after *The Mind of a Mnemonist*, because the name should
  point at the faculty rather than at one failure it prevents, and because the
  book's cautionary half (a memory that never forgets and never abstracts becomes
  unusable) is the design brief.
