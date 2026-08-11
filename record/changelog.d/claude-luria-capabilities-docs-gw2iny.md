### Added

- `luria index` now renders `docs/configuration.md`, a reference for every
  `luria.toml` key generated from the config dataclasses themselves — prose
  from their docstrings, key tables from `dataclasses.fields()`. A key that
  exists in the schema is a documented row whether or not anyone remembered
  to describe it ([ADR-044](record/decisions.d/ADR-044.md)).

### Documentation

- The docs say what Luria can be configured *into*, not only what it ships
  as. `docs/adopting.md` gains "Shaping the record to your project" — worked
  examples for a second document family, a second journal, collocated views,
  fragment styles, `uid` remotes for citing things that are not Luria records
  (arXiv identifiers, ticket keys), and the `fail_on` enforcement dial.
- The README and the scaffolded `CLAUDE.md` now say plainly that the four
  shipped subsystems are a default rather than the machinery's fixed parts,
  and point at the configuration reference.
- Both documents state a limit rather than leaving it to be discovered:
  adding a scheme costs one table, but renaming one is still a manual pass
  ([ADR-040](record/decisions.d/ADR-040.md)).

### Added (examples)

- `examples/` holds four complete, working projects — RFCs beside specs, a
  collocated layout, three journals at three granularities, and `uid` remotes
  citing arXiv papers, Jira tickets and CVEs. `tests/test_examples.py` builds
  each one and runs the real `luria index` and `luria lint` against it, so
  these are configurations CI defends rather than prose ([ADR-045](record/decisions.d/ADR-045.md)).

### Fixed

- A `render = "document"` scheme with no `README.stub` no longer emits the
  heading `# Design principles` regardless of its prefix. A SPEC family
  rendered as a document is titled after itself.
- `luria init`'s scaffolded `docs/README.md` now lists the configuration
  reference, so a freshly initialized project passes `luria lint` on the first
  run as the adoption guide promises. An existing project upgrading will see
  one docs-index violation naming the missing entry; adding the line clears
  it.
- Two wrong claims in the new adoption guidance, both caught by building the
  examples: `active` selects from the closed status vocabulary and cannot
  extend it, and omitting `output` does not collocate the shipped `ADR`
  scheme (set it equal to `dir`). Both are now documented accurately and
  pinned by tests.
