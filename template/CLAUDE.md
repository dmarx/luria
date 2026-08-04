# CLAUDE.md

<!-- This file is a BOOTLOADER, not a knowledge store: pointers to the shared
     record, plus harness mechanics no human needs. Anything a new human hire
     would also need belongs in docs/, and this file links to it. A private
     memory is a doc that skipped review. -->

## Project memory — read this before writing anything down

This project keeps its memory in four layers. Which one you want:

| layer | holds | test |
|---|---|---|
| [`record/principles.d/`](docs/design-principles.md) | standing **values**, numbered, cited as "DP-2" | *have we re-derived this more than once?* |
| [`record/decisions.d/`](docs/decisions/README.md) | a **choice among alternatives** at a point in time | *did I reject an alternative or set a constraint?* |
| `record/changelog.d/` | **what changed**, operator-facing, terse | *would someone running this notice?* |
| `record/devlog.d/` | **how it went**, including the wrong theories | *will a future debugger want the narrative?* |

**You read in `docs/`, you file in `record/`.** That is the whole layout rule
([LU-ADR-021](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-021.md)): everything a reader browses — the doctrine and every generated
view — lives under `docs/`; everything a contributor files lives under
`record/`, each container wearing the `.d` suffix that says *fragments live
here*. Nothing under a view directory is hand-written, and the lint fails
anything that is. If you are editing a file whose directory doesn't end in
`.d` and isn't prose you were asked to change, stop — you are probably editing
a view.

The two fragment kinds differ in whether the source survives, and it decides how
you file one ([LU-ADR-012](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-012.md)):

- **Collected** — `record/changelog.d/<branch-slug>.md`. Assembled into
  `CHANGELOG.md` and the fragment is *consumed*. One file per contribution.
- **A journal** — `record/devlog.d/`, filed with `luria journal new "What you
  did"`, which puts it at `yyyy/mm/dd/hhmmss.md`. Entries **persist**: a dated
  observation was true when you wrote it and stays true, so `docs/devlog/` is
  regenerated from them and each month's book carries a contents list built from
  the titles. Don't name journal files yourself — the path is the timestamp, and
  the lint checks it against `created:`.

**File it in the same contribution as the work.** A fact filed while its context
is loaded costs a paragraph; re-derived cold, it costs a session.

**Record the failed approaches.** The dead ends are what the next debugger needs
most, and they are the part that never appears in a commit message.

## Commands

```
luria lint            # the only one that can fail
luria link --fix      # rewrite bare references as hyperlinks
luria index           # regenerate every generated view (+ the README's counts)
luria journal new "…" # file a dated devlog entry at its timestamp
luria ref-status      # what still cites a retired decision
luria pending         # what has been undecided, and for how long
luria remotes         # other projects' records, and how they resolve
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
number, or an example.

**Another project's decision is not that case — give it a prefix.**
`LU-ADR-013` is remote `LU`'s decision 13 — the scaffold registers `LU` for
Luria itself, and yours go beside it. One `[luria.remotes.X]` entry in
`luria.toml` makes a code a first-class reference: the fixer writes the link, the
lint demands it, and `luria remotes` shows how each one resolves. A remote whose
filenames carry title slugs needs `luria remotes --refresh` once, to discover
them into the committed lockfile; one that names files after their codes needs
nothing.

## Adding a decision

Copy [`record/decisions.d/_template.md`](record/decisions.d/_template.md) to
`ADR-<NNN>.md` with the next free number — the filename is the code and nothing
else, and the title goes in `title:`. Repeat the title as the body's
`# ADR-NNN:` heading; the lint checks that the two agree. Then run
`luria index`. Write the `summary:` — it is what the index shows, and the
index is read far more often than the decision. Say what was decided **and what
was rejected**; a decision with an empty "alternatives considered" usually
wasn't a decision.

When the **choice** changes, supersede: add a decision and flip the old one's
status to `Superseded`, leaving its body intact.

When the choice stands and only a **reason** was wrong, correct the body in
place, bump `version:`, and say in `history:` what the previous version claimed
and why it was wrong. Superseding there is theatre — it retires a decision still
in force and points every citation at an identical claim.

**Nothing in the record is frozen.** The rule objects to *silent* revision, and
a version bump with a history note is the opposite of silent. The test for the
ambiguous case: *would a reader who acted on the old version have done something
different?* If yes, supersede; if they'd have done the same thing for a worse
reason, correct in place. Luria's own record carries a worked example of each:
[LU-ADR-019](https://github.com/dmarx/luria/blob/main/record/decisions.d/ADR-019.md).

## Adding or revising a principle

Same shape, one directory over: copy
[`record/principles.d/_template.md`](record/principles.d/_template.md) to
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
