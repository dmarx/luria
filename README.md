<p align="center">
  <img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg"
       alt="Luria — project memory" width="480">
</p>

# Luria

**A record of what your project knows — and of what it no longer believes.**

Projects forget, and they forget *silently*. The wiki still renders. The
decisions folder still has files in it. The status column still exists. Nothing
announces that a convention drifted, that a rationale expired, or that the
reasoning behind a constraint now points at a document somebody deleted.

A Luria record makes those questions answerable, because every entry in it has:

- **A name something can cite.** `ADR-012`, `RFC-7` — in prose, in a commit,
  in a source comment. `luria link --fix` turns the bare code into a working
  link; the lint reports codes that resolve to nothing, so a reference is a
  claim that gets checked rather than a string that gets stale.
- **A standing.** In force, proposed, superseded, rejected. Retiring something
  is an edit to its status, never a deletion — so the record keeps what it
  stopped believing, and can tell you when a live document is still citing it.
- **Rules you declare instead of hope for.** Required fields, exactly one
  primary category, what each status means *in this scheme*. The conventions
  you would otherwise write in CONTRIBUTING become things that fail. Luria will
  even tell you when a field has stopped carrying information — which is what a
  status column looks like a year after anyone maintained it.
- **A view that is generated.** Indexes, tag pages, journal books, status
  reports. Built by `luria index`, never hand-edited, so what people read
  cannot drift from what people file.

Filing is cheap — `luria new` scaffolds the next entry with its identity
already assigned — and the whole record publishes as a static site with
backlinks and a local graph (`luria site`).

Luria is also its own first user: this repository's record is scaffolded,
generated and linted by the CLI it ships.

<!-- luria:badges -->
[![needs decision: 1](https://img.shields.io/badge/needs%20decision-1-orange)](docs/reports/pending-decisions.md)
[![cited, not in force: 1](https://img.shields.io/badge/cited,%20not%20in%20force-1-orange)](docs/reports/reference-status.md)
<!-- /luria:badges -->

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

## A note on files

A record is kept as plain text in your repository, one entry per file, and
that is a deliberate implementation choice rather than the product. It is
chosen for *participation*: a contributor — or a coding agent — edits a file,
opens a pull request, and greps the result, with no application to run, no
database to migrate, and no export to negotiate when they want their history
back.

Markdown is what that looks like today and will likely stay the primary shape.
Nothing in the model above depends on it. Identity, standing, declared rules
and generated views are claims about a record, not about a file format.

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
