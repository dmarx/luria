# CLAUDE.md

Luria is a CLI that keeps a project's memory — and this repository is its
own first user: the record here is scaffolded, generated, and linted by
the code in `luria/`. This file is a map, not a manual; when it disagrees
with `luria --help` or the docs, it is this file that is wrong.

Orient first:

- **Run `luria --help`** — the live command surface; every command takes
  `--help`.
- [Project memory](docs/project-memory.md) — the model: sources vs. generated views,
  schemes, journals, fragments, remotes, and how references are checked.
- [The record](docs/record.md) — this project's own configuration,
  generated: what kinds of entry exist and what to type to file one.
- [Decisions](docs/decisions/README.md) and
  [design principles](docs/design-principles.md) — why things are the way
  they are. Check here before re-deriving or re-litigating a choice.
- [Comment directives](docs/directives.md) — how to acknowledge a lint
  finding deliberately instead of working around it.

## Working agreements

- **Work goes to a branch and a pull request, never straight to `main`.**
  The record is the deliverable; it needs a chance to be read before it
  becomes what the project believes.
- **File the record entry in the same contribution as the work**
  (`luria new`): a changelog fragment for the change, a devlog entry for
  anything the next person would otherwise rediscover, a decision document
  when a real alternative was rejected. Filed with context loaded it costs
  a paragraph; re-derived cold it costs a session.
- **Never edit a generated file.** Anything stamped `GENERATED` — the
  decision index, tag pages, `docs/design-principles.md`, journal books,
  reports, `docs/record.md`, `docs/configuration.md`, the README badge
  region — is rebuilt by `luria index`. Edit the sources, rerun it.
- **Never hand-write a link target for a code.** Write the bare code and
  run `luria link --fix`; record prose renders into views in other
  directories, so only the fixer knows the frame a target must resolve
  from. Codes in backticks are mentions, not citations, and are left
  alone.
- **A guard that keeps catching you is a bug report about the workflow.**
  One catch is the net working; the same catch twice means the hazard is
  upstream, and the fix is to remove what generates the mistake, not to
  keep thanking the net.

## Developing the package

`python -m pytest tests -q` plus `luria lint` is what CI runs. A new check
joins the lint only if the violation is always wrong and mechanically
fixable; anything needing judgement is a report with an acknowledgement
directive. Fire any new guard once on a real case before trusting it, and
say so in the devlog.
