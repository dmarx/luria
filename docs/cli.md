# CLI reference

Every command takes `--help`, and `luria --help` lists what is available in your
version. This page is the map and the reasoning; `--help` is the authority on
flags.

## The loop

Four commands cover most days:

```console
$ luria new adr         # scaffold a record
$ luria link --fix      # bare codes in prose become links
$ luria index           # regenerate every view
$ luria lint            # exit 1, one line per violation
```

`link --fix` before `index` before `lint`. In CI the order is enforced for you
by the actions.

---

## `luria lint`

Check the record. Exit 0 when clean, 1 with one line per violation.

Two kinds of output, and the difference matters:

**Violations** always fail. A stale generated view, frontmatter that will not
parse, a title that disagrees with its heading, a bare reference the fixer
would link, a wikilink that resolves to nothing.

**Warnings** never fail unless you ask. Citations of retired documents, codes
that resolve to nothing, hand-written URLs, dead relative targets, stale
directives, a scheme whose status never varies, a count of undecided documents.
Each belongs to a named class:

```toml
[luria.lint]
fail_on = ["retired-citations", "unresolved-codes"]
```

Promoting a class makes its *unacknowledged* rows fail. Acknowledged rows never
fail, so the escape hatch survives enforcement — the dial changes the
consequence, not the accounting.

Start with everything reported. Promote a class the day your record is clean on
it, and you will never have to declare bankruptcy on the whole thing at once.

## `luria link [PATHS...]`

Rewrite bare references as links. Without `--fix` it reports what would change.

```console
$ luria link --fix
docs/scaling.md: 3 reference(s)
linked 3 reference(s) in 47 file(s)
```

Handles local codes (`ADR-012`), foreign codes from declared remotes
(`LU-ADR-013`), design principles (`DP-6`), issue numbers (`#42`), and wikilinks
(`[[ADR-012]]`, `[[ADR-012|the caching decision]]`).

**This is the only thing that should write a link target.** Record prose renders
into views in other directories, so the correct depth depends on where the text
*lands* — and only the fixer knows that frame. Write the bare code.

It deliberately does not touch: codes inside backticks or fences (a specimen is
not a citation), a code that resolves to nothing, self-references, and a low
`#N` that might be a principle number rather than an issue.

## `luria index [--check]`

Regenerate every view from the frontmatter: scheme indexes and tag pages,
document-rendered schemes, journal books, the status reports, the configuration
reference, the README badges.

`--check` exits 1 naming stale files instead of writing them — what CI runs when
it wants to fail rather than fix.

Never hand-edit a generated view. Edit the record and regenerate.

## `luria new KIND [--title ... --status ... --tags ...]`

Scaffold a record and print its path. `KIND` defaults to the journal; the others
come from `luria.toml` — every scheme prefix, fragment directory and journal is
a kind, so `luria new rfc` works the moment `[luria.schemes.RFC]` is declared.

The field flags are conveniences. Content belongs in your editor.

Which identity you get depends on the scheme's `allocate`: the next free number
(default), or a temporary code that `luria concretize` numbers later.

## `luria concretize [--check]`

Assign real numbers to temporary codes and rewrite every citation of them.

Run it **where merges serialize** — the push to the default branch — and never
on a pull request, since concretizing on a branch is exactly the premature
number claim temporary codes exist to avoid.

`--check` exits 1 naming any temporary codes that exist. That is the trunk
guard: a temp code on the default branch means this did not run.

## `luria reports [--out DIR]`

Write the status reports as markdown: what is pending, and what is cited but not
in force. `luria index` does this too; the standalone command is for CI staging
directories.

## `luria collect [--dir D] [--commit]`

Assemble fragment directories into their documents — a changelog from
`record/changelog.d/`, a digest from wherever you put one.

Fragments exist so the assembled file is not a lock every branch must touch.
Collect on a cadence, not on every merge.

## `luria skip-markers [--rev-range R] [--strict]`

Report commits whose message carries a CI skip marker **in its body** — a
message *describing* the convention contains the marker, and so tells the forge
not to build the commit that describes it.

Position is the whole rule, and it is what keeps this quiet enough to be worth
running. A deliberate skip goes in the subject line or a trailer, which is where
every tool that generates one puts it — the `generate` action's own
`docs: regenerate views [skip ci]` included, which is why no author check is
needed. A marker anywhere else was almost certainly prose.

Prints nothing when there is nothing to say, warns rather than fails, and says
nothing at all when it cannot read history — a depth-1 checkout is the ordinary
case, and a build should not break on a checkout setting. `--strict` exits 1 for
a project that wants it enforced.

This is a backstop, not a fix: the run it warns on is a **later** one, because
the suppressed commit's own run is precisely what did not happen. What it
converts is silence into a message — and silence is the reason the failure is
hard to spot, since a suppressed build is not a red check but *no* check, with
the previous commit's green still on display.

The `lint` action runs it; give that job's checkout a `fetch-depth` covering the
range, or it has nothing to read.

## `luria init [--config PATH] [--dry-run] [--issue-url URL]`

Scaffold the record a config declares. Never overwrites, so it is safe in a repo
that already has files, and `--dry-run` lists what it would write.

By default it scaffolds the detected root's own config, or the shipped template
if there is none. `--config PATH` installs that file as `luria.toml` and
scaffolds *its* shape — how you clone a record layout between projects.

## `luria migrate SPEC [--dry-run] [--commit]`

Execute a migration: rename a scheme, move documents between schemes, without
losing the record's memory of where things were. `--dry-run` prints the plan;
`--commit` commits the result and appends it to `.git-blame-ignore-revs` so the
mechanical change does not bury authorship.

## `luria remotes [--refresh] [--check]`

How each configured remote's cited references resolve. `--refresh` discovers
code→filename maps into the lockfile. `--check` HEADs every constructed URL —
needs network, and is a report rather than a failure, because someone else's
outage is not your build's problem.

## `luria site [OUT]`

Stage the record as a Quartz vault — `content/` plus config — ready for
`npx quartz build`. A build step over the record as it stands; it changes
nothing.

---

## In CI

```yaml
jobs:
  docs:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: dmarx/luria/actions/generate@main
        with:
          pip-spec: luria==0.5.0
          concretize: ${{ github.event_name != 'pull_request' }}
      - uses: dmarx/luria/actions/lint@main
        with:
          pip-spec: luria==0.5.0
```

`generate` regenerates and commits the views, so a contributor who forgets
`luria index` does not fail the build for it. `lint` then checks the result.

**Pin `pip-spec` on both, to the same version.** Taking the action from `@main`
while the package comes from PyPI is a version split inside one dependency: CI
generates with an older generator than your record is written against, reverts
your committed views on every push, and the next contribution opens by resolving
the same conflict.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | clean, or warnings only |
| 1 | at least one violation, or a `fail_on` class with unacknowledged rows |
