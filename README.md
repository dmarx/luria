# Luria

[![CI](https://github.com/dmarx/luria/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dmarx/luria/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/github/license/dmarx/luria)](LICENSE)
<!-- luria:badges -->
[![needs decision: 0](https://img.shields.io/badge/needs%20decision-0-brightgreen)](docs/decisions/README.md)
[![cited but retired: 0](https://img.shields.io/badge/cited%20but%20retired-0-brightgreen)](docs/decisions/README.md)
<!-- /luria:badges -->

A project's memory: the decisions, the principles, the changelog and the
narrative log — kept where the next collaborator will find them, and kept honest
by a lint.

Half the collaborators on a modern codebase are stateless. They arrive with no
memory, read some pages, work, and vanish. Unwritten knowledge is re-derived at
cost, per session, forever. Luria is the machinery for a record that survives
that: [project memory](docs/project-memory.md) is the doctrine, and this package
is what stops it drifting.

```
pip install git+https://github.com/dmarx/luria      # not on PyPI yet
luria init --issue-url https://github.com/owner/repo/issues
luria index && luria lint
```

## What it does

| command | |
|---|---|
| `luria lint` | the only command that can fail: index completeness, frontmatter, a stale generated index, and references that should be links |
| `luria link --fix` | rewrites bare references as hyperlinks — the same scanner the lint reads, so the failure names its own remedy |
| `luria index` | regenerates every generated view from frontmatter — the decision index and its per-tag pages, the principles document |
| `luria ref-status` | which retired decisions are still cited, and where |
| `luria pending` | which documents are undecided, by age **and** citation count — every scheme |
| `luria badges` | the README's two counts, derived from the record |
| `luria reports` | both reports as markdown, for a CI artifact |
| `luria collect` | assembles fragment directories into their views |
| `luria remotes` | another project's record: how each foreign reference resolves, and whether it is reachable |
| `luria init` | scaffolds the record into a project that has none |

## The four layers

| layer | holds | test |
|---|---|---|
| design principles | standing **values**, numbered, citable and **versioned** | *have we re-derived this more than once?* |
| decisions | a **choice among alternatives** at a point in time | *did we reject an alternative, or set a constraint?* |
| changelog fragments | **what changed**, operator-facing | *would someone running this notice?* |
| devlog entries | **how it went**, including the wrong theories | *will a future debugger want the narrative?* |

Each contribution writes a *fragment* nobody else touches; the shared documents
are **views**. A file every contribution appends to is a lock, and its conflicts
carry no information ([DP-2](docs/design-principles.md#dp-2)).

Views come in two kinds, and the difference is whether the sources survive
([ADR-012](docs/decisions/ADR-012.md)). The changelog is **collected**: its
fragments are consumed, so the view can only be appended to. The decision index,
the principles document and the devlog are **generated** — a pure function of
sources that persist, which is the only reason `luria lint` can tell you one has
gone stale.

The devlog is a **journal**: entries are filed at their authoring timestamp
(`devlog.d/2026/08/03/211926.md`), never deleted, and rendered into one book per
month with a generated contents list ([ADR-020](docs/decisions/ADR-020.md)). A
dated observation was true when it was written and stays true; consuming it
throws away the only copy of something that never expires.

## Citing another project

A record extracted from another project cites it constantly, and an unprefixed
code can't mean both "ours" and "theirs". Register the remote once:

```toml
[luria.remotes.SG]
repo = "dmarx/strata-g"
```

and `SG-ADR-032` becomes a first-class reference — `luria link --fix` writes the
URL, `luria lint` demands it, and `luria remotes --check` says whether it still
resolves. A remote that names its files after their codes needs nothing else; one
whose filenames carry title slugs gets `luria remotes --refresh` once, which
discovers them into a committed lockfile so CI and offline checkouts resolve
identically ([ADR-016](docs/decisions/ADR-016.md)).

A citation can land before its URL does. Luria cites both `SG` (the pilot it was
extracted from, whose filenames haven't been converted yet) and `LU` (itself,
which the `luria init` scaffold points at). Naming the document is the durable
half and works immediately; the URL improves when the remote does
([ADR-017](docs/decisions/ADR-017.md)).

## Why a lint

Because the same audit result keeps recurring: **every documentation surface
with an executable guard held; every surface governed by prose alone had
drifted.** Not toward one wrong value — toward *variety*, which is worse,
because a reader can't learn what the convention is.

So the norms that matter get walked up the ladder — prose → convention →
mechanism → guarantee ([DP-5](docs/design-principles.md#dp-5)) — and this
package is the last rung.

## Provenance

Every rule here was earned in
[strata-g](https://github.com/dmarx/strata-g), where the machinery was built and
run before it was extracted. The principles and decisions name the incidents
that produced them, because a rule whose evidence is missing reads as taste, and
taste gets re-litigated ([ADR-009](docs/decisions/ADR-009.md)).

Luria runs its own machinery on its own record — the decision index and the
principles document in this repo are both generated by `luria index`, and these
files are linted by `luria lint`. That is not tidiness: it is how the first
consumer to hit a bug is this repo.

## Docs

- [Project memory](docs/project-memory.md) — the doctrine
- [Design principles](docs/design-principles.md)
- [Decisions](docs/decisions/README.md)
- [Comment directives](docs/directives.md) — `inactive-ok`, `unexempt`
- [Adopting Luria](docs/adopting.md)

MIT.
