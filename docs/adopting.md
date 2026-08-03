# Adopting Luria

## Install and scaffold

```
pip install luria
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
luria index     # build the decision index from frontmatter
luria lint      # should be clean
```

## What you get

```
luria.toml                  paths, issue URL, code globs, reference schemes
docs/
  decisions/
    _template.md            copy this to make a decision
    README.stub             the index's prose; the index itself is generated
    tags.yaml               tag order and blurbs
  design-principles.md      seeded with the ones that earn this machinery
changelog.d/_template.md    one fragment per contribution
devlog.d/_template.md       optional; significant work only
CLAUDE.md                   a bootloader section pointing at the above
```

## Adopting into a project that already has decisions

Point `luria.toml` at wherever they live and run `luria lint`. Expect failures
on the first run — that is the machinery telling you what the prose convention
had been letting through. Two are usual:

- **Frontmatter.** If your decisions use a prose `**Status:**` header, they need
  frontmatter ([ADR-003](decisions/adr-003-status-vocabulary-and-frontmatter.md)).
  Migrating is mechanical; the audit that motivated the closed vocabulary found
  thirty distinct spellings across 121 files, so budget for a normalizing pass.
- **Bare references.** `luria link --fix` writes them all. In the corpus this
  package was extracted from that was 2,246 references across 160 files. Read a
  sample of the diff rather than trusting it wholesale — that is how the
  code-span bug in [ADR-005](decisions/adr-005-references-are-hyperlinks.md) was
  caught.

Everything else is a warning and can wait
([ADR-007](decisions/adr-007-status-is-reported-not-enforced.md)).

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
([ADR-002](decisions/adr-002-fragments-and-generated-views.md)):

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
