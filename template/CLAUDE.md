# CLAUDE.md

**Before anything else, read
[the design principles](docs/design-principles.md) in full.** They are the
standing values every choice in this project is judged against; the rest of
this file, and the record itself, assume you hold them. Read them
immediately after finishing this file, before any other code or
documentation in this repository.

This project keeps its memory in a Luria record — decisions, principles, a
changelog and a devlog — scaffolded, generated and linted by the `luria`
CLI. This file is a map, not a copy
([LU-ADR-037](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-037.md)):
the doctrine lives one link away and the current command surface lives in
`luria --help`. When this file disagrees with either, this file is the one
that's wrong.

- **Run `luria --help`** for what the CLI does today; every command takes
  `--help`.
- [This project's docs](docs/README.md) — the generated views: the decision
  record, the principles, the devlog books, the status reports.
- [Project memory: how a repo thinks](https://github.com/dmarx/luria/blob/main/docs/project-memory.md)
  — the doctrine behind the layout: the four layers, what files where, how
  the record is revised.
- [Comment directives](https://github.com/dmarx/luria/blob/main/docs/directives.md)
  — the acknowledgement vocabulary (`inactive-ok:` and friends), wikilinks,
  and fixture codes.
- [Configuration](https://github.com/dmarx/luria/blob/main/docs/configuration.md)
  — every `luria.toml` key, generated from Luria's own schema. Read this
  before assuming the record can only hold decisions: schemes, fragment
  directories, journals and remotes are families this project names, and
  `luria.toml` is where its shape is decided.

Four ground rules, terse enough to restate:

- **Work goes to a branch and a pull request, never straight to the default
  branch** — the record is the deliverable, and it needs a chance to be read
  before it becomes what the project believes.
- **File the fragment in the same contribution as the work** (`luria new`):
  a fact filed while its context is loaded costs a paragraph; re-derived
  cold, it costs a session.
- **Never hand-write a link target.** Write the bare code and let `luria
  link --fix` spell the target: record prose is rendered into views in
  *other directories*, so a target has to resolve from where the text
  lands, not where it lives — only the fixer knows that frame. Want prose
  as the label? That's `[[ADR-001|a labeled wikilink]]`, still the fixer's
  job. A hand-written target that looks right here is wrong somewhere.
- **A guard that keeps catching you is a bug report about the workflow.**
  One catch is the net working; the same catch again means the hazard is
  upstream — a practice, a missing affordance, an undocumented rule — and
  the fix is to remove what *generates* the mistake, not to keep thanking
  the net. Quiet guards are the goal; a busy one is compensating for
  something.
