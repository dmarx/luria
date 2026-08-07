### Added

- **`luria new [kind]` scaffolds an entry anywhere the record takes one**
  ([ADR-036](record/decisions.d/ADR-036.md),
  [#42](https://github.com/dmarx/luria/issues/42)): the journal by default,
  any configured scheme by prefix (`luria new adr` copies `_template.md` to
  the next free number and stamps the date), any fragment directory by name
  (`luria new changelog` names the file after the branch). It computes only
  what a machine can know, prints the path, and leaves the content to a
  markdown-aware editor; `--title`/`--status`/`--summary`/`--tags` exist for
  tools driving the CLI, never as requirements. Kinds derive from
  `luria.toml`, so a new scheme scaffolds for free. This fragment and its
  devlog entry were created with it.

### Removed

- **`luria journal`** — subsumed by `luria new` and removed without a shim
  ([ADR-030](record/decisions.d/ADR-030.md)); `python -m luria.journal`
  remains for the interactive look at what is filed.
