### Added

- **Luria: the project-memory machinery, extracted from
  [strata-g](https://github.com/dmarx/strata-g) as a reusable package.** The four
  layers ([ADR-001](record/decisions.d/ADR-001.md)), the
  fragment convention ([ADR-002](record/decisions.d/ADR-002.md)),
  the generated decision index
  ([ADR-004](record/decisions.d/ADR-004.md)), the
  reference-hyperlink lint
  ([ADR-005](record/decisions.d/ADR-005.md)), the
  retired-document and pending-decision reports
  ([ADR-007](record/decisions.d/ADR-007.md)), and the
  `inactive-ok` / `unexempt` directive vocabulary
  ([ADR-008](record/decisions.d/ADR-008.md)).
- **`luria` CLI** — `lint`, `link`, `index`, `ref-status`, `pending`, `reports`,
  `collect`, `init`. `luria lint` is the only one that can fail.
- **`luria init`** scaffolds the record into a project that has none, and never
  overwrites: a scaffolder that clobbers is one nobody dares re-run.
- **Everything project-specific is configuration**
  ([ADR-006](record/decisions.d/ADR-006.md)): paths,
  issue URL, code globs, fragment directories, and reference schemes. A second
  scheme (RFC, SPEC) is a `luria.toml` entry and a directory.

### Documentation

- **The name.** The package was very nearly `chester`, after Chesterton's Fence;
  [ADR-010](record/decisions.d/ADR-010.md) records that
  reasoning and [ADR-011](record/decisions.d/ADR-011.md)
  supersedes it — Luria, after *The Mind of a Mnemonist*, because the name should
  point at the faculty rather than at one failure it prevents, and because the
  book's cautionary half (a memory that never forgets and never abstracts becomes
  unusable) is the design brief.
