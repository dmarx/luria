# Adopting Luria

## Install and scaffold

```
pip install git+https://github.com/dmarx/luria      # not on PyPI yet
cd your-project
luria init --issue-url https://github.com/owner/repo/issues
```

`luria init` never overwrites. Existing files are reported as skipped, so
running it on a project that already has half the record adds only the missing
half — and running it twice is a no-op. A scaffolder that clobbers is one nobody
dares re-run, which means the thing it is best at (filling in what a project
grew past) never gets used.

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
  principles.d/
    _template.md            copy this to make a principle
    README.stub             the document's prose; renders to docs/design-principles.md
    DP-00N.md               seeded with the ones that earn this machinery
  changelog.d/_template.md  one fragment per contribution; collected, then consumed
  devlog.d/_template.md     the shape of a journal entry; optional, significant work only
CLAUDE.md                   a bootloader section pointing at the above
```

The split is [LU-ADR-021](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-021.md):
you read in `docs/`, you file in `record/`, and a view directory holds only
what the generator wrote — the lint enforces all three.

Delete the seed principles you disagree with — a principle nobody believes is
worse than an empty file. Keep the ones you keep *honest*: replace each
`origin:` note with your own first instance, because a rule whose evidence is
missing reads as taste, and taste gets re-litigated by the next person with
different taste.

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
([ADR-007](../record/decisions.d/ADR-007.md)).

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

```yaml
- run: pip install luria
- run: luria lint
- run: luria reports
  if: always()
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: doc-reports
    path: build/doc-reports/
```

`if: always()` on the reports is the point: they are most wanted when the lint
failed.

**Nothing that writes belongs in that job**, and this is the one invariant here
worth stating as a rule rather than an example
([ADR-029](../record/decisions.d/ADR-029.md)). `luria lint` verifies generated
views by re-rendering them and diffing against what is on disk, so a
`luria index` step ahead of it makes the comparison vacuous — the check
compares the generator's output against the generator's output, and **stops
being able to fail**, for the index and the books as much as the badges.

The trap is that the failure it produces is a *green check*, and that the
tempting moment to add the step is exactly when the lint has gone red saying
`stale — run luria index`. That instruction is for your working copy. Luria now
says as much when the message is being read in a build, and warns when a
generator writes inside CI at all — but the rule is the durable half:

```yaml
- run: luria index   # ← never here. It disables the check below.
- run: luria lint
```

An adopter shipped exactly that, cleared a red build with it, and ran for three
green builds with the badge region still empty and the staleness gate dead.
Regenerating is an author's job; CI's job is to disagree.

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
