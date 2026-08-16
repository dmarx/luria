# Adopting Luria

## Install and scaffold

```
pip install git+https://github.com/dmarx/luria      # not on PyPI yet
cd your-project
luria init --issue-url https://github.com/owner/repo/issues
```

The scaffold is planned from configuration, not copied from a fixed tree
([ADR-048](../record/decisions.d/ADR-048.md)), which gives `luria init` three modes:

- **Bare** (above): the shipped default config — decisions, principles, a
  changelog, a devlog.
- **`luria init --config my.toml`**: write your `luria.toml` first — the
  schemes, journals and fragment directories *your* record needs — and init
  installs it and scaffolds exactly that shape. A config that declares RFCs
  and an incident log gets RFC and incident directories, their templates and
  stubs, and a docs index listing those views; it does not get a decision
  directory it never asked for. Skip ahead to
  [shaping the record](#shaping-the-record-to-your-project) for what a config
  can declare.
- **A project that already has a `luria.toml`**: init reads it and scaffolds
  what it declares, filling in whatever is missing.

`luria init` never overwrites. Existing files are reported as skipped, so
running it on a project that already has half the record adds only the missing
half — and running it twice is a no-op. A scaffolder that clobbers is one nobody
dares re-run, which means the thing it is best at (filling in what a project
grew past) never gets used. The one refusal: `--config` against a project that
already has a `luria.toml` is an error, because scaffolding one config's shape
while another governs the record would build directories the project's own
machinery doesn't know about.

Then:

```
luria index     # build the generated views from frontmatter
luria lint      # should be clean
```

`luria index` is not optional after scaffolding: the two documents a reader
actually opens — the decision index and `design-principles.md` — do not exist
until it runs, because both are generated from the fragments beside them
([ADR-012](../record/decisions.d/ADR-012.md)).

## What you get

```
luria.toml                  paths, issue URL, code globs, reference schemes
docs/                       the READ surface: prose + every generated view
  README.md                 the index a reader lands on; hand-written
record/                     the WRITE surface: every source, marked `.d`
  decisions.d/
    _template.md            copy this to make a decision
    README.stub             the index's prose; the index renders to docs/decisions/
    tags.yaml               tag order and blurbs
    statuses.yaml           optional: which statuses this scheme uses, and what they mean
  principles.d/
    _template.md            copy this to make a principle
    README.stub             the document's prose; renders to docs/design-principles.md
    DP-00N.md               seeded with the ones that earn this machinery
  changelog.d/_template.md  one fragment per contribution; collected, then consumed
  devlog.d/_template.md     the shape of a journal entry; optional, significant work only
.github/workflows/
  docs.yml                  regenerate views, lint them, collect fragments on a cadence
  pages.yml                 publish the record as a site with a citation graph
CLAUDE.md                   a bootloader section pointing at the above
```

### Saying what a status means here

The five status words are fixed — `Active`, `Proposed`, `Deferred`,
`Superseded`, `Rejected` — because an open vocabulary drifted into thirty forms
before [ADR-003](../record/decisions.d/ADR-003.md) closed it. What they *mean*
is yours, and it differs by scheme: `Rejected` on a decision means considered
and declined, while on a scheme recording a corpus's claims it can mean the
corpus asserts this and it is wrong.

Say so in a `statuses.yaml` beside the scheme's `tags.yaml`:

```yaml
Active:
  label: Asserted
  blurb: the record asserts this proposition
Rejected:
  label: Defeated
  blurb: the corpus contains it and it is wrong
```

Two things follow. A record whose status the scheme does not declare fails the
lint, so declaring is also *narrowing* — a scheme that never defers can say so
and be held to it. And the meanings render above the index table, where a
reader browsing the status column can see them without finding your decision
record.

Keys outside the five are an error. This narrows luria's vocabulary per scheme;
it does not extend it. If you want a distinction the five words cannot carry,
that is what `tags` are for — those are open by design.

Declaring nothing keeps the default: all five words, no legend.

The split is [LU-ADR-021](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-021.md):
you read in `docs/`, you file in `record/`, and a view directory holds only
what the generator wrote — the lint enforces all three.

Delete the seed principles you disagree with — a principle nobody believes is
worse than an empty file. Keep the ones you keep *honest*: replace each
`origin:` note with your own first instance, because a rule whose evidence is
missing reads as taste, and taste gets re-litigated by the next person with
different taste.

## Shaping the record to your project

The scaffold above is a *default*, not a shape you have to accept. Four of the
tables in `luria.toml` — `schemes`, `fragments`, `journals` and `remotes` —
are families: you name the entries, and the name becomes part of the
vocabulary ([ADR-006](../record/decisions.d/ADR-006.md)). A family you
declare **replaces** the shipped default rather than merging into it
([ADR-047](../record/decisions.d/ADR-047.md)) — so a record of RFCs and specs is exactly that, with no phantom
decision scheme left over from the defaults — while a family you never
mention keeps them. Settings tables (`paths`, `code`, `lint`, `site`) merge
per key as you'd expect.

The [configuration reference](configuration.md) is generated from the schema
and lists every key. [`examples/`](../examples/) holds four complete projects
in these shapes — RFCs and specs, a collocated layout, three journals, and
citations to things that are not records at all — and CI runs `luria index`
and `luria lint` against every one of them, so what follows is described
rather than hoped. This section is the short version, in the order the
questions usually arrive.

**A second document family.** Decisions are not the only thing worth
numbering:

```toml
[luria.schemes.RFC]
dir    = "record/rfcs.d"
output = "docs/rfcs"
```

`RFC-7` is now a first-class reference — `luria link --fix` writes its link,
`luria lint` demands one, the index and tag pages generate, and `luria new
rfc` scaffolds the next free number from `_template.md`. Nothing else changes,
because the kinds are the config ([ADR-036](../record/decisions.d/ADR-036.md)).

There is an `active` key for the status that means "in force", but it
*selects* from the closed vocabulary rather than extending it. `Active`,
`Proposed`, `Deferred`, `Superseded` and `Rejected` are fixed and
lint-enforced on purpose ([ADR-003](../record/decisions.d/ADR-003.md)) — an
audit found thirty spellings of "this one counts" across 121 files. So
`active = "Accepted"` names a state no document can legally hold, and fails
every document in the scheme.

**Browsed, or read as a whole.** `render = "index"` builds a table of links
plus per-tag pages: right when documents are read one at a time. `render =
"document"` concatenates the bodies into a single page: right when the set is
read start-to-finish, which is what a principles document is ([ADR-012](../record/decisions.d/ADR-012.md)). The
shipped `DP` scheme is the second kind, and it is an ordinary scheme entry —
not a special case.

**Keeping the layout you already have.** Omit `output` and the view renders
beside its sources — the collocated shape projects had before the read/write
boundary existed ([ADR-021](../record/decisions.d/ADR-021.md)). Adoption
never has to start with moving files:

```toml
[luria.schemes.ADR]
dir = "decisions"         # wherever yours already live; the index renders here
```

Omission works because a declared family replaces the defaults — there is no
shipped `output = "docs/decisions"` left for the blank to inherit. (Under the
old merge rule there was, and the documented adoption path silently relocated
your index; the fix is [ADR-047](../record/decisions.d/ADR-047.md).)
[`examples/collocated/`](../examples/collocated/) is the worked version, and
CI runs it.

**More than one journal.** `[luria.journals.X]` is a family like the others, so
a devlog, a meeting log and an incident log can run side by side, each with its
own cadence:

```toml
[luria.journals.incidents]
dir         = "record/incidents.d"
output      = "docs/incidents"
granularity = "year"         # year | month | day — measure your rate first
title       = "Incident log"
```

The distinction that decides between a journal and a fragment directory is
whether the sources survive. A journal's entries are dated observations that
stay true, so they persist and the books are generated from them ([ADR-020](../record/decisions.d/ADR-020.md)). A
fragment directory's files are *consumed* when collected — right for a
changelog, wrong for anything you might want to reread.

**How fragments assemble.** `style = "append"` is the narrative shape, bodies
oldest-first. `style = "changelog"` is the release shape, dated batches newest
first ([ADR-028](../record/decisions.d/ADR-028.md)). The same directory-of-fragments serves either; the collector
is not the contract.

**Citing things that are not Luria records.** A remote need not hold a record
at all. Give it a `uid` pattern and a URL template and its references are
linted like any other ([ADR-024](../record/decisions.d/ADR-024.md)):

```toml
[luria.remotes.ARXIV]
uid = "(\\d{4})[.:](\\d{4,5})"
url = "https://arxiv.org/abs/{1}.{2}"    # {0} or {uid} is the whole tail

[luria.remotes.JIRA]
uid = "[A-Z]+-\\d+"
url = "https://example.atlassian.net/browse/{uid}"
```

`ARXIV-2301.07041` and `JIRA-PROJ-412` now resolve, and `luria remotes
--check` reports whether they still do.

**Concurrent branches that both file documents.** A sequential number claimed
from a branch is a race: two branches both read 122 as the last number and
both mint `ADR-123`. If your workflow is N concurrent branches — an
agent-driven flow is — switch the scheme to merge allocation ([ADR-049](../record/decisions.d/ADR-049.md)):

```toml
[luria.schemes.ADR]
dir      = "record/decisions.d"
output   = "docs/decisions"
allocate = "merge"           # numbers are assigned where merges serialize
```

`luria new adr` then issues a temporary code (`ADR-tmp47fje`) that is
first-class on its branch — indexed, linted, citable bare or as
`[[ADR-tmp47fje]]` — and `luria concretize`, run by whatever serializes your
merges (a merge queue, the job that lands PRs), assigns real numbers in merge
order, rewrites every reference, and records the temporary code as a
permanent `formerly:` alias, so a citation in a PR thread or a commit message
never goes dead. Put `luria concretize --check` in CI on your default branch:
a temporary code there means the concretizer didn't run, and it fails loudly.

**How much the lint enforces.** Status findings are warnings by default;
`fail_on` promotes a class to a build failure, and the acknowledgement
directives keep working under enforcement because only unacknowledged rows
ever reach a class ([ADR-035](../record/decisions.d/ADR-035.md)):

```toml
[luria.lint]
fail_on = ["retired-citations"]
```

One limit worth knowing before you commit to names: adding a scheme costs one
table, but **renaming** one — or moving its documents — is a manual pass
today. There is no migration command; [ADR-040](../record/decisions.d/ADR-040.md) is the decision that would give
it one. Pick prefixes you can live with.

## Adopting into a project that already has decisions

Point `luria.toml` at wherever they live and run `luria lint`. Expect failures
on the first run — that is the machinery telling you what the prose convention
had been letting through. Three are usual:

- **Frontmatter.** If your decisions use a prose `**Status:**` header, they need
  frontmatter ([ADR-003](../record/decisions.d/ADR-003.md)). Migrating is mechanical; the
  audit that motivated the closed vocabulary found thirty distinct spellings
  across 121 files, so budget for a normalizing pass.
- **`title:`.** Every document needs one, and it has to match the body's `#`
  heading ([ADR-013](../record/decisions.d/ADR-013.md)). Lift it from the heading in a
  single pass — that is where the generator used to read it from.

  Renaming the files to `ADR-<NNN>.md` is *not* required and is not linted:
  Luria writes the short form and reads `adr-010-a-slug.md` too, so adoption
  isn't a rename-everything-first proposition. Do it when you want the filename
  to stop being a third copy of the title; expect to rewrite every inbound link
  in the same commit.
- **Bare references.** `luria link --fix` writes them all. In the corpus this
  package was extracted from that was 2,246 references across 160 files. Read a
  sample of the diff rather than trusting it wholesale — that is how the
  code-span bug in [ADR-005](../record/decisions.d/ADR-005.md) was caught.
- **A hand-written principles document.** Split it: one `DP-NNN.md` per
  section, `## N. Title` back up to `# DP-NNN: Title`, and the `README.stub`
  keeping the prose that came before them. Set every `version: 1` except the
  ones you know were reworded — those are the interesting ones, and `history:`
  is where the rewording goes. Until you split it, leave the DP scheme out of
  `luria.toml` and the document stays hand-maintained; links to `#N-the-heading`
  keep resolving either way.

Everything else is a warning and can wait
([ADR-035](../record/decisions.d/ADR-035.md)).

## Adopting into a project that already has a devlog

A single hand-appended `docs/devlog.md` becomes a journal by *not* migrating it.
Configure `[luria.journals.devlog]`, leave the old file where it is, and file
new work with `luria journal new "…"`; the accumulated document is one dated
record and re-cutting it into per-work entries would be guesswork about when
each was written.

If you already keep devlog *fragments*, they can be migrated — their real
authoring times are in the history:

```
git log --diff-filter=A --format=%aI -1 -- <old-fragment-path>.md
```

That is how Luria's own seven entries got their timestamps
([ADR-020](../record/decisions.d/ADR-020.md)), and it is worth the trouble: a migration that
stamps everything with the day it ran makes the log's first page a lie. Two
things to watch. Timestamps come out in the *committer's* offset, so normalise
to a single zone before deriving the paths, or an evening entry sorts into the
following morning. And links written for the old collected file resolve from
*its* directory — a book one level deeper needs them rebased, which `luria lint`
will not catch, because a link is not a bare reference.

## Citing another project

A record extracted from — or working alongside — another project cites it
constantly, and an unprefixed code can't mean both "ours" and "theirs".
Register the remote and cite it with a prefix
([ADR-016](../record/decisions.d/ADR-016.md)):

```toml
[luria.remotes.SG]
name = "strata-g"
repo = "dmarx/strata-g"
```

`SG-ADR-032` is then a first-class reference. Then:

```
luria remotes --refresh     # discover filenames; commit remotes.lock.json
luria remotes               # how each cited reference resolves
luria remotes --check       # HEAD them all (network; never part of the lint)
```

Three things worth knowing before you rely on it:

- **A remote that follows [ADR-013](../record/decisions.d/ADR-013.md) needs no lockfile** —
  the code *is* the filename, so the URL is exact with nothing to refresh. The
  lockfile exists for records whose filenames carry title slugs, where no
  template can turn `032` into `adr-032-a-long-title.md`; `--refresh` reads
  those from the remote once and commits them.
- **Discovery reads public repositories, over HTTPS, with no credentials.** A
  remote Luria can't read is told so and left on the code-only convention. If
  that is wrong for your remote, give it a `url` template — the answer to an
  unreadable remote is configuration, not a credential path CI can't reproduce.
- **A remote's code families can construct differently.** One `dir` covers
  file-per-code schemes; a document-rendered scheme — principles are the
  usual case — gets its own entry
  ([ADR-023](../record/decisions.d/ADR-023.md)):

  ```toml
  [luria.remotes.SG.schemes.DP]
  document = "docs/design-principles.md"    # anchor defaults to dp-{number}
  ```

  The anchor template covers remotes on current conventions; a legacy remote
  whose anchors are heading-derived still needs a hand URL with a `url-ok`,
  now excusing only the anchor.
- **A remote need not hold a Luria record at all.** Give it a `uid` pattern
  and a `url` template, and its references are the prefix, a configurable
  delimiter, and whatever the pattern matches
  ([ADR-024](../record/decisions.d/ADR-024.md)) — the fixer, the lint and
  `url-ok` treat them like any other foreign code:

  ```toml
  [luria.remotes.ARXIV]
  uid = "(\\d{4})[.:](\\d{4,5})"
  url = "https://arxiv.org/abs/{1}.{2}"   # capture groups by position
  ```

  A bare `ARXIV-2403.05530` in prose then linkifies through the template. A
  uid is never normalised, and a uid remote without a template constructs
  nothing rather than guessing.
- **A citation can land before its URL does.** If the remote hasn't adopted
  the code-only filenames yet, register it anyway and cite it: naming the
  document is the durable half, and the links start working when the remote
  converts, with no edit on your side ([ADR-017](../record/decisions.d/ADR-017.md)).
- **`--check` reports, it never fails a build**, and it is never part of
  `luria lint`. It also can't distinguish "the document was deleted" from "this
  repo is private and you are anonymous", so it probes the repository once and
  says *unverifiable* rather than inventing a shelf of 404s.

## Badges that can be wrong

Two numbers are worth putting on a README, because they are the ones a reader
can't get any other way and both can turn amber
([ADR-018](../record/decisions.d/ADR-018.md)):

```
<!-- luria:badges -->
<!-- /luria:badges -->
```

Add that region anywhere in `README.md`, then **run `luria index` and commit
what it wrote**. It fills the region with **needs decision** (`Proposed` +
`Deferred`, every scheme) and **cited but retired** (retired documents still
cited without an acknowledgement). The counts are baked into the URLs, so there
is no service to configure and no committed JSON to keep current — and
`luria lint` fails when the region disagrees with the record.

The region does not fill itself, and nothing fills it for you: like the
decision index and the devlog books, the badges are a **generated artifact that
its author commits** ([ADR-029](../record/decisions.d/ADR-029.md)). The badge
counts are the first generated view most projects add *after* adoption, so this
is usually the first time that matters.

A project with no region is left alone.

## Wiring it into CI

The short version: `luria init` scaffolds
[a complete workflow](../template/.github/workflows/docs.yml) — copy it into
`.github/workflows/` if your project predates the scaffold — built from two
composite actions you can also drop into a workflow you already have:

```yaml
- uses: dmarx/luria/actions/generate@main   # regenerate views, commit + push, output the SHA
- uses: dmarx/luria/actions/lint@main       # luria lint + status reports as an artifact
```

Both assume a checkout and `actions/setup-python` first; `generate` needs
`permissions: contents: write` and takes `pip-spec` if you pin luria. Luria's
own [`ci.yml`](../.github/workflows/ci.yml) runs the same two actions by local
path, so the workflow you scaffold is the one this repository lives on
([ADR-009](../record/decisions.d/ADR-009.md)). The rest of this section is
what those pieces do and why their wiring is load-bearing — read it before
rearranging them.

### Who regenerates?

Something has to *run* the generator, and there are two working answers
([ADR-029](../record/decisions.d/ADR-029.md)):

- **The author does.** Run `luria index`, commit what it wrote. Nothing extra
  in CI, no write permissions, and every contributor carries a build step.
- **A generation job does.** CI runs `luria link --fix` and `luria index`,
  commits the diff as a bot and pushes. Hands-off, and the better default:
  a view a human has to rebuild by hand is still a hand-maintained projection,
  and those drift at a rate rather than a risk.

What does **not** work is the shape in between — the generator in the checking
job, committing nothing:

```yaml
- run: luria index   # ← output discarded, AND the lint below stops working
- run: luria lint
```

Two failures at once. The regenerated files die with the runner, so they never
reach the repository; and `luria lint` verifies views by re-rendering and
diffing against disk, so a generator immediately ahead of it makes the
comparison vacuous — it compares the generator's output against itself and
**stops being able to fail**, for the index and the books as much as the
badges. An adopter shipped exactly that, cleared a red build with it, and ran
three green builds with an empty badge region and a dead gate.

The tempting moment to write it is when the lint has gone red saying
`stale — run luria index`, which is why that message now names the committing
half when it is read in a build.

### Wiring the generation job

The commit/push/handoff logic lives in
[`actions/generate`](../actions/generate/action.yml) — one authoritative
implementation rather than a snippet every adopter restates and drifts. What
stays in *your* workflow is the wiring around it, and two pieces of that
wiring are load-bearing:

```yaml
jobs:
  docs-generate:
    permissions: {contents: write}
    outputs:
      sha: ${{ steps.generate.outputs.sha }}
    steps:
      - uses: actions/checkout@v4
        with:
          # Same-repo PR: the head branch, so there is something to commit
          # onto. Fork PR: that branch only exists in the fork, so naming it
          # FAILS THE CHECKOUT before any push guard runs — fall back to the
          # default merge-commit checkout (empty ref); the generator still
          # runs, nothing is pushed, and the staleness check downstream fires
          # as intended.
          ref: ${{ github.event_name != 'pull_request' && github.ref_name || (github.event.pull_request.head.repo.full_name == github.repository && github.head_ref || '') }}
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - id: generate
        uses: dmarx/luria/actions/generate@main

  docs-lint:
    needs: docs-generate
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ needs.docs-generate.outputs.sha }}
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - uses: dmarx/luria/actions/lint@main
```

Three details that are load-bearing, all of which cost somebody an afternoon:

- **The SHA handoff, and both jobs in one workflow.** A push made with
  `GITHUB_TOKEN` deliberately does not retrigger workflows. Put generation in
  a *separate* workflow and the lint keeps the red it earned from the
  pre-generation commit, with nothing to clear it. `needs:` plus a `sha`
  output is what makes the lint read what the generator just produced.
- **Never write the skip marker into a commit message you author.** GitHub
  matches `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]` and
  `[actions skip]` in the *first or last line* of a message
  ([docs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)),
  so a commit message *documenting* this workflow suppresses its own run —
  silently, with zero check runs on the SHA, which reads like a slow queue
  rather than a skip. Name the marker in prose; file contents are unaffected.
- **Fork PRs break the job in two places, and the checkout is the one people
  miss.** `github.head_ref` on a fork names a branch that only exists in the
  fork, so a checkout naming it fails *before* any push guard runs — which is
  why the `ref:` expression above falls back to the default merge-commit
  checkout for forks. The push guard is the generate action's job (a fork's
  read-only token gets a warning annotation, not a 403), but the checkout is
  *yours*: it happens before any action can help. The checkout half was found
  broken in the first real deployment of this recipe — a hand-trace of the
  fork case is cheaper than waiting for the fork PR you can't send yourself.

