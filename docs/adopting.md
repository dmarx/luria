# Adopting Luria

Putting a record into a project that already exists — and the CI that keeps
it running without anyone's attention.

## Whether this fits

Worth answering before the scaffold, because the honest answers rule some
projects out.

**What makes it pay.** A record earns its keep when decisions get cited and
then change. A project with a handful of choices nobody refers back to is
paying the filing cost for a graph with no edges. The threshold is not size or
age — it is whether anything ever says *because*.

**What if nobody moves a status?** Then nothing propagates, and Luria
degenerates into a documentation generator with a linter. That failure is
detected rather than assumed: a scheme where every document shares one status
is reported as `inert-status`, on the grounds that a green build then means
only that nothing is being judged. If you expect never to retire anything, you
do not need this.

**What should stay ordinary prose?** Most of it. A getting-started guide, an
API reference, a design sketch — none has an identity worth citing or a
standing that can change, and putting them in a scheme buys nothing.
[Designing a record](modeling.md#identity-standing-relation) is the test.

**How much machinery does adoption add?** A scaffold is around twenty files:
one directory and template per family, a stub per view, a docs index, an agent
context file, and two GitHub Actions workflows. `luria init --dry-run` lists
them before anything is written. The generated views grow with the record; the
CI is two jobs, one of which commits regenerated views back.

**What is GitHub-specific?** The shipped workflows and the Pages publishing
path. The `issue_url` inference recognises GitHub and GitLab. Everything else
— the record, the checks, the generated views, `luria site`'s output — is
plain files and plain Git, and the CI is two ordinary jobs that any runner can
express. A GitLab or self-hosted project writes its own workflow and loses
nothing else.

**What is most likely to change?** The two things this record is least settled
about: how a scheme's view is named (`render = "index" | "document"` describes
output where the choice is about reading), and the migration machinery, which
has run on real records only a handful of times. Both are recorded as
decisions rather than as intentions, so a change to either arrives as a
superseding decision you can read.

## Scaffold

```console
$ pip install luria
$ luria init --issue-url https://github.com/you/yourproject/issues
```

`--issue-url` can be left out where `origin` points at GitHub or GitLab —
init infers it, and with it the site's title, Pages URL and source base.

`init` writes only what is missing — an existing `docs/README.md`,
`CLAUDE.md`, or `luria.toml` is skipped and reported, never overwritten —
so it composes with whatever documentation you already have. If you keep
your own `CLAUDE.md`, borrow the scaffolded shape: a short map pointing at
the record's docs, plus an invitation to run `luria --help`, beats a copy
of either.

Then build the views and take stock:

```console
$ luria index
$ luria lint
```

A fresh scaffold lints clean. From here the work is habits, not setup:
file entries with `luria new` in the same branch as the work they
describe, and let CI do the rest.

## Shape the record to the project

The scaffold ships decisions, principles, a changelog, and a devlog.
None of that is fixed — the families in `luria.toml` are yours to name
(see [project memory](project-memory.md) and the
[configuration reference](configuration.md)). The `examples/` directory in
the Luria repository holds small, CI-tested configurations worth stealing
from:

- **collocated** — decisions living beside the docs, no `record/` split,
  for a small project.
- **rfcs-and-specs** — two schemes: RFCs rendered as an index, specs
  concatenated into a single interfaces page.
- **many-journals** — a devlog, an incident log, and meeting notes side by
  side with different granularities.
- **external-citations** — arXiv, Jira, and CVE identifiers as first-class
  linted references via `uid` remotes.
- **knowledge-base** — two schemes of *domain* content citing each other,
  with required fields and a one-primary-category rule: a record that is not
  project meta-documentation at all.

Shaping the record is a design question before it is a configuration one —
[designing a record](modeling.md) is the guide; if your material already
exists as data, [importing an existing corpus](importing.md) covers the
transform.

Two settings earn attention early:

- `[luria.code] globs` — which *source files* are scanned for references.
  A decision code in a code comment is the strongest form of the record's
  claim (it is the stated reason the code is shaped that way), and scanning
  makes it a checked claim.
- `[luria.lint] fail_on` — which warning classes fail the build. Start
  empty; promote a class once the report for it is clean and you want it
  to stay that way.

