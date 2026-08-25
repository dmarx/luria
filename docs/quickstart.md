# Quickstart

From an empty (or existing) repository to a linted, self-checking record.
Everything here is explained properly in [project memory](project-memory.md).

## 1. Install and scaffold

```console
$ pip install luria
$ cd yourproject
$ luria init --issue-url https://github.com/you/yourproject/issues
luria init → /home/you/yourproject
  write  luria.toml
  write  record/decisions.d/_template.md
  write  record/decisions.d/README.stub
  write  record/decisions.d/tags.yaml
  write  record/principles.d/DP-001.md
  ...
  write  docs/README.md
  write  CLAUDE.md
  write  .github/workflows/docs.yml
  write  .github/workflows/pages.yml
wrote 18 file(s), skipped 0 existing.
```

`init` never overwrites: a file that already exists is skipped and
reported, so re-running it on a grown project is safe. It scaffolds the
default record — decisions (`ADR`), design principles (`DP`), a changelog
fragment directory, a devlog — plus a `luria.toml` where all of that can be
renamed, replaced, or extended. Every key has a default, so the file starts
nearly empty.

If you already know the record needs more than decisions and principles, say
so here and skip the editing:

```console
$ luria init --issue-url https://github.com/you/yourproject/issues \
             --schemes "RFC,SPEC:document" --journals "incidents:day"
```

Same scaffold, three more families in it. Each entry is `NAME` or
`NAME:kind`, and the tables land in `luria.toml` as ordinary commented TOML —
nothing here is a format you have to keep.
[Designing a record](modeling.md) is how to decide what you need; this is how
to type it once you have.

## 2. Build the views

```console
$ luria index
Wrote 9 file(s) from 0 ADRs, 6 DPs, 0 devlog entries.
```

`luria index` renders every generated view: the decision index and tag
pages, the principles document, journal books, the status reports, and the
badge region in your README (add `<!-- luria:badges -->` /
`<!-- /luria:badges -->` markers where you want the badges). Run it after
any change to the record; CI will hold you to it — a stale committed view
fails `luria lint`.

## 3. File things

Filing is the habit the whole system exists to make cheap. The rule of
thumb: **file the entry in the same branch as the work it describes**,
while the context is loaded — a fact filed now costs a paragraph, and
re-derived cold it costs a session.

A devlog entry (the default kind when only one journal is configured):

```console
$ luria new --title "Rate limiter: token bucket beat sliding window"
record/devlog.d/2026/08/22/143005.md
```

A decision:

```console
$ luria new adr --title "Public API errors are RFC 7807 problem documents"
record/decisions.d/ADR-001.md
```

A changelog fragment (collected into `CHANGELOG.md` later — no shared file,
no merge conflict):

```console
$ luria new changelog
record/changelog.d/20260822-143107.md
```

Each command prints the file it created; open it and write. The scaffolded
frontmatter shows what the machinery expects — a `status:` from the closed
vocabulary, a `title:`, `tags:`, and a `summary:` that becomes the index
row.

## 4. Cite, link, lint

Reference a decision from anywhere — docs, other record entries, even code
comments — by its bare code, then let the fixer spell the link:

```console
$ luria link --fix
docs/api.md: 2 reference(s)
linked 2 reference(s) in 14 file(s)
$ luria lint
luria: docs lint clean
```

Never hand-write a link target for a code: prose gets rendered into views
in other directories, so the right relative path depends on where the text
*lands*, and only the fixer knows that. Want prose as the label? Write
`[[ADR-001|the error-format decision]]` and fix it the same way.

`luria lint` is the whole contract: frontmatter present and well-formed,
statuses from the declared vocabulary, no stale or orphaned generated
files, every code linked, every wikilink expanded, every docs page listed
in the docs index. It also *reports* (without failing) the judgement-call
findings — retired documents still cited, codes that resolve to nothing —
which land in `docs/reports/` and can be promoted to failures per class
with `[luria.lint] fail_on`.

## 5. Wire up CI

`luria init` scaffolds two workflows using Luria's published composite
actions:

- **docs.yml** — on every push and PR: regenerate the views and push the
  diff (`dmarx/luria/actions/generate`), then lint the result
  (`dmarx/luria/actions/lint`) and upload the status reports as an
  artifact. A weekly scheduled run calls `luria collect --commit` to
  assemble changelog fragments.
- **pages.yml** — build the record into a static site
  (`dmarx/luria/actions/site`) and deploy it to GitHub Pages. See
  [adopting](adopting.md) for what the site gives you and how to brand it.

That is the steady state: contributors file sources, CI regenerates views
and keeps every reference honest, and the record accretes.

## Where next

- [Project memory](project-memory.md) — the model behind these commands.
- [CLI reference](cli.md) — every command and flag, including the ones
  this page skipped (`concretize`, `migrate`, `remotes`).
- [Configuration reference](configuration.md) — renaming the families,
  adding schemes and journals, scanning your source code for references.
