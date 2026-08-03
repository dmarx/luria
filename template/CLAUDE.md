# CLAUDE.md

<!-- This file is a BOOTLOADER, not a knowledge store: pointers to the shared
     record, plus harness mechanics no human needs. Anything a new human hire
     would also need belongs in docs/, and this file links to it. A private
     memory is a doc that skipped review. -->

## Project memory — read this before writing anything down

This project keeps its memory in four layers. Which one you want:

| layer | holds | test |
|---|---|---|
| [`docs/principles/`](docs/design-principles.md) | standing **values**, numbered, cited as "DP-2" | *have we re-derived this more than once?* |
| [`docs/decisions/`](docs/decisions/README.md) | a **choice among alternatives** at a point in time | *did I reject an alternative or set a constraint?* |
| `changelog.d/` | **what changed**, operator-facing, terse | *would someone running this notice?* |
| `devlog.d/` | **how it went**, including the wrong theories | *will a future debugger want the narrative?* |

**Write a fragment, never edit the assembled file.** `CHANGELOG.md`, the devlog,
the decision index and `docs/design-principles.md` are all *views*, generated or
collected from fragments. One file per contribution, named after your branch.
The lint fails on hand edits to generated files.

**File it in the same contribution as the work.** A fact filed while its context
is loaded costs a paragraph; re-derived cold, it costs a session.

**Record the failed approaches.** The dead ends are what the next debugger needs
most, and they are the part that never appears in a commit message.

## Commands

```
luria lint            # the only one that can fail
luria link --fix      # rewrite bare references as hyperlinks
luria index           # regenerate every generated view (decisions, principles)
luria ref-status      # what still cites a retired decision
luria pending         # what has been undecided, and for how long
```

**Every reference is a hyperlink.** A decision code, a design principle or an
issue number written in prose is a link, never bare text — `luria lint` fails
otherwise. Don't hand-write them: `luria link --fix` writes exactly what the
lint demands.

**When a reference is deliberately odd, say so** rather than leaving it on the
report. The suffix decides the scope, uniformly, and a directive is one line:

```
<!-- inactive-ok: ADR-012 — the decision this replaced -->     line + the line below
<!-- inactive-ok-block: ADR-012 — this whole paragraph -->     the block it sits in
<!-- inactive-ok-file: ADR-012 — this page is that history --> the whole document
<!-- unresolved-ok: ADR-777 — a fixture code, not a real one --> names nothing on purpose
```

`unresolved-ok` is for a code that resolves to **no document here**: a fixture
number, or an example. Another project's decision is not that case — write it
as a link out, which needs no annotation.

## Adding a decision

Copy [`docs/decisions/_template.md`](docs/decisions/_template.md) to
`ADR-<NNN>.md` with the next free number — the filename is the code and nothing
else, and the title goes in `title:`. Repeat the title as the body's
`# ADR-NNN:` heading; the lint checks that the two agree. Then run
`luria index`. Write the `summary:` — it is what the index shows, and the
index is read far more often than the decision. Say what was decided **and what
was rejected**; a decision with an empty "alternatives considered" usually
wasn't a decision.

Supersede by **adding** a decision and flipping the old one's status to
`Superseded`. Never rewrite a decision's body — the history is the point.

## Adding or revising a principle

Same shape, one directory over: copy
[`docs/principles/_template.md`](docs/principles/_template.md) to
`DP-<NNN>.md` with the next free number, run `luria index`. Add one only on the
**second** re-derivation of the same reasoning — one instance is a decision, a pattern is a principle.

Principles are **living documents**, and a revision is the opposite of a
supersession: when new experience shows an existing principle nearly covers it,
widen that principle's wording, bump `version`, and add a `history:` entry
saying what changed — don't write a neighbour it will be confused with. A value
stated about one artifact is a value nobody applies to the next one, and that is
the failure this field exists to make visible.

Fill in `influenced_by:` with the decisions whose experience produced it. That
is the evidence; without it a principle reads as taste, and taste gets
re-litigated by the next person with different taste.