## CI

`init` scaffolds two workflows built on composite actions published from
the Luria repository. What they do, so you can rearrange them:

### `docs.yml` — generate, then lint

1. **`dmarx/luria/actions/generate`** runs `luria link --fix` and
   `luria index`, commits any diff as `github-actions[bot]` with a
   `[skip ci]` message, pushes, and outputs the resulting SHA. On a fork
   PR it cannot push; it outputs the unregenerated SHA so the downstream
   lint fails informatively instead of the job dying on a 403. With
   `concretize: true` — pass it only on push-to-main runs, never on PRs —
   it first runs `luria concretize`, assigning real numbers to any
   merge-allocated temporary codes now that merges have serialized.
2. **`dmarx/luria/actions/lint`** checks out that SHA, runs `luria lint`,
   then writes the status reports and uploads them as an artifact whether
   or not the lint passed.
3. A scheduled job (weekly, in the scaffold) runs `luria collect --commit`
   to assemble changelog fragments and pushes the result.

The generate/lint split matters: a checking job that regenerates views
in-place would be comparing its own output against itself. Generation
commits; the check reads the commit.

Two hazards, both found by adopting this into a repository that already had
generators of its own.

**Anything else that commits to the branch defeats the handoff.** The lint
reads the SHA generation produced; a second workflow that renders something
and commits *after* it makes that SHA no longer the tip, and the branch now
has a commit nothing checked. The symptom is a pull request showing green
checks that belong to an earlier commit. If your repository already builds a
README, a diagram, or a lockfile, fold it into the generate job — render
without committing, and let the generate action's `git add -A` carry it into
the one commit:

```yaml
- name: Render the README from its templates
  run: |
    pip install your-generator
    your-generator build --commit=false
- id: generate
  uses: dmarx/luria/actions/generate@0.4.2
```

Give any bot commit you cannot fold in the skip marker of its own, for the
reason below.

**A commit message that contains the skip marker skips that commit's CI**,
including when the message is merely *describing* the convention. Write about
it in prose — "the skip marker", not the literal token — in commit messages,
PR descriptions, and squash-merge bodies. This one is worth knowing precisely
because of how it presents: not as a failing build but as *no* build, with
the pull request still displaying the previous commit's green checks.
Silence is indistinguishable from success unless you check which commit the
green belongs to.

### `pages.yml` — publish the site

**`dmarx/luria/actions/site`** runs `luria site`, then builds the staged
vault with a pinned [Quartz](https://quartz.jzhao.xyz/) (v4 — bump the pin
deliberately; the generated config targets its plugin API) and hands the
HTML to `actions/upload-pages-artifact` / `actions/deploy-pages`.

## The published site

`luria site` stages every publishable markdown page at its repository
path, which is what lets the record's ordinary relative links keep
resolving with no second link-resolution system:

- The root `README.md` becomes the landing page (and still answers to its
  old name via an alias).
- Each scheme document gets its code as an alias, so `/ADR-012` finds it.
- A **record line** — status, version, filing date, issue, influences, and
  the document's typed edges both ways (what it supersedes, what it
  influenced, what a declared reference names and who names it) — is
  injected under each document's title from the record's frontmatter.
- Links to files that are not published (source code, for instance) are
  retargeted to the repository on GitHub; images are staged alongside
  their pages.
- Readers get full-text search, backlinks on every page, and a local graph
  of each document's neighbourhood — a record this cross-cited is a graph,
  and the site shows it.

Branding and colours come from `[luria.site]`: an icon, a logo (with an
optional dark variant, or a single SVG re-inked per theme), and a
light/dark palette. Every key defaults from `issue_url` for a GitHub
project, so the conventional case needs no `[luria.site]` table at all.

## Adopting into an agent workflow

The record is as much for coding agents as for people: an agent that can
run `luria --help`, read the generated views, and file entries with
`luria new` inherits the project's memory instead of re-deriving it. The
scaffolded `CLAUDE.md` encodes the working agreement — file fragments with
the work, never hand-write link targets, treat a repeatedly-firing guard
as a bug report about the workflow — and the lint enforces the parts a
machine can check.
