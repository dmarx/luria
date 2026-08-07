<div align="center">

<img src="assets/branding/luria-brainslug/luria_project_memory_lockup_horizontal.svg" alt="luria"  height="240">

[![CI](https://github.com/dmarx/luria/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dmarx/luria/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/github/license/dmarx/luria)](LICENSE)
<!-- luria:badges -->
[![needs decision: 0](https://img.shields.io/badge/needs%20decision-0-brightgreen)](docs/decisions/README.md)
[![cited but retired: 0](https://img.shields.io/badge/cited%20but%20retired-0-brightgreen)](docs/decisions/README.md)
<!-- /luria:badges -->

</div>

A simple framework for accumulating domain knowledge by leveraging time tested change management strategies.

Luria encapsulates a collection of best practices you should probably be using anyway. Things like:

* maintaining a journal to document your daily activities
* documenting decisions along with their context, alternatives considered, and citations to other relevant decisions
* a mechanism for un-endorsing decisions
* lineage tracking that facilitates identifying assumptions that are based on premises that are no longer endorsed
* a self-reenforcing feedback loop to surface unwritten rules or principles which should be documented and formalized
* tools that facilitate translating (inert) good intentions into (actively interventional) mechanisms

The consequence is that if you integrate luria into your project, the project itself will become its own living memory.


## How It Works

Luria is comprised of four documentation subsystems designed to reference one another, a linter for ensuring those references haven't gone stale,
and some convenience tools for interfacing with the linter and documentation subsystems.

The heart and soul of luria is the **decision record**. If you take away nothing else from reading this: ADD SOME KIND OF DECISION LOG TO
YOUR PROJECT. It is the best possible guard against [Chesterton's Fence](https://en.wikipedia.org/wiki/G._K._Chesterton#Chesterton's_Fence)
problems which otherwise can be a recurring theme when working with LLMs. They also make it easier to only explain yourself once, since if
the LLM feels inclined to relitigate anything it will find itself directed towards the documented reason things are the way they are.

In Luria, decisions carry a state. Decisions can be Active, Proposed, Deferred, Rejected, or Superseded. Decisions often influence each other,
which manifests as references in documentation as well as in code. Luria's linter standardizes the form these references take, and also checks 
that all referenced decisions are in an "active" state. If the linter discovers (unacknowledged) references to non-active decisions, it can raise 
warnings, generate reports, and/or fail CI until the unendorsed decisions are dealt with (or the references to them are annotated for the linter). 


### The four layers

| layer | holds | test |
|---|---|---|
| design principles | standing **values**, numbered, citable and **versioned** | *have we re-derived this more than once?* |
| decisions | a **choice among alternatives** at a point in time | *did we reject an alternative, or set a constraint?* |
| changelog fragments | **what changed**, operator-facing | *would someone running this notice?* |
| devlog entries | **how it went**, including the wrong theories | *will a future debugger want the narrative?* |

Each contribution writes a *fragment* nobody else touches; the shared documents
are **views**. A file every contribution appends to is a lock, and its conflicts
carry no information ([DP-2](docs/design-principles.md#dp-2)).

The tree says which is which ([DP-9](docs/design-principles.md#dp-9),
[ADR-021](record/decisions.d/ADR-021.md)): **you read in `docs/`, you file in
`record/`**. Browsing lands on prose and generated views; the sources sit in
`record/`'s `.d`-suffixed containers, arrived at by link or on purpose. A view
directory holds only what the generator wrote — a hand edit there is a lint
failure, not a plea in a comment.

```
docs/                     READ  — doctrine + every generated view
record/decisions.d/       WRITE — one file per decision
record/principles.d/      WRITE — one file per principle
record/changelog.d/       WRITE — fragments, collected into /CHANGELOG.md
record/devlog.d/          WRITE — journal entries, yyyy/mm/dd/hhmmss.md
```

Views come in two kinds, and the difference is whether the sources survive
([ADR-012](record/decisions.d/ADR-012.md)). The changelog is **collected**: its
fragments are consumed, so the view can only be appended to. The decision index,
the principles document and the devlog are **generated** — a pure function of
sources that persist, which is the only reason `luria lint` can tell you one has
gone stale.

The devlog is a **journal**: entries are filed at their authoring timestamp
(`record/devlog.d/2026/08/03/211926.md`), never deleted, and rendered into one book per
month with a generated contents list ([ADR-020](record/decisions.d/ADR-020.md)). A
dated observation was true when it was written and stays true; consuming it
throws away the only copy of something that never expires.


## Motivation

Are you using any form of "agentic AI"? You are probably doing it wrong. Luria's position is that most of the standard 
practices of contemporary agentic programming are actually anti-patterns and should be treated as code smells rather 
than development strategies to aspire towards. This is obviously pretty big talk, so I'm going to back it up by pointing
my finger at the leader of the pack: Claude Code.

Don't get me wrong: I love CC and use it all the time. I've barely written any code by hand myself in months because CC
is just so damn good. But there are few ways in which I use CC which run directly counter to how the system is designed
and how Anthropic recommends it be used.

* I discourage CC from documenting memories privately (both in `.claude/` as well as `CLAUDE.md`)
* I rarely use MCPs/skills.

When Karpathy coined the phrase "Vibe Coding", he was talking specifically about the frame where you say "yes" to 
everything the LLM suggests. I feel like today, "Vibe Coding" has come to mean any LLM-assisted coding. When I use
CC, I am not "vibing" with the model. I am *collaborating* with it. I often need to interrupt it, reverse its decisions,
propose alternatives and solutions it hasn't considered, grab the wheel and perform outright course corrections... 
The Software Engineering world already has language that describes the situation where one developer writes most of the code
while another looks over their shoulder providing feedback and guidance: it's called **pair programming**.

Adopting the perspective that an LLM is just a non-human collaborator that we pair with, let's revisit practices like 
"storing memories" and building entire control planes (i.e. MCPs) just for LLMs.

* Imagine you had a coworker who every time they learned about a new edge case in the code, they document it in their own
  private notes instead of simply extending the project's normal documentation. This is exactly what "memories" and `CLAUDE.md`
  are. They are the LLMs private notes to itself. It's increasingly becoming the case where the most up-to-date documentation
  for a project aren't in the project's docs, they're in `.claude/`, where no one but the LLM will see them. That means no one
  else from the team can learn from them. It also means no one will put eyes on those notes to make sure they were actually
  correct. If your LLM documents an incorrect policy or procedure in a memory and doesn't immediately announce to you that they
  did so, do you have any process for even realizing that happened? Or will you just rely on the LLM doing the thing wrong
  enough times that you'll realize it documented the wrong way to do things in its notes to itself?
* Imagine you had a coworker who wrote a bunch of scripts and tools that they found useful for their own work. Convenience
  functions for chaining multiple steps that often go together, ways for listing frequently relevant information. You pair with
  this person, so if it's useful to them, it's probably useful to you to. Why should these things live in your coworker's private
  toolbox instead of just putting them somewhere they can benefit the whole team? 

Instead of "the agent's memory" being siloed for no reason, all knowledge relevant to a project can and should accumulate alongside it,
in a manner where all contributors to the project can benefit from it and validate its correctness.

Instead of "the agent's tools" being a whole separate toolkit, the agent can and should interact through the exact same control plane as
any other user. Why maintain an interface for people and a separate interface for machines? If your answer is "humans like a UI" then fine,
give them a UI: it can sit on top of a backend that your LLM accesses directly. If your answer is "I want to be able to control what
my LLM has access to": that's what access control is for. Create a user principal for your agents and manage the scope of their access
from that, like you would for any other collaborator.

These are solved problems. "Memory" is one of them: we just need to shift our thinking from "agent memory" to "institutional memory".
The tools for accumulating and curating institutional memory are **Change Management Processes**. Humans often consider processes to be
an imposition because they take up time. LLMs move through processes and procedures extremely quickly, so they are unhampered by
bureaucracy the way we are. The myriad processes in luria may seem like a big ask for a human collaborator. Well, yeah, they are. You (human)
don't need to engage with them directly if you don't want to. If the LLM engages with the processes, that's probably good enough for both of you.

LLMs aren't burdened by time constraints, they're burdened by being a perpetual newcomer with a limited 
context length. The LLM is a collaborator who must be onboarded every time you interact with them. Front-load discoverability of
relevant information in your project like you were expecting to onboard a bunch of inexperienced juniors who you don't want to bother you,
and you've automatically rigged your project to make that information easily discoverable for an LLM as well. Conversely, if you force
your LLM make the information it needs discoverable through the project's common documentation, you end up with strong onboarding material
for free.

Luria systematizes an opinionated collection of processes which implements a ratchet for accumulating empirical evidence and demonstrated solutions, shines a light on technical debt, and publishes lessons learned in a manner that facilitates their future influence on the project.


---

A project's memory: the decisions, the principles, the changelog and the
narrative log — kept where the next collaborator will find them, and kept honest
by a lint.

Half the collaborators on a modern codebase are stateless. They arrive with no
memory, read some pages, work, and vanish. Unwritten knowledge is re-derived at
cost, per session, forever. Luria is the machinery for a record that survives
that: [project memory](docs/project-memory.md) is the doctrine, and this package
is what stops it drifting.

```
pip install luria
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
identically ([ADR-016](record/decisions.d/ADR-016.md)).

A citation can land before its URL does. Luria cites both `SG` (the pilot it was
extracted from, whose filenames haven't been converted yet) and `LU` (itself,
which the `luria init` scaffold points at). Naming the document is the durable
half and works immediately; the URL improves when the remote does
([ADR-017](record/decisions.d/ADR-017.md)).

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
taste gets re-litigated ([ADR-009](record/decisions.d/ADR-009.md)).

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


## Citation

```latex
@software{marx2026luria,
  author    = {Marx, David},
  title     = {{Luria}: Project Memory as Change Management},
  year      = {2026},
  url       = {https://github.com/dmarx/luria},
  note      = {Open-source software}
}
```
