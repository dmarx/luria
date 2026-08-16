# Contributing

This repository uses luria on itself. That is not a demo — it is how the project
is maintained, and it means a contribution here has one requirement most repos
do not have: **the reasoning ships with the code.**

## Before anything else

Read [the design principles](docs/design-principles.md) in full. They are the
standing values every choice here is judged against, and reviews cite them by
number.

Then [project memory](docs/project-memory.md), which is the doctrine behind the
layout.

## The loop

```console
$ git checkout -b your-branch
$ pip install -e .
# ... make the change ...
$ luria new changelog                  # one fragment per contribution
$ luria link --fix
$ luria index
$ luria lint
$ python -m pytest tests -q
```

`pytest tests -q` plus `luria lint` is exactly what CI runs.

## Four ground rules

**Work goes to a branch and a pull request, never straight to `main`.** The
record is the deliverable, and it needs a chance to be read before it becomes
what the project believes.

**File the fragment in the same contribution as the work.** `luria new
changelog`, and a devlog entry if anything went wrong on the way. A fact filed
while its context is loaded costs a paragraph; re-derived cold, it costs a
session. No user-facing change? Replace the fragment with a comment saying why —
a stub collects to nothing, which keeps the rule enforceable without inventing
an entry.

**Never hand-write a link target.** Write the bare code — `ADR-035`, `DP-6`,
`#57` — and let `luria link --fix` spell it. Record prose is rendered into views
in other directories, so a target has to resolve from where the text lands, not
where it lives, and only the fixer knows that frame. Want prose as the label?
`[[ADR-035|the escalation ladder]]`, still the fixer's job. A hand-written
target that looks right here is wrong somewhere.

**A guard that keeps catching you is a bug report about the workflow.** One
catch is the net working. The same catch again means the hazard is upstream — a
practice, a missing affordance, an undocumented rule — and the fix is to remove
what *generates* the mistake, not to keep thanking the net. Quiet guards are the
goal; a busy one is compensating for something.

## When a change needs a decision

Most do not. Write one when you rejected an alternative, chose a constraint, or
made something a future edit could silently violate.

```console
$ luria new adr
```

File it `Proposed` if it is genuinely open; `Active` if you are making the call
and the PR is where it gets challenged. The template explains every field —
read it once, then delete the parts you have internalised.

**One decision, one thing.** If your change has two unrelated halves, that is
two decisions and probably two PRs. A record with two halves is one nobody can
cite half of.

## Adding a check

A new check joins the **lint** only if the violation is always wrong *and*
mechanically fixable. Otherwise it is a **report** — a named class, warned by
default, promotable through `[luria.lint] fail_on`.

That distinction is load-bearing. A lint failure says "this is broken, here is
the fix"; a report says "this needs a human". Getting it wrong in either
direction is how a tool becomes something people route around.

**Fire any new guard once before trusting it**, and say so in the devlog: what
you broke, what the guard printed, what it printed after the repair. Provisioned
is not working. A guard that has never fired is one nobody can distinguish from
a guard that cannot.

Point it at a real record, not only a fixture. The most useful bug reports this
project has had came from running a new check against a downstream adoption and
finding things the author of the check did not expect — including, twice, bugs
in the shipped templates.

## Tests

Live in `tests/`, one file per subject. Two conventions worth knowing:

**Every test states its own vocabulary.** A fixture that borrows a live
sequence's prefix is the hazard the fixture-code rule exists for, so tests use
`VP`, `NT` and similar rather than `ADR`.

**Say why the test exists**, especially for the non-obvious ones. Several tests
here exist because of a specific bug, and the docstring naming it is what stops
a future tidy-up from deleting the guard along with the redundancy it looks
like. The load-bearing ones say which refactor would break them.

## What gets rejected in review

- A change with no record fragment.
- A hand-written link target.
- A generated file edited by hand.
- A new check that should have been a report.
- A decision that bundles two choices.
- A guard added without firing it once.

None of these are style preferences. Each is a failure mode that has cost this
project a session, and most have a decision record naming the incident.

## Releasing

Version comes from the git tag via `hatch-vcs`; there is no version string to
edit. Tag, and the published package derives from it.

`luria collect --commit` assembles the changelog fragments into `CHANGELOG.md`.
It runs on a cadence rather than on every merge, so fragments accumulate between
releases and the assembled file is not a lock every branch must touch.
