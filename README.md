<p align="center">
  <img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg"
       alt="Luria — project memory" width="480">
</p>

# Luria

**A project's memory: decisions, principles, changelog and devlog, kept
honest by lint.**

Projects forget. The reason a module is shaped the way it is lives in a
merged PR nobody rereads; the failed approach gets rediscovered a year
later; the "temporary" workaround outlives the person who wrote it. Luria
gives a repository a *record* — small, plain-markdown files, one per
decision, principle, or observation — and the machinery to keep that record
readable, linked, and true:

- **Filing is cheap.** `luria new` scaffolds the next entry — a decision
  with its number allocated, a devlog entry stamped with the minute, a
  changelog fragment nobody will conflict on.
- **Views are built, never edited.** `luria index` renders the record into
  browsable pages — a decision index with tag pages, a principles document,
  journal books, status reports — and `luria lint` fails when a committed
  view has drifted from its sources.
- **References are checked.** A code like `ADR-012` in prose or a source
  comment is a claim. `luria link --fix` turns it into a working link;
  the lint flags codes that resolve to nothing and citations of decisions
  that are no longer in force.
- **The record can be published.** `luria site` stages the whole thing as a
  static site with backlinks and a local graph, ready for GitHub Pages.

Luria is also its own first user: this repository's record is scaffolded,
generated and linted by the CLI it ships.

<!-- luria:badges -->
[![needs decision: 9](https://img.shields.io/badge/needs%20decision-9-orange)](docs/reports/pending-decisions.md)
[![cited, not in force: 3](https://img.shields.io/badge/cited,%20not%20in%20force-3-orange)](docs/reports/reference-status.md)
<!-- /luria:badges -->

## Install

```
pip install luria
```

Python 3.11+. Two runtime dependencies (PyYAML, fire).

## Sixty seconds

```console
$ luria init --issue-url https://github.com/you/yourproject/issues
$ luria index          # build the generated views
$ luria new --title "Switched the queue to at-least-once delivery"
record/devlog.d/2026/08/22/143005.md
$ luria new adr --title "Consumers must be idempotent"
record/decisions.d/ADR-tmp3kf9x.md
$ luria index && luria lint
luria: docs lint clean
```

Edit the two files it printed, commit, and the record has begun. The
[quickstart](docs/quickstart.md) walks the same path with explanations.

## The shape of it

```
luria.toml            what this record is made of (all keys have defaults)
record/               sources — one small file per entry, written by people
  decisions.d/        ADR-001.md, ADR-002.md, …   (a "scheme")
  principles.d/       DP-001.md, …                (another scheme)
  devlog.d/           2026/08/22/143005.md        (a "journal")
  changelog.d/        one fragment per change     (a "fragment directory")
docs/                 the read surface — prose plus generated views
  decisions/          index + tag pages    (GENERATED)
  design-principles.md  one page, anchored (GENERATED)
  devlog/             monthly books        (GENERATED)
  reports/            status reports       (GENERATED)
CHANGELOG.md          assembled from fragments by `luria collect`
```

None of the names above are hard-coded. Schemes, journals, fragment
directories and remote projects are *families* declared in `luria.toml` —
a record made of RFCs, specs, and an incident log is the same engine with
different tables. See [project memory](docs/project-memory.md) and the generated
[configuration reference](docs/configuration.md).

## Documentation

- [Quickstart](docs/quickstart.md) — from empty repository to linted record.
- [Project memory](docs/project-memory.md) — sources and views, schemes, journals,
  fragments, remotes, statuses, and how references work.
- [CLI reference](docs/cli.md) — every command and flag.
- [Comment directives](docs/directives.md) — acknowledging a finding where
  it happens instead of silencing the check.
- [Adopting Luria](docs/adopting.md) — scaffolding an existing project,
  wiring up CI, publishing the site.
- [Configuration reference](docs/configuration.md) — generated from the
  schema, every key with its default.

And the record itself, dogfooded: [decisions](docs/decisions/README.md) ·
[design principles](docs/design-principles.md) ·
[development log](docs/devlog/README.md) ·
[status reports](docs/reports/pending-decisions.md).

## License

[MIT](LICENSE).
