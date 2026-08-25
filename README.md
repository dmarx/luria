<p align="center">
  <img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg"
       alt="Luria — project memory" width="480">
</p>

# Luria

**Small markdown files that can be cited, carry a status, and are held to
the rules you chose for them.**

Projects forget. The reason a module is shaped the way it is lives in a
merged PR nobody rereads; the failed approach gets rediscovered a year
later; the "temporary" workaround outlives the person who wrote it. Luria
gives a repository a *record* — one small file per entry — and the machinery
to keep that record readable, linked, and true:

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
- **The rules are yours, and they hold.** A scheme can require its own
  fields, demand exactly one primary category, and declare what each status
  means for it. The conventions you would otherwise write in CONTRIBUTING —
  *every entry cites a source*, *pick one category* — become things that
  fail. Luria will even tell you when a field has stopped carrying
  information, which is what a status column looks like after nobody has
  maintained it for a year.
- **The record can be published.** `luria site` stages the whole thing as a
  static site with backlinks and a local graph, ready for GitHub Pages.

Luria is also its own first user: this repository's record is scaffolded,
generated and linted by the CLI it ships.

## It is not only for decisions

`ADR` is not in the code. It is a table in a config file, and so is
everything else: schemes (documents with codes), journals (dated entries
that persist), fragment directories (written now, assembled later), and
remotes (someone else's namespace, cited by prefix). Name the tables and you
have a different record on the same engine.

- **Project memory** — decisions, principles, a changelog, a devlog. The
  default, and what `luria init` writes.
- **A research anthology** — one scheme of papers, another of the practices
  drawn from them, each with its own status so a foundational paper and a
  stale recommendation can disagree; arXiv identifiers linted and linked as
  a `uid` remote.
- **A standards registry** — proposals browsed as an index, the interfaces
  they define concatenated into one page.
- **An operations record** — an incident journal that is never revised
  beside runbooks that are cited by name and go stale.

[Designing a record](docs/modeling.md) is how to work out which of these
your material is.

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
- [Designing a record](docs/modeling.md) — what belongs in one, which family
  fits, when two kinds of entry are two schemes, and what the schema can be
  made to refuse.
- [Project memory](docs/project-memory.md) — sources and views, schemes, journals,
  fragments, remotes, statuses, constraints, and how references work.
- [CLI reference](docs/cli.md) — every command and flag.
- [Comment directives](docs/directives.md) — acknowledging a finding where
  it happens instead of silencing the check.
- [Adopting Luria](docs/adopting.md) — scaffolding an existing project,
  wiring up CI, publishing the site.
- [Importing an existing corpus](docs/importing.md) — when the material
  already exists as data, and what the transform will surface.
- [Configuration reference](docs/configuration.md) — generated from the
  schema, every key with its default.

And the record itself, dogfooded: [decisions](docs/decisions/README.md) ·
[design principles](docs/design-principles.md) ·
[development log](docs/devlog/README.md) ·
[status reports](docs/reports/pending-decisions.md).

## License

[MIT](LICENSE).
