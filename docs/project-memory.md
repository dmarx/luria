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
  reports, the badge counts in the README — and, on demand rather than
  committed, the SQLite database `luria export` writes for asking the
  record questions. A view directory holds *only*
  generated files — `luria lint` fails on a stray hand-written file inside
  one, and `luria index --check` on the default branch fails on a stale
  view, so a reader can trust that what they see reflects the sources.

The split is the whole trick. Contributors write into an append-only pile;
readers get curated, cross-linked pages; and nothing depends on anyone
remembering to keep the two in sync, because the lint remembers.

## The four families

`luria.yaml` declares what the record is made of, using four *families* of
table. You name the entries, and the names become the vocabulary — nothing
in the code spells `ADR`; it is simply the scheme this package ships as a
default.

### Schemes — referable documents

```yaml
schemes:
  RFC:
    dir: record/rfcs.d
    output: docs/rfcs
    render: index
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

#### What each render produces

Every scheme declares a `render`. Which one you want is a question about how
the set is read — [designing a record](modeling.md#index-or-document) is that
question. What each one *does*:

| | `render = "index"` | `render = "document"` |
|---|---|---|
| the reading | one entry at a time, arrived at by a link | the whole set, in order |
| `output` means | a **directory** the view renders into | the assembled **file** itself |
| what is generated | `README.md`, a table of every entry, plus `<field>/<value>.md` per value of each grouped field | one page, every body concatenated |
| a citation lands on | the entry's own file — `ADR-012.md` | a section anchor — `design-principles.md#dp-3` |
| the `axis:` vocabulary | orders the index and titles the value pages | unused; an assembled document groups by nothing |
| `inert-status` | applies | exempt — every principle being in force is the expected state, not a dead field |
| cited from a remote | `remotes.X.schemes.Y.dir = …` | `document = …`, with an optional `anchor` |

Watch `output`, which means something different in each: `docs/rfcs` for an
index is a directory that will come to contain `README.md` and `tags/`, while
`docs/interfaces.md` for a document is the page itself.

Unset, either render puts the view beside its sources — the collocated shape
a project has before it splits `docs/` from `record/`.

### Journals — dated entries that persist

```yaml
journals:
  devlog:
    dir: record/devlog.d
    output: docs/devlog
    granularity: month
```

A journal entry is filed at `yyyy/mm/dd/hhmmss.md` and is true about the
day it was written: never revised, and never expected to stay current. `luria index` renders the entries into **books** — one
page per year, month, or day, with a contents list — plus an index of all
books. Because sources persist and every entry is a fresh path, a journal
is safe to write into without coordinating with anyone.

A project can run several — a devlog, an incident log, meeting notes — each
with its own table, granularity and output.

### Fragment directories — pieces assembled later

```yaml
fragments:
  record/changelog.d:
    file: CHANGELOG.md
    style: changelog
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

```yaml
remotes:
  LU:
    name: luria
    repo: dmarx/luria
```

A remote gives a foreign record a prefix, so `LU-ADR-013` cites a decision
in another repository and says *whose* decision it is at the point of use.
Luria constructs the URL by convention (a file named for the code in the
remote's record directory), from a lockfile of discovered filenames
(`luria remotes --refresh` writes `remotes.lock.json`, committed so CI and
offline checkouts resolve identically), or from an explicit template.
`luria remotes --check` HEAD-probes every cited URL and reports the ones
that would 404 on a reader.

A foreign document's *status* is unknowable — upstream may retire it
tomorrow and nothing here would notice — but a change in its content is
not. `luria remotes --pin` stores a hash of each cited document in the
lockfile as an endorsement; `--refresh` records what upstream serves now;
and `luria lint` compares the two committed hashes offline, reporting each
pinned document that changed since a human vouched for it (the
`remote-drift` warning class). Re-endorsing after review is the
acknowledgement. `pin = true` on a remote or one of its schemes registers
the whole code family — every cited reference is pinned automatically,
and the lint reports any not yet endorsed. A remote whose readable page
is a rendering declares where its stable bytes live
(`pin_url = "https://arxiv.org/e-print/…"`), and a URL that is not a
foreign code at all is pinned by flagging it where it is cited
(`<!-- pin: https://… — why -->`). Removing a registration — the config
line, the flag — retires its pins.

Under it all, a code relates to a set of *named URIs* through one template
vocabulary: `url` is the `read` relation, `pin_url` the `bytes` one, and a
`uris` table on a remote or scheme names more — a different forge's raw
scheme, an edit view — without a new mechanism.

