# Adopting luria

Bringing this to a repository that already has history — code, opinions, and
documentation somebody wrote two years ago.

The short version: **start with one scheme and zero enforcement**, get the
generated views committed, then turn dials up one at a time. The failure mode is
adopting everything at once, drowning in findings on day one, and concluding the
tool is noisy.

## Before you start

You need one thing that is not technical: a **question the record should be able
to answer**. "What did we decide about X, and does it still hold?" is a good
one. Without it you will produce a directory of files nobody reads, which is
what most documentation efforts produce, and luria will not save you from that.

The tool's value is the propagation. If nothing will ever be retired, you want a
static-site generator.

## 1. Scaffold

```console
$ pip install luria
$ luria init --issue-url https://github.com/you/repo/issues/{n}
$ luria index
$ luria lint
```

`init` never overwrites, so it is safe. `--dry-run` lists what it would write.

Commit that before writing any content. It is a small, reviewable diff, and it
separates "we adopted a tool" from "we wrote down what we believe".

## 2. The layout

```
luria.toml                  paths, issue URL, code globs, schemes
docs/                       the READ surface: prose plus every generated view
  README.md                 the index a reader lands on; hand-written
record/                     the WRITE surface: every source, marked `.d`
  decisions.d/
    _template.md            what `luria new adr` copies
    README.stub             the index's prose; renders to docs/decisions/
    tags.yaml               tag order and blurbs
    statuses.yaml           optional: which statuses this scheme uses, and what they mean
  principles.d/
    _template.md
    README.stub             renders to docs/design-principles.md
    DP-00N.md               seeded with the ones that earn this machinery
  changelog.d/_template.md  one fragment per contribution; collected, then consumed
  devlog.d/_template.md     the shape of a journal entry
.github/workflows/
  docs.yml                  regenerate views, lint them, collect fragments on a cadence
```

You write in `record/`. Everything luria owns under `docs/` is generated.

## 3. Backfill, or don't

The tempting first move is to write up every decision the project ever made.
Resist it. Retrospective decisions are the worst records you will ever write:
you no longer remember the alternatives, so the section that matters most comes
out empty, and you produce fifty records nobody cites.

Two better options:

**Write the ones that are still being re-litigated.** If a question comes up
every few months, that is a decision with no record. Ten of those beats a
hundred archaeological ones.

**Write forward.** Adopt the rule that a non-obvious choice gets a record when
it is made, and let the corpus accumulate. Six months of that is a real record;
a weekend of backfill is a directory.

Either way, when you *do* write one retrospectively and cannot reconstruct the
alternatives, say so in the record. "Reconstructed in 2026; the alternatives are
not recoverable" is worth more than a confident invention.

## 4. Say what your statuses mean

The five words are fixed. What they mean is yours, and this is the cheapest step
with the highest payoff:

```yaml
# record/decisions.d/statuses.yaml
Active:
  label: In force
  blurb: the current answer; change it by superseding, not editing
Superseded:
  label: Replaced
  blurb: a later decision re-decided this; the note names it
Rejected:
  label: Declined
  blurb: considered and turned down — the reasoning is why this is kept
```

It renders above the index table, so a reader learns what your column means
without finding the decision that says so. It also *narrows*: a record whose
status the scheme does not declare fails the lint.

Do this on day one. The most common failure in this system is a scheme where
everything sits at `Active` forever because nobody ever said what else would
mean, and by the time you notice, the propagation has never once run.

## 5. Start citing

The habit that makes everything else work: **cite the decision where it does
work.** In a module docstring, in a review comment, in another decision.

```python
# Retries are the worker's own business, not the queue's (ADR-019).
```

Then:

```console
$ luria link --fix
```

Point `[luria.code] globs` at whatever should be scanned — source, docs, both:

```toml
[luria.code]
globs = ["src/**/*.py", "docs/**/*.md"]
historical = ["CHANGELOG.md"]
```

`historical` is for files that are true about the day they were written and
never retroactively wrong. A changelog citing a since-retired decision is not a
defect; it is a record of what was true then.

## 6. Turn enforcement up, one class at a time

Everything is reported before it is enforced. When a class reads clean, promote
it:

```toml
[luria.lint]
fail_on = ["retired-citations"]
```

Suggested order, roughly by how much cleanup each costs:

1. `unresolved-codes` — usually typos, cheap
2. `broken-targets` — mechanical
3. `retired-citations` — the one you came for
4. `pending-documents` — only if you want an SLA on undecided things

Nothing forces you past step three, and most projects should not go there.

## 7. CI

```yaml
- uses: dmarx/luria/actions/generate@main
  with:
    pip-spec: luria==0.5.0
    concretize: ${{ github.event_name != 'pull_request' }}
- uses: dmarx/luria/actions/lint@main
  with:
    pip-spec: luria==0.5.0
```

Generate before lint. The generate action commits the regenerated views, so a
contributor who forgets `luria index` does not fail the build for it.

**Pin `pip-spec` on both, to the same version.** Taking the action from `@main`
while the package comes from PyPI is a version split inside one dependency, and
it produces a specific, recurring symptom: CI regenerates every view with a
different generator than yours, reverts your committed views on push, and the
next contribution opens by resolving the same conflict. Three rebases in one
session is how this gets noticed.

## 8. Tell your agents

If AI agents work in this repo, the record is most of what they need and none of
what they will find by default. Put a map in `CLAUDE.md` or `AGENTS.md` — a map,
not a copy, since a copy drifts:

- run `luria --help` for the current command surface
- work goes to a branch and a pull request
- file the record fragment in the same contribution as the work
- never hand-write a link target; write the bare code and run `luria link --fix`

That last one matters more than it looks. An agent will compute a relative path
confidently and correctly for the wrong frame, and it is invisible until
something checks it.

## Common first-week problems

**"Everything is `Active`."** Expected, and the thing to fix. Nothing has been
retired because nothing has been reconsidered yet. If it persists past a few
dozen records, `luria lint` will say so — that is the `inert-status` report, and
it means the enforcement you configured cannot fire.

**"The findings are all legitimate."** Also expected in the first wave, and
what `inactive-ok:` is for. Acknowledge with a reason. If you find yourself
acknowledging the same shape repeatedly, that is a signal about the shape, not
about the tool.

**"CI keeps reverting my generated files."** Version split; see step 7.

**"A guard keeps catching me."** One catch is the net working. The same catch
repeatedly means the hazard is upstream — a missing affordance, an undocumented
rule — and the fix is to remove what *generates* the mistake. Quiet guards are
the goal.

## Where to go next

- [Quickstart](quickstart.md) — the fifteen-minute version, on a scratch repo.
- [Schemes](schemes.md) — once one scheme is working and you want a second.
- [Concepts](concepts.md) — the model and its prior art.
