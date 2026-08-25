<div align="center">

<img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg" alt="luria" height="240">

[![CI](https://github.com/dmarx/luria/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dmarx/luria/actions/workflows/ci.yml)
[![the record, browsable](https://img.shields.io/badge/the%20record-browsable-6b7f9e)](https://dmarx.github.io/luria/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/github/license/dmarx/luria)](LICENSE)
<!-- luria:badges -->
[![needs decision: 11](https://img.shields.io/badge/needs%20decision-11-orange)](docs/reports/pending-decisions.md)
[![cited, not in force: 6](https://img.shields.io/badge/cited,%20not%20in%20force-6-orange)](docs/reports/reference-status.md)
<!-- /luria:badges -->

</div>

## Retract a premise, and the build tells you what rested on it

Write down why you decided something. Cite that decision by code wherever it
does work. Later, change your mind — mark it `Rejected`, or `Superseded`, or
`Deferred`.

Every place that leaned on it now fails the build.

```console
$ luria lint
luria: 2 warning(s) — retired documents cited unacknowledged
  ADR-012 is Superseded, cited 6× in 4 file(s) — Cache invalidation is time-based
  ADR-019 is Rejected,   cited 2× in 2 file(s) — Workers own their own retry policy
luria: 1 violation(s)
  docs/scaling.md:88: ADR-012 is not a link — run `luria link --fix`
```

Not "this file is out of date." *These four files argue from something you no
longer believe, and here they are.*

## This is a truth maintenance system

Not a metaphor. A [truth maintenance
system](https://en.wikipedia.org/wiki/Reason_maintenance) — Doyle, 1979 — holds
a set of beliefs together with the **justifications** linking them. Each node is
IN or OUT. Retract a belief, and the system propagates to every node whose
justification depended on it.

Luria is that, with three differences that make it usable by people:

- **The nodes are documents you wrote.** The justification graph is a side
  effect of citing premises by code instead of by paraphrase.
- **Propagation stops at a finding.** A classical TMS marks a node OUT
  automatically. Whether a withdrawn premise actually kills the argument
  resting on it is a judgment, so luria fails the build and waits for you.
- **Acknowledgement is first-class.** `<!-- inactive-ok: ADR-012 — the decision
  this one replaces -->` says *I know, and I mean it*. Most findings resolve
  that way, and a suppression that stops applying reports itself.

If you know the literature: a JTMS with linter-style suppressions, enforced in
CI. Retraction is AGM contraction. The industrial cousin is requirements
traceability with impact analysis. We say so plainly rather than inventing a
word — the reasoning is in [ADR-058](record/decisions.d/ADR-058.md).

## Why bother

A repository's real memory is not in its documentation. It is in the arguments
people had, the alternatives they rejected, and the constraints they found the
hard way — and that lives in review threads and in the heads of whoever was
there. When they leave, you re-litigate it. When an agent joins, it has no
access at all.

Writing decisions down is the well-known half. The half nobody does is **keeping
them honest**. Documentation rots not by becoming wrong but by staying
confidently right about a world that moved, and the only thing that reliably
stops it is a check. Every convention here governed by prose alone has drifted;
every one guarded by an executable check has held. That finding is
[DP-5](docs/design-principles.md#dp-5), and it is why this exists.

## Sixty seconds

```console
$ pip install luria
$ luria init            # scaffold record/ and docs/ into the current repo
$ luria new adr         # a decision, numbered and templated
$ luria link --fix      # a bare `ADR-004` in prose becomes a link
$ luria index           # regenerate every view from the frontmatter
$ luria lint            # exit 1, one line per violation
```

Then the [quickstart](docs/quickstart.md), which gets you to a real finding in
about fifteen minutes.

## What it looks like in a repo

```
luria.toml               what schemes exist, what gets scanned, what fails
record/                  the WRITE surface — hand-edited, one file per record
  decisions.d/
    ADR-001.md           frontmatter (status, title, tags) + prose
    _template.md         what `luria new adr` copies
    tags.yaml            what each tag means
    statuses.yaml        what each status means IN THIS SCHEME
docs/                    the READ surface — indexes, tag pages, reports
  decisions/README.md    generated; never hand-edited
  reports/               what is pending, what is cited but retired
```

You write in `record/`. Everything under `docs/` is derived, and a stale view
fails the lint rather than sitting there quietly wrong.

## More than decisions

`ADR` is one **scheme**, not the product. A scheme is a family of numbered
records with its own directory, template, tag vocabulary and status meanings,
and `luria.toml` is where you declare as many as you need.

One project reading a corpus of philosophical arguments runs six: claims,
arguments, concepts, positions, decisions, principles. Its arguments cite claims
as premises, so retiring a claim surfaces every argument built on it — the same
engine, pointed at a body of ideas instead of a codebase.

[Schemes](docs/schemes.md) covers designing your own.

## Documentation

| | |
|---|---|
| [Quickstart](docs/quickstart.md) | fifteen minutes, ending in a real finding |
| [Concepts](docs/concepts.md) | the model: records, status, citations, propagation |
| [Schemes](docs/schemes.md) | record families beyond decisions |
| [CLI reference](docs/cli.md) | every command and flag |
| [Configuration](docs/configuration.md) | every `luria.toml` key, generated from the schema |
| [The record](docs/record.md) | what *this* project configured, generated from `luria.toml` — the page every adopting project gets |
| [Directives](docs/directives.md) | the acknowledgement vocabulary |
| [Adopting](docs/adopting.md) | bringing luria to a repo that already has history |
| [In practice](docs/in-practice.md) | three real records compared, and what drove each choice |
| [Python API](docs/api.md) | using it as a library |
| [Project memory](docs/project-memory.md) | the doctrine: four layers, and what goes where |
| [Contributing](CONTRIBUTING.md) | how this repo works on itself |

## This repo eats its own cooking

The badges above are generated from this project's own record. `needs decision`
counts documents sitting at `Proposed` or `Deferred`; `cited, not in force`
counts references to retired documents nobody has acknowledged. They are
sometimes non-zero on purpose — a project whose own reports always read clean is
one whose reports are not wired to anything.

The [decision record](docs/decisions/README.md) is every choice this package
made and the alternatives that lost. The [devlog](docs/devlog/README.md) is what
went wrong on the way.

## License

MIT.