**Keep the staleness check either way.** Automating regeneration renders
staleness *moot*, not unreachable — the generation job can fail, be disabled,
lose its write permission, or be that fork PR. The check simply changes what it
watches: it used to catch a forgetful author, and now catches a generator that
didn't run or couldn't push. In the fork case it fires on an ordinary Tuesday,
because the `sha` output is then the un-regenerated commit the lint reads.

Collection runs on a cadence, **not on every merge** — a per-merge bot commit
races in-flight rebases, reintroducing the conflict fragments exist to remove
([ADR-002](../record/decisions.d/ADR-002.md)):

```yaml
on:
  schedule: [{ cron: "0 9 * * 1" }]
  workflow_dispatch:
jobs:
  collect:
    steps:
      - run: luria collect --commit
```

## Publishing the record

`luria init` also scaffolds
[a Pages workflow](../template/.github/workflows/pages.yml). It stages the
record as an Obsidian/Quartz vault and builds it, which turns the citations
the lint already guarantees are links into a graph, backlinks, full-text
search and per-tag pages — none of them maintained by hand
([ADR-042](../record/decisions.d/ADR-042.md)):

```yaml
- id: site
  uses: dmarx/luria/actions/site@main       # stage + build, outputs a directory
- uses: actions/upload-pages-artifact@v3
  with:
    path: ${{ steps.site.outputs.path }}
```

