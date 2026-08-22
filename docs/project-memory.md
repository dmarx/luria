# Project memory

How Luria models a project's memory. The [quickstart](quickstart.md) shows
the commands; this page explains the machine they drive.

## Sources and views

Everything in a Luria record divides into two kinds of file:

- **Sources** are written by people: one small markdown file per entry,
  filed under `record/`. A source is cheap to write, trivial to review in a
  PR, and never conflicts with a neighbour, because every contribution is a
  new file.
- **Views** are written by `luria index`: the decision index and its tag
  pages, the rendered principles document, journal books, the status
  reports, the badge counts in the README. A view directory holds *only*
  generated files — `luria lint` fails on a stale view and on a stray
  hand-written file inside one, so a reader can trust that what they see
  reflects the sources.

The split is the whole trick. Contributors write into an append-only pile;
readers get curated, cross-linked pages; and nothing depends on anyone
remembering to keep the two in sync, because the lint remembers.

## The four families

`luria.toml` declares what the record is made of, using four *families* of
table. You name the entries, and the names become the vocabulary — nothing
in the code spells `ADR`; it is simply the scheme this package ships as a
default.

### Schemes — referable documents

```toml
[luria.schemes.RFC]
dir    = "record/rfcs.d"
output = "docs/rfcs"
render = "index"
```

A scheme is a family of documents with **codes**: `RFC-001`, `RFC-002`.
Declaring the table above is everything it takes to make `RFC-7` a
first-class reference — `luria new rfc` scaffolds the next number,
`luria link --fix` writes its link, and the lint tracks every place it is
cited.

Each document is one markdown file whose filename is its code and nothing
else. The title lives in frontmatter, where correcting it costs an edit
rather than a rename plus every inbound link:

```yaml
---
status: Proposed
title: Consumers must be idempotent
version: 1
tags: [record]
date: '2026-08-22'
summary: >-
  One paragraph for the index row — what this establishes, and what it
  rejected.
---
```

A scheme renders one of two ways:

- `render = "index"` — a generated `README.md` table of every document,
  plus one page per tag. Decisions read this way.
- `render = "document"` — every entry concatenated into a single page at
  `output`, each with a stable anchor. Design principles read this way: the
  set is short enough to read whole, and a reference points at a section,
  not a file.

### Journals — dated entries that persist

```toml
[luria.journals.devlog]
dir         = "record/devlog.d"
output      = "docs/devlog"
granularity = "month"
```

A journal entry is filed at `yyyy/mm/dd/hhmmss.md` and is true about the
day it was written: it is never revised, never consumed, and never expected
to stay current. `luria index` renders the entries into **books** — one
page per year, month, or day, with a contents list — plus an index of all
books. Because sources persist and every entry is a fresh path, a journal
is safe to write into without coordinating with anyone.

A project can run several: a devlog, an incident log, meeting notes — each
its own table, granularity, and output.

### Fragment directories — write now, assemble later

```toml
[luria.fragments."record/changelog.d"]
file  = "CHANGELOG.md"
style = "changelog"
```

The changelog problem: a shared file every PR appends to is a standing
merge conflict. A fragment directory dissolves it — each contribution is a
new file, and `luria collect` (typically a scheduled CI job) assembles the
fragments into the target document at its `<!-- luria-insert-here -->`
marker and deletes them. `style = "changelog"` groups a collection run
under a dated heading; the default style appends bodies in the order the
fragments entered git history.

Fragments are the one *consumed* source: they exist to be collected.

### Remotes — citing another project's record

```toml
[luria.remotes.LU]
name = "luria"
repo = "dmarx/luria"
```