The `uid` form generalises past Luria-shaped records entirely: give a
remote a regex and a URL template and arXiv identifiers, Jira keys, or CVE
numbers become linted, linkable references:

```yaml
remotes:
  CVE:
    uid: \d{4}-\d{4,7}
    url: https://nvd.nist.gov/vuln/detail/CVE-{uid}
```

One rule follows from the family design: a *settings* table (`paths`,
`code`, `lint`, `site`) merges key by key with the defaults, but a family
you declare **replaces the shipped family whole**. A project that writes
`schemes.RFC` and nothing else has exactly one scheme; the default
`ADR` is simply absent. Declare a family and it is yours entirely.

## The five statuses

Every scheme document carries a `status:` from a closed vocabulary —

> `Active` · `Proposed` · `Deferred` · `Superseded` · `Rejected`

— with `superseded_by:` naming a superseded document's successor (a
reference field: checked, resolved, an edge) and an optional
`status_note:` for anything the field cannot say, which is prose: a code
in it is a citation, linked by the fixer. The words
are Luria's; what they *mean* for a scheme is the project's, declared per
scheme: the `active` key names which status counts as **in force**, and an
optional `statuses.yaml` beside the sources narrows the vocabulary and
gives each status a legend line rendered above the index.

Status is what makes the record more than a pile of prose. Only an in-force
document is a safe thing to cite as justification; `Proposed` and
`Deferred` are open questions, `Superseded` and `Rejected` are history. The
reference machinery (below) leans on exactly this distinction.

## Constraints

Status says what is in force. **Constraints say what a document is allowed to
be** — and they are how a record stops being a folder of markdown with a
naming convention, because a convention nobody can break is a comment.

All of them are opt-in and per scheme. A scheme that declares none behaves
exactly as every scheme did before they existed.

**Required fields.** Beyond `status:`, `title:` and `tags:`, a scheme can
require fields of its own:

```yaml
schemes:
  SOTA:
    requires:
    - source
```

A document without `source:` now fails the lint. This is also what makes a
cross-scheme move safe to automate: `luria migrate` relocates a file, and the
document then fails until a human supplies what the destination scheme's
template would have prompted for. The machinery moves it; only a person
vouches that it belongs.

**One of several fields.** `requires` demands every field it names. When
the need is *a source* and any of several fields is one, a field group
says so and the lint asks for one:

```yaml
schemes:
  LIT:
    field_groups:
      source:
        fields:
        - arxiv
        - doi
        - url
        require: at-least-one
```

A paper never posted to arXiv but carrying a DOI, or only a URL, passes;
one with none of the three fails, and the finding names all three.

**A field no two documents may share.** `unique: true` on a field — or on a
field group, where it means the group as a whole — makes a second document
of the same scheme carrying that value a violation, naming both:

```yaml
schemes:
  LIT:
    field_groups:
      source:
        fields:
        - arxiv
        - doi
        - url
        require: at-least-one
        unique: true
```

Said once on the group rather than three times on the fields, because a
source is what the three have in common and uniqueness is a property of it.
Two notes filed for one paper is the failure it catches: the record grows a
second entry nobody knows to merge, and both go on being cited.

**Typed relations.** A field that holds a *code* is not just a required
field — `requires: [source]` is satisfied by the string "a paper I read
once". Declaring what the field points at makes four checks out of one:
present, shaped like a code, resolving to a real document, and in force.

```yaml
schemes:
  SOTA:
    references:
      source:
        scheme: LIT
        required: true
      extends:
        scheme: SOTA
        many: true
        converse: extended_by
        invariant: worlds
```

`converse` names the field holding the same relation read backwards, which
is what licenses `luria link --fix` to write the missing side — a relation
naming *itself* is what symmetry is. `invariant` names a field both ends
must agree on: a scene that extends a scene in another world is a mistake
the codes alone cannot show. A relation with no declared converse is left
alone entirely, because its reverse edge would be a guess.

A relation can also be *walked*, which is what a chain is:

```yaml
chains:
  lineage:
    scheme: LIT
    relation: extends
    sibling: compared_against
    output: docs/lineage.md
    title: Lines of work
```

Where a reference gives one document its neighbours, a chain answers the
question no single document holds — *what line of work is this a step in* —
and renders the sequences on one page. A cycle, or a comparison held on one
side only, becomes a finding rather than a page that quietly omits it.