**One step cannot be scaffolded.** Set Settings → Pages → Source to "GitHub
Actions" on the repository. Until you do, the deploy job fails with "Pages is
not enabled" while the build job stays green.

Nothing needs configuring beyond that: the site's title, its URL and the base
a link falls back to when it points at a repository file the site does not
publish all derive from your `issue_url`. `[luria.site]` exists to override one
of those, or to keep a directory of markdown out of the site
(`exclude = ["vendor/**"]`).

### Putting your own brand on it

Three optional keys, and the site wears your artwork instead of the
generator's:

```toml
[luria.site]
icon = "assets/brand/icon.svg"      # favicon: point at the vector master
logo = "assets/brand/lockup.svg"    # replaces the site title in the sidebar

[luria.site.theme.light]            # any of Quartz's colour names; the rest
light = "#f4f1e8"                   # stay the generator's
dark  = "#111111"
```

The favicon is **rasterized during the build**, from whatever you point
`icon` at — so the file you maintain is the vector one, and no derived PNG
sits in the repository going quietly out of date
([DP-3](design-principles.md#dp-3)). A name Quartz doesn't know is refused
and named, rather than dropped where you'd be left wondering why the colour
never took.

The logo is baked once per theme, because whether artwork can invert itself
is a *browser* question — a browser that carries the page's `color-scheme`
into an embedded SVG resolves the artwork's own dark-mode rules against the
site's toggle, and one that doesn't resolves them against the reader's
operating system, which the toggle has nothing to do with. If your artwork
exposes a `--luria-ink` custom property it is re-inked to match each theme
automatically; otherwise give it a `logo_dark` or accept one rendition in
both.

Run `luria site --out build/site` locally to see what would be published
before any of it ships. It prints what it staged and — the number worth
watching — how many links it could not place.

Two things are worth knowing about *what* it publishes. Pages land at their
repository paths, so the relative links `luria link --fix` already wrote keep
resolving and nothing re-derives them. And a file whose prose renders into a
view somewhere else — a changelog fragment, a journal entry, a
document-scheme source — is deliberately **not** published: its links are
spelled for the page it lands in, and that page is already on the site.

## What to expect

The first `luria lint` on an established project is not a clean bill of health,
and it isn't meant to be. It is the difference between what the convention said
and what the corpus does — which, in every case measured so far, has been
larger than anyone expected.

**The documents you bring with you are not frozen either.** A decision whose
choice still stands but whose reasoning has aged badly is corrected in place,
with a `version` bump and a `history:` entry saying what the old version
claimed — you do not have to retire a decision that is still in force in order
to fix a paragraph in it ([ADR-019](../record/decisions.d/ADR-019.md)). Luria's own record
has worked examples of every shape of revision; they are listed in
[project memory §2](project-memory.md).
