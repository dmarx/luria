### Changed

- **Both CLAUDE.mds are maps now, not copies**
  ([ADR-037](record/decisions.d/ADR-037.md), part of
  [#45](https://github.com/dmarx/luria/issues/45)): a short list of links to
  the authoritative docs, the invitation to run `luria --help` for the
  current API, and three one-line ground rules — plus the statement that
  when the file disagrees with the docs or the CLI, the file is the one
  that's wrong. The restated command block and doctrine walkthroughs are
  gone; they had drifted twice in one week, exactly as
  [GP-3](docs/guiding-principles.md#gp-3) predicts for hand-maintained
  copies. The scaffolded `template/CLAUDE.md` gets the same treatment,
  mapping an adopting project instead of this one.

### Removed

- **The Makefile** ([ADR-038](record/decisions.d/ADR-038.md)): its "run what
  CI runs is `make <target>`" doctrine stopped being true when
  [ADR-029](record/decisions.d/ADR-029.md) moved the docs jobs into composite
  actions, leaving one `make test` line wrapping pytest and a set of targets
  that restated CLI one-liners and drifted twice in a week. ci.yml runs
  pytest directly; `luria --help` is the one list of what you can run.

### Added

- **`luria init` speaks up about a kept CLAUDE.md**: it never overwrote
  existing files, but the one file an agent reads first deserved more than a
  silent skip — when CLAUDE.md exists, init now prints a pointer at the
  scaffolded map shape (links + `luria --help`) and suggests asking your
  agent to fold it in. The recommendation goes to stdout, where permission
  isn't needed; the file is never touched.
