# CLI reference

One binary, `luria`, dispatching to plain functions. Every command takes
`--help`. Flags are shown GNU-style; the CLI (python-fire) also accepts
`--flag=value` and positional forms.

| command | one line |
|---|---|
| [`luria init`](#luria-init) | scaffold a record into a repository |
| [`luria config`](#luria-config) | write a starting `luria.toml`, without scaffolding |
| [`luria new`](#luria-new) | file a new entry of any configured kind |
| [`luria repair`](#luria-repair) | write every mechanical source repair |
| [`luria index`](#luria-index) | render every generated view |
| [`luria link`](#luria-link) | turn bare codes and wikilinks into links |
| [`luria lint`](#luria-lint) | enforce the record's invariants |
| [`luria reports`](#luria-reports) | write the status reports |
| [`luria collect`](#luria-collect) | assemble fragments into their target |
| [`luria concretize`](#luria-concretize) | give temporary codes real numbers |
| [`luria remotes`](#luria-remotes) | inspect and verify foreign references |
| [`luria migrate`](#luria-migrate) | execute a rename/move spec |
| [`luria site`](#luria-site) | stage the record as a publishable site |

## luria init

```
luria init [INTO] [--issue-url URL] [--schemes S] [--journals J]
           [--config FILE] [--dry-run]
```

Scaffolds the default record — templates, stubs, tag vocabulary, principle
seeds, a docs index, a `CLAUDE.md`, and CI workflows — into `INTO`
(default: the project root, found via `luria.toml`, then `.git`).

- Existing files are **always skipped**, never overwritten; each is
  reported. Re-running on a grown project is safe.
- `--issue-url` seeds `issue_url` in the scaffolded `luria.toml`; append
  `{n}` yourself or let init place it. **Left out, it is inferred from the
  `origin` remote** — `git@github.com:acme/widgets.git` becomes
  `https://github.com/acme/widgets/issues/{n}`, and init says so as it goes.
  That one value also gives `[luria.site]` its title, its Pages URL and the
  base a link falls back to, so a repository with a remote needs no
  configuration at all. GitHub and GitLab are recognised; any other host
  infers nothing, because a wrong issue URL renders a broken link on every
  entry that carries an issue.
- `--schemes` and `--journals` add families to the shipped shape, for a
  project that wants the defaults plus a little:

  ```console
  $ luria init --schemes "RFC,SPEC:document" --journals "incidents:day"
  ```

  Each entry is `NAME` or `NAME:kind` — `index` or `document` for a scheme
  ([which one?](modeling.md#index-or-document)), `year`, `month` or `day` for
  a journal. Paths follow the prefix, so `RFC`
  gives `record/rfcs.d` rendered into `docs/rfcs`; rename them afterwards if
  the family is better called something other than what its codes spell.

  The shorthand is an argument, not a stored format: what it writes is the
  ordinary commented table, so nothing reads it back and the config looks
  like every other project's. It is additive — the template's own ADR and DP
  tables stay, which is what keeps them alive given that a declared family
  replaces the shipped one whole. Removing a default means deleting a table.
- `--config FILE` scaffolds from your own `luria.toml` instead of the
  shipped one — this is how you init a record with no ADR scheme at all,
  rather than one with an extra family. Refused if a `luria.toml` already
  exists (merge by hand instead), as are `--schemes`/`--journals`: where a
  config exists the shape is declared, and a flag should not edit it.
- `--dry-run` prints the plan and writes nothing.

## luria config

```
luria config [INTO] [--schemes S] [--journals J] [--issue-url URL] [--stdout]
```

Writes the `luria.toml` that `luria init` would have written, and stops.

The shorthand covers the two things projects usually vary. A project that also
wants a different directory, a narrowed status vocabulary or a tag group has to
edit the config — and editing it *after* a scaffold means moving directories
the first run already created. This is the order that avoids that:

```console
$ luria config --schemes "RFC,SPEC:document"
luria.toml

Edit it, then `luria init` to scaffold the shape it declares.
$ $EDITOR luria.toml
$ luria init
```

- Takes the same `--schemes`, `--journals` and `--issue-url` as `init`, and
  infers the issue URL from the `origin` remote the same way.
- **Refuses to overwrite.** A config that exists has already started.
- `--stdout` prints instead of writing, which also works where a config
  exists — looking is not writing.

## luria new

```
luria new [KIND] [--title T] [--status S] [--summary S] [--tags a,b] [--name N]
```

Files one new entry and prints its path. `KIND` is any name the project's
`luria.toml` gives the machinery, lower-cased:

- a **scheme** prefix (`adr`, `rfc`, …) — scaffolds the next document from
  the scheme's `_template.md`, with the number allocated (or a temporary
  code minted, if the scheme allocates on merge) and today's date stamped;
- a **journal** name (`devlog`, `incidents`, …) — creates
  `dir/yyyy/mm/dd/hhmmss.md` stamped with the current time;
- a **fragment** directory's short name (`changelog` for
  `record/changelog.d`) — creates a timestamped fragment, or a named one
  with `--name`;
- `migration` — scaffolds a numbered migration spec in
  `record/migrations.d/`.

With no `KIND` and exactly one journal configured, the journal is the
default — `luria new --title "…"` is the cheapest possible filing. The
field flags (`--title`, `--status`, `--summary`, `--tags`) pre-fill the
scaffolded frontmatter. The generated view of your own config lists every
kind your project accepts (see [the record](record.md) for this one).

## luria repair

```
luria repair
```

Writes every mechanical repair to the sources — each one a state the lint
reports with this command as its remedy: bare codes in prose become links
(what `luria link --fix` does, over every file), a journal entry filed
without `created:` gets the timestamp its path already implies, and a
configuration reference Luria no longer renders here is removed. Prints
what changed. Idempotent: a second run changes nothing.

Repairs are a command apart from the views because they land in a
different place. A repair touches only the files a branch itself authored,
so the generate action commits it onto the branch, where the review reads
it; a view is a shared file every branch would rewrite, so it is committed
on the default branch only.

## luria index

```
luria index [--check]
```

Renders every generated view from the sources: scheme indexes and tag
pages (or the single concatenated page for `render = "document"` schemes),
journal books, the status reports, the record and configuration reference
pages, and the README badge region. Also deletes orphaned files from view
directories. Writes views only; the sources are `luria repair`'s.

`--check` writes nothing and exits non-zero if any committed view differs
from what would be generated, a file sits in a view directory the generator
never wrote, or the README's generated region has drifted — the one
staleness check there is, run by the generation job on the default branch
right after it regenerates. `luria lint` asks no staleness question, so it
runs on a branch as it is. (Views listed in `.gitignore` are exempt: an
uncommitted view cannot be stale.)

## luria link

```
luria link [PATHS…] [--fix]
```

Finds every linkable reference in the given files (default: every
non-generated markdown file the record knows about): bare codes
(`ADR-012`, `DP-3`), temporary codes, remote codes (`LU-ADR-013`),
issue numbers, and `[[wikilinks]]`. Prints per-file counts; with `--fix`,
rewrites them into links whose relative targets are computed *for the
directory where each piece of prose ultimately renders* — which is why
hand-writing targets is the one thing the workflow forbids.

References inside backticks, fences, existing links, HTML comments, and
frontmatter (except designated prose fields) are left alone.

## luria lint

```
luria lint
```

The contract, in two halves.

**Violations** (exit 1), each with the file and line:

- a scheme document without frontmatter, `status:`, `title:`, or `tags:`;
  a status outside the vocabulary (`Active`, `Proposed`, `Deferred`,
  `Superseded`, `Rejected`; a note still riding in `status:` rather
  than in `status_note:`; `Superseded` with no `superseded_by:`) or
  undeclared in the
  scheme's `statuses.yaml`; a missing field the scheme `requires`;
  a `title:` disagreeing with the body heading; tag-group rules
  (`exactly-one`, `at-most-one`, `excluded_by`) broken
- a `version:` above 1 with no `history:`, or history that ends on a
  different version than the document claims
- a journal entry with no derivable `created:`, or filed at a path its
  timestamp says is wrong
- a stray hand-written file in a view directory (whether a committed view
  is *current* is `luria index --check`'s question, asked in the generation
  job on the default branch; a branch carries no view of its own)
- a bare code or unexpanded wikilink that `luria link --fix` would rewrite,
  or a wikilink that resolves to nothing
- a docs page missing from the docs index (`docs/README.md`)

**Warnings**, printed but passing — each is a judgement call, surfaced with
its acknowledgement route (see [directives](directives.md)) and listed in
full in the [reports](reports/reference-status.md):

`retired-citations` · `unresolved-codes` · `hand-written-urls` ·
`broken-targets` · `inert-status` · `legacy-spellings` · `narrow-titles` ·
`stale-directives` · `pending-documents` · `unlinted-files` ·
`workflow-temp-codes`

Any of those class names listed in `[luria.lint] fail_on` fails the build
instead. Only unacknowledged findings ever reach a class, so
acknowledgements keep working under enforcement.

## luria reports

```
luria reports [--out DIR]
```

Writes the two status reports (default: the configured `reports` path,
`docs/reports/`): **pending-decisions** — every `Proposed`/`Deferred`
document with age and citation counts — and **reference-status** — retired
documents cited unacknowledged, codes resolving to nothing, files opted
out of checking, and directives that no longer apply. `luria index` writes
these too; the standalone command exists for CI jobs that want only the
reports.

## luria collect

```
luria collect [DIR] [--commit]
```

For each configured fragment directory (or just `DIR`): read every
fragment in the order it entered git history, insert the non-empty ones at
the target's `<!-- luria-insert-here -->` marker (the `changelog` style
adds a dated heading; the default appends), and delete the fragments.
`--commit` stages and commits the result with `[skip ci]` — the shape a
scheduled CI job wants.

## luria concretize

```
luria concretize [--check]
```

For schemes with `allocate = "merge"`: assign each temporary code
(`ADR-tmp3kf9x`) the next real number, rename the file, rewrite every
reference in docs and scanned code, and record the old spelling under
`formerly:` so stale spellings keep resolving. Run it where merges
serialize — the push-to-main CI job — and never on a PR branch, which
would re-create the collision the temporary codes exist to avoid.
`--check` exits non-zero while any temporary code is pending.

## luria remotes

```
luria remotes [--refresh] [--check] [--pin [CODE]]
```

Prints every foreign code the record cites, per remote, with the URL each
resolves to and the evidence behind it (explicit template, discovered
filename, or bare convention). `--refresh` re-discovers each remote's
actual filenames via the GitHub API and writes `remotes.lock.json` —
committed, so CI and offline checkouts resolve identically. `--check`
HEAD-probes every cited URL and reports what a reader would find: broken,
absent from the remote, or unverifiable because the repository is not
readable anonymously.

`--pin` endorses remote *content*: it fetches each document, hashes it,
and stores the hash in the same lockfile. A remote document has no status
this project can read, but a change in its bytes is knowable — `--refresh`
re-observes every pinned document, and `luria lint` reports each one whose
content moved on since its endorsement (the `remote-drift` warning class,
promotable via `fail_on`). Review the change, then
`luria remotes --pin CODE` endorses it again.

Every pin has a registration — the thing that says it should exist, and
whose removal retires it. `pin = true` on a remote (or one of its
schemes) registers the whole code family: each cited reference is pinned
automatically, and the lint reports any the lockfile has not endorsed
yet. A `pin:` comment directive registers one arbitrary URL where it is
cited. An explicit `--pin CODE` registers one ad-hoc pin, whose lockfile
entry is its own registration. A bare `--pin` syncs the lockfile to the
registrations — endorsing what is newly registered, re-observing what
exists, dropping what nothing cites or flags — and it never re-endorses
drifted content: that always takes the explicit command, so a scheduled
sweep cannot quietly launder a drift finding.

What gets hashed is the construction's *stable bytes*, not the page a
reader lands on. A GitHub file construction qualifies on its own; any
other remote declares where its stable bytes live with a `pin_url`
template — arXiv's immutable e-print archive behind its abstract page, a
forge's own raw scheme — because a rendered page's markup churns under
identical content, and a hash of it would cry wolf. Without either, the
command says so rather than storing a hash that would drift on its own.
Under the hood these are two entries in one table: a code relates to a
set of *named URIs* (`read`, `bytes`, and any name a project declares in
`[luria.remotes.X.uris]`), each a template over one vocabulary — see the
[configuration reference](configuration.md).

An arbitrary URL — a spec, a dataset card, a post the design leans on —
is pinned by flagging it where it is cited
(`<!-- pin: https://… — why it matters -->`, see
[comment directives](directives.md)) and running the same `--pin`.
Deleting the flag retires the pin.

## luria migrate

```
luria migrate SPEC [--dry-run] [--commit]
```

Executes a migration spec from `record/migrations.d/` (`SPEC` can be a
path, a filename, or a unique prefix like `0001`). Two operations:

- `rename_scheme` — rename a prefix wholesale: files move (`git mv`),
  every reference and anchor in the repository is swept to the new
  spelling, config tables are renamed, and each moved document is stamped
  `formerly:` with its old code.
- `move_doc` — move one document into another scheme, where it gets a
  temporary code for the next concretize.

Either operation takes `strategy = "supersede"` to copy instead of move,
leaving a tombstone (`status: Superseded`, `superseded_by: …`) at the
old code. `--dry-run`
prints the full plan. `--commit` commits the sweep and appends the commit
to `.git-blame-ignore-revs`, so blame reads through the rename. The spec
itself is never swept: its mapping is the durable memory of the old names.

## luria site

```
luria site [--out build/site]
```

Stages the record as a [Quartz](https://quartz.jzhao.xyz/) vault: every
publishable page at its repository path (so all relative links keep
working), a `record line` (status · version · filed · issue · influenced
by · the typed edges in and out of it) injected under each document's
title, codes registered as aliases,
README as the landing page, links to unpublished files redirected to the
repository, and the theme/branding from `[luria.site]` rendered into
Quartz config. The published site gets search, backlinks, and a local
graph per page. The `actions/site` composite action builds the staged
vault with a pinned Quartz for GitHub Pages — see [adopting](adopting.md).

## Environment

- `LURIA_ROOT` — overrides project-root discovery; how CI and the test
  suite point a run at a tree that is not the working directory.
- `LURIA_JOBS` — caps the thread pool used for rendering, scanning, and
  URL probing. `LURIA_JOBS=1` is the deterministic escape hatch.

Every module is also runnable standalone (`python -m luria.ref_status
--all`) for projects that vendor a file rather than installing the
package.
