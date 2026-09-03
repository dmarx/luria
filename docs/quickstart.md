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

`luria init --dry-run` prints that same list and writes nothing, which is
worth running first in a repository that already has history — this adds two
GitHub Actions workflows and an agent context file, and seeing the list before
it lands is cheaper than reading it back out of `git status`.

`CLAUDE.md` is a short map pointing at the record's docs plus an invitation to
run `luria --help`. Nothing in Luria depends on Claude or on any agent; the
file is there because a coding agent that reads one file at the start of a
session is a reader worth writing for, and it is safe to delete or rename.

`init` never overwrites: a file that already exists is skipped and
reported, so re-running it on a grown project is safe. It scaffolds the
default record — decisions (`ADR`), design principles (`DP`), a changelog
fragment directory, a devlog — plus a `luria.toml` where all of that can be
renamed, replaced, or extended. Every key has a default, so the file starts
nearly empty.

`--issue-url` is optional in a repository that has an `origin` remote on
GitHub or GitLab: init reads it from there, and reports what it used.

If you already know the record needs more than decisions and principles, say
so here and skip the editing:

```console
$ luria init --issue-url https://github.com/you/yourproject/issues \
             --schemes "RFC,SPEC:document" --journals "incidents:day"
```

Same scaffold, three more families in it. If you want to change something the
shorthand does not cover — a directory name, a status vocabulary, a tag group
— write the config first and scaffold second, so nothing has to move:

```console
$ luria config --schemes "RFC,SPEC:document"
$ $EDITOR luria.toml
$ luria init
```
 Each entry is `NAME` or
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

## 5. Break it on purpose

Everything so far was setup. This is the part that pays for it.

Suppose `docs/api.md` says why the code is shaped the way it is:

```markdown
We retry writes because ADR-001 requires at-least-once delivery.
```

Now the decision changes. File its successor, and retire the old one by
editing one field — not by deleting it:

```yaml
status: Superseded
superseded_by: ADR-002
```

Nobody touched `docs/api.md`. It is now wrong, and the record says so:

```console
$ luria index && luria lint
luria: 1 warning(s) — retired documents cited unacknowledged from current docs/code
  ADR-001 is Superseded, cited 1× in 1 file(s) — Errors carry a machine-readable code

$ luria reports
docs/api.md:3
```

That is the whole mechanism: **one field moved, and a page nobody opened
became a finding.** [ADR-001](../record/decisions.d/ADR-001.md) keeps its body and its reasoning — the record
still knows what the project used to believe, and why.

Two ways to close it, and the choice is the point:

- **The citation is wrong.** Rewrite the sentence to cite `ADR-002`. Re-run,
  and the finding is gone.
- **The citation is deliberate** — the paragraph is about the history, or the
  rejection is what you meant to point at. Say so where it happens:

  ```markdown
  <!-- inactive-ok: ADR-001 — the decision this section explains replacing -->
  ```

  The reason is mandatory, it lives at the citing site, and it goes stale on
  its own if [ADR-001](../record/decisions.d/ADR-001.md) ever returns to force.

What you must not do is nothing, silently. That is the state the whole tool
exists to make impossible.

## 6. Wire up CI

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
