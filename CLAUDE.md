# CLAUDE.md

**Before anything else, read
[the design principles](docs/design-principles.md) in full.** They are the
standing values every choice in this repo is judged against; the rest of
this file, and the record itself, assume you hold them. Read them
immediately after finishing this file, before any other code or
documentation in this repository.

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

Four ground rules, terse enough to restate:

- **Work goes to a branch and a pull request, never straight to `main`** —
  the record is the deliverable, and it needs a chance to be read before it
  becomes what the project believes.
- **File the fragment in the same contribution as the work** (`luria new`):
  a fact filed while its context is loaded costs a paragraph; re-derived
  cold, it costs a session.
- **Never hand-write a link target.** Write the bare code (`ADR-035`,
  `DP-6`, `#57`) and let `luria link --fix` spell the target: record prose
  is rendered into views in *other directories*, so a target has to resolve
  from where the text lands, not where it lives — only the fixer knows that
  frame. Want prose as the label? That's `[[ADR-035|the escalation
  ladder]]`, still the fixer's job. A hand-written target that looks right
  here is wrong somewhere.
- **A guard that keeps catching you is a bug report about the workflow.**
  One catch is the net working; the same catch again means the hazard is
  upstream — a practice, a missing affordance, an undocumented rule — and
  the fix is to remove what *generates* the mistake, not to keep thanking
  the net ([DP-5](docs/design-principles.md#dp-5): a repeated correction is
  the signal to walk the norm up a rung). Quiet guards are the goal; a busy
  one is compensating for something.

Working on the package itself: `python -m pytest tests -q` plus `luria lint`
is what CI runs; a new check joins the lint only if the violation is always
wrong and mechanically fixable, otherwise it is a report
([ADR-035](record/decisions.d/ADR-035.md)); and fire any new guard once
before trusting it, saying so in the devlog
([DP-6](docs/design-principles.md#dp-6)).
