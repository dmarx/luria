# CLAUDE.md

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

Three ground rules, terse enough to restate:

- **Work goes to a branch and a pull request, never straight to the default
  branch** — the record is the deliverable, and it needs a chance to be read
  before it becomes what the project believes.
- **File the fragment in the same contribution as the work** (`luria new`):
  a fact filed while its context is loaded costs a paragraph; re-derived
  cold, it costs a session.
- **Every reference is a hyperlink.** Don't hand-write them — `luria link
  --fix` writes exactly what the lint demands, and `[[BRACKETS]]` force one
  the heuristics would pass over.
