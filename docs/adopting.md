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
([ADR-012](decisions/ADR-012.md)).

## What you get

```
luria.toml                  paths, issue URL, code globs, reference schemes
docs/
  decisions/
    _template.md            copy this to make a decision
    README.stub             the index's prose; the index itself is generated
    tags.yaml               tag order and blurbs
  principles/
    _template.md            copy this to make a principle
    README.stub             the document's prose; the rest is generated
    DP-00N.md               seeded with the ones that earn this machinery
changelog.d/_template.md    one fragment per contribution
devlog.d/_template.md       optional; significant work only
CLAUDE.md                   a bootloader section pointing at the above
```

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
  frontmatter ([ADR-003](decisions/ADR-003.md)). Migrating is mechanical; the
  audit that motivated the closed vocabulary found thirty distinct spellings
  across 121 files, so budget for a normalizing pass.
- **`title:`.** Every document needs one, and it has to match the body's `#`
  heading ([ADR-013](decisions/ADR-013.md)). Lift it from the heading in a
  single pass — that is where the generator used to read it from.

  Renaming the files to `ADR-<NNN>.md` is *not* required and is not linted:
  Luria writes the short form and reads `adr-010-a-slug.md` too, so adoption
  isn't a rename-everything-first proposition. Do it when you want the filename
  to stop being a third copy of the title; expect to rewrite every inbound link
  in the same commit.
- **Bare references.** `luria link --fix` writes them all. In the corpus this
  package was extracted from that was 2,246 references across 160 files. Read a
  sample of the diff rather than trusting it wholesale — that is how the
  code-span bug in [ADR-005](decisions/ADR-005.md) was caught.
- **A hand-written principles document.** Split it: one `DP-NNN.md` per
  section, `## N. Title` back up to `# DP-NNN: Title`, and the `README.stub`
  keeping the prose that came before them. Set every `version: 1` except the
  ones you know were reworded — those are the interesting ones, and `history:`
  is where the rewording goes. Until you split it, leave the DP scheme out of
  `luria.toml` and the document stays hand-maintained; links to `#N-the-heading`
  keep resolving either way.

Everything else is a warning and can wait
([ADR-007](decisions/ADR-007.md)).

## Citing another project

A record extracted from — or working alongside — another project cites it
constantly, and an unprefixed code can't mean both "ours" and "theirs".
Register the remote and cite it with a prefix
([ADR-016](decisions/ADR-016.md)):

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

- **A remote that follows [ADR-013](decisions/ADR-013.md) needs no lockfile** —
  the code *is* the filename, so the URL is exact with nothing to refresh. The
  lockfile exists for records whose filenames carry title slugs, where no
  template can turn `032` into `adr-032-a-long-title.md`; `--refresh` reads
  those from the remote once and commits them.
- **Discovery reads public repositories, over HTTPS, with no credentials.** A
  remote Luria can't read is told so and left on the code-only convention. If
  that is wrong for your remote, give it a `url` template — the answer to an
  unreadable remote is configuration, not a credential path CI can't reproduce.
- **A citation can land before its URL does.** If the remote hasn't adopted
  the code-only filenames yet, register it anyway and cite it: naming the
  document is the durable half, and the links start working when the remote
  converts, with no edit on your side ([ADR-017](decisions/ADR-017.md)).
- **`--check` reports, it never fails a build**, and it is never part of
  `luria lint`. It also can't distinguish "the document was deleted" from "this
  repo is private and you are anonymous", so it probes the repository once and
  says *unverifiable* rather than inventing a shelf of 404s.

## Badges that can be wrong

Two numbers are worth putting on a README, because they are the ones a reader
can't get any other way and both can turn amber
([ADR-018](decisions/ADR-018.md)):

```
<!-- luria:badges -->
<!-- /luria:badges -->
```

Add that region anywhere in `README.md` and `luria index` fills it with
**needs decision** (`Proposed` + `Deferred`, every scheme) and **cited but
retired** (retired documents still cited without an acknowledgement). The
counts are baked into the URLs, so there is no service to configure and no
committed JSON to keep current — and `luria lint` fails when the region
disagrees with the record.

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

Collection runs on a cadence, **not on every merge** — a per-merge bot commit
races in-flight rebases, reintroducing the conflict fragments exist to remove
([ADR-002](decisions/ADR-002.md)):

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