**Tag rules.** A vocabulary says what a value *means*; a group says which of
them may appear together, because some fields are an axis rather than a pile.
The group is declared under the field it constrains:

```yaml
schemes:
  SOTA:
    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
        closed: false
        groups:
          primary_topic:
            require: exactly-one
            tags:
            - training-optimization
            - systems-optimization
            - model-stability
            excluded_by: []
```

`exactly-one` is the "pick a primary category" rule, checked. Tags outside the
group stay unconstrained, so secondary tags remain free. `excluded_by` covers
the contradiction case — naming how an argument fails contradicts saying it
holds.

**Controlled vocabularies.** A field whose values come from a closed set the
project defines — not codes, so not a reference; a second axis, so not a
tag; many-valued and project-defined, so not a status:

```yaml
schemes:
  SCENE:
    fields:
      worlds:
        vocabulary: worlds
        many: true
        default:
        - B
```

The values and what they mean live under `vocabularies:` in `luria.yaml`,
named once and referenced by every field that uses them. Closed is the
default: a value the vocabulary does not name is a finding. `closed: false`
is the other posture — the declaration supplies order, label and blurb, and
a document may still reach for a new value, which is what `tags` needs. The
default is an effective value — the lint, the index and the record page read
an absent field as `B` — and is never written into the source. `luria index`
renders a page per value, for every grouped field alike: `status` and `tags`
are two instances of this shape, not two special cases beside it.

**What a rule says when it fires.** A vocabulary or a tag group can carry an
`alert` — prose printed after its own violation:

```yaml
vocabularies:
  topics:
    alert: >-
      Closed so every tag is one somebody chose, not because the list is
      finished — add a value here rather than reaching for the nearest
      wrong one.
```

The rule is mechanical and the reason for it is not. A closed vocabulary's
default message reads as *this value is not allowed*, where the project
usually means *this value is not declared yet, and declaring it is the move*
— and only the record knows which. It rides the set rather than the field,
so every field using that vocabulary gets the same sentence; a guard whose
message teaches the wrong lesson costs more than the typo it catches.

**Titles that generalise.** A principle stated about the one artifact it was
noticed on is a principle nobody applies to the next one. That failure is
quiet: the entry stays true and keeps rendering, and never gets cited.

```yaml
schemes:
  DP:
    titles_generalize: true
lint:
  narrow_terms:
  - toolbar
  - canvas
  - queue
```

The vocabulary is your project's own concrete nouns — Luria ships none,
because a shipped list would be some other project's vocabulary wearing the
authority of a default. It fires on titles only, and fails open: a missed noun
costs a review comment, where a false alarm would cost trust in the check.

**Fields carrying no information.** Not configured, always on: a scheme where
every document shares one status is reported as `inert-status`. A field every
record agrees on is indistinguishable from no field, and the difference
matters because other machinery reads it — `active` decides what counts as
retired, and the retired-citation check fires off that. A scheme in that state
has an enforcement mechanism that cannot fire, and the build is green
*because* nothing is being judged.

Which constraints to reach for, and when a rule is better expressed as a
second scheme, is [designing a record](modeling.md).

## Codes and links

A code in prose — in a doc page, a record entry, a `README`, or a source
comment covered by `code.globs` — is treated as a **claim**: this
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
- **Codes that resolve to nothing are surfaced** the same way. A typo, a
  number from another project and a deliberate example all look identical to
  the machine, so telling them apart takes a person, and the finding is a
  report and not a failure.

These findings are warnings by default. A project that wants any class to
fail the build promotes it with `lint.fail_on` — the dial between
reported and enforced, per class, without ever silencing the account.

## Numbering without collisions

<!-- unresolved-ok-block: ADR-158, ADR-tmp3kf9x — illustrative codes, not citations -->
Sequential numbers collide: two branches both file `ADR-158`, and one of
them is renumbering after the merge. A scheme with `allocate = "merge"`
sidesteps this — `luria new` mints a **temporary code**
(`ADR-tmp3kf9x`), the work merges under it, and `luria concretize`,
run where merges serialize (the push-to-main CI job), assigns the next real
number and rewrites every reference in the repository.

The old spelling is recorded in the document's `formerly:` list, so a
temporary code in an unmerged branch, an old commit message, or a teammate's
notes still resolves — the linter treats `formerly:` entries as aliases and
upgrades leftover spellings when it can.

## Superseding and correcting

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

## The status reports

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
  from its `luria.yaml`.
