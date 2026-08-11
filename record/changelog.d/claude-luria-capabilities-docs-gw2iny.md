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

### Fixed (reference checking)

- **Every configured scheme is now linted and linked, not just `ADR`.**
  Reference detection matched three hardcoded patterns, so a project with an
  `RFC` or `SPEC` scheme got indexes, tag pages and `luria new rfc` — and no
  reference checking at all. `RFC-7` in prose was neither linked nor reported
  ([ADR-046](record/decisions.d/ADR-046.md)).
- The bare `DP-6` spelling is found. `CLAUDE.md` and the scaffolded template
  both tell contributors to write the bare code and let `luria link --fix`
  spell the target; for design principles that had never been true, because
  only the prose spelling (`design principles #6`) was matched. Applying the
  fix linked 38 references in this repository that had accumulated unseen.
- Cross-scheme references resolve in both directions — a file link into an
  index-rendered scheme, an anchor into a document-rendered one, each from
  the base where the citing text renders.

**Upgrading:** references your record has been carrying unchecked will become
violations in one pass. Run `luria link --fix` and read a sample of the diff
rather than trusting it wholesale.
