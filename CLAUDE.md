# CLAUDE.md

Luria is the machinery *and* a project that uses it: this record is
scaffolded, generated and linted by its own CLI. This file is a map, not a
copy ([ADR-037](record/decisions.d/ADR-037.md)) — the doctrine lives in the
docs and the current command surface lives in `luria --help`. When this file
disagrees with either, this file is the one that's wrong.

- **Run `luria --help`** for what the CLI does today; every command takes
  `--help`.
- [Project memory: how a repo thinks](docs/project-memory.md) — the doctrine:
  the four layers, what files where, how the record is revised. Start here.
- [Design principles](docs/design-principles.md) — the standing values,
  cited as "DP-2".
- [The decision record](docs/decisions/README.md) — every choice, its
  alternatives, its status.
- [Comment directives](docs/directives.md) — the acknowledgement vocabulary,
  wikilinks, and fixture codes.
- [Status reports](docs/reports/pending-decisions.md) — what awaits a
  decision, and [what still cites a retired one](docs/reports/reference-status.md).
- [Adopting Luria](docs/adopting.md) — putting the record into another
  project.

Three ground rules, terse enough to restate:

- **Work goes to a branch and a pull request, never straight to `main`** —
  the record is the deliverable, and it needs a chance to be read before it
  becomes what the project believes.
- **File the fragment in the same contribution as the work** (`luria new`):
  a fact filed while its context is loaded costs a paragraph; re-derived
  cold, it costs a session.
- **Every reference is a hyperlink.** Don't hand-write them — `luria link
  --fix` writes exactly what the lint demands, and `[[BRACKETS]]` force one
  the heuristics would pass over.

Working on the package itself: `python -m pytest tests -q` plus `luria lint`
is what CI runs; a new check joins the lint only if the violation is always
wrong and mechanically fixable, otherwise it is a report
([ADR-035](record/decisions.d/ADR-035.md)); and fire any new guard once
before trusting it, saying so in the devlog
([DP-6](docs/design-principles.md#dp-6)).