A remote gives a foreign record a prefix, so `LU-ADR-013` cites a decision
in another repository and says *whose* decision it is at the point of use.
Luria constructs the URL by convention (a file named for the code in the
remote's record directory), from a lockfile of discovered filenames
(`luria remotes --refresh` writes `remotes.lock.json`, committed so CI and
offline checkouts resolve identically), or from an explicit template.
`luria remotes --check` HEAD-probes every cited URL and reports the ones
that would 404 on a reader.

The `uid` form generalises past Luria-shaped records entirely: give a
remote a regex and a URL template and arXiv identifiers, Jira keys, or CVE
numbers become linted, linkable references:

```toml
[luria.remotes.CVE]
uid = "\\d{4}-\\d{4,7}"
url = "https://nvd.nist.gov/vuln/detail/CVE-{uid}"
```

One rule follows from the family design: a *settings* table (`paths`,
`code`, `lint`, `site`) merges key by key with the defaults, but a family
you declare **replaces the shipped family whole**. A project that writes
`[luria.schemes.RFC]` and nothing else has exactly one scheme; the default
`ADR` is simply absent. Declare a family and it is yours entirely.

## Status: what is in force

Every scheme document carries a `status:` from a closed vocabulary —

> `Active` · `Proposed` · `Deferred` · `Superseded` · `Rejected`

— optionally followed by ` — a note` (`Superseded — by RFC-9`). The words
are Luria's; what they *mean* for a scheme is the project's, declared per
scheme: the `active` key names which status counts as **in force**, and an
optional `statuses.yaml` beside the sources narrows the vocabulary and
gives each status a legend line rendered above the index.

Status is what makes the record more than a pile of prose. Only an in-force
document is a safe thing to cite as justification; `Proposed` and
`Deferred` are open questions, `Superseded` and `Rejected` are history. The
reference machinery (below) leans on exactly this distinction.

## Codes, references, and links

A code in prose — in a doc page, a record entry, a `README`, or a source
comment covered by `[luria.code] globs` — is treated as a **claim**: this
text says that document is why things are this way. Luria keeps the claims
honest:

- **Bare codes must become links.** `luria lint` flags a plain code in a
  markdown file; `luria link --fix` rewrites it into a link. Never
  hand-write the target: record prose is *rendered into views in other
  directories*, so the correct relative path depends on where the text
  lands, not where it lives — the fixer computes that frame, a human
  reliably gets it wrong. Codes inside backticks or fenced blocks are
  exempt; that is how you mention a code without citing it.
- **Wikilinks label a reference.** `[[RFC-7]]` expands to a plain link;
  `[[RFC-7|the delivery decision]]` uses your prose as the label. The
  fixer expands both.
- **Issue references.** With `issue_url` configured, `#123` links to the
  tracker. A low number needs a cue word nearby (`issue`, `fixes`,
  `closes`, …) so that prose like `principle #2` is not mistaken for a
  ticket.
- **Citations of retired documents are surfaced.** A reference to a
  document that is not in force appears in the
  [reference-status report](reports/reference-status.md) until a human
  either fixes the text or vouches for the citation with an
  [acknowledgement directive](directives.md) at the citing site.
- **Codes that resolve to nothing are surfaced** the same way — a typo, a
  number from another project, and a deliberate example look identical to
  the machine, so telling them apart is a report, not an error.

These findings are warnings by default. A project that wants any class to
fail the build promotes it with `[luria.lint] fail_on` — the dial between
reported and enforced, per class, without ever silencing the account.

## Numbering without collisions

<!-- unresolved-ok: ADR-060 — an illustrative collision, not a citation -->
Sequential numbers collide: two branches both file `ADR-060`, and one of
them is renumbering after the merge. A scheme with `allocate = "merge"`
sidesteps this — `luria new` mints a **temporary code**
(`ADR-tmp3kf9x`), the work merges under it, and `luria concretize`,
run where merges serialize (the push-to-main CI job), assigns the next real
number and rewrites every reference in the repository.

The old spelling is recorded in the document's `formerly:` list, so a
temporary code in an unmerged branch, an old commit message, or a teammate's
notes still resolves — the linter treats `formerly:` entries as aliases and
upgrades leftover spellings when it can.

## Revising the record

A record you cannot revise becomes a record you stop trusting. Two
mechanisms keep revision honest:

- **Versions.** Correcting a document means bumping `version:` and
  appending a `history:` entry saying what changed — the lint refuses a
  version bump with no account of itself.
- **Migrations.** Renaming a scheme or moving documents between schemes is
  a repository-wide rewrite, so it is executed from a committed spec
  (`record/migrations.d/NNNN-*.toml`) by `luria migrate` — moves, reference
  sweeps, `formerly:` stamps, and a `.git-blame-ignore-revs` entry so blame
  reads through the rename. The spec stays in the repository afterward: its
  mapping *is* the memory of the old names.

## Reports: what awaits a human

Some questions cannot fail a build because they need judgement. Those
render as committed report pages under `docs/reports/`:

- [Pending decisions](reports/pending-decisions.md) — every `Proposed` or
  `Deferred` document, with age and citation count. An old proposal nothing
  cites is a stalled idea worth closing; an old proposal many files cite is
  a decision the codebase already made and never wrote down.
- [Reference status](reports/reference-status.md) — citations of retired
  documents, codes that resolve to nothing, and the acknowledgements that
  keep either quiet on purpose.

The README badge region (`luria index` maintains it between
`<!-- luria:badges -->` markers) summarises both counts at a glance.

## Where to go next

- [Quickstart](quickstart.md) — do all of the above in ten minutes.
- [CLI reference](cli.md) — the commands, flag by flag.
- [Configuration reference](configuration.md) — every key, generated from
  the schema.
- [The record](record.md) — this project's own instantiation, generated
  from its `luria.toml`.
