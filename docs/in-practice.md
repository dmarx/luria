# In practice: three records compared

[Adopting](adopting.md) is how to start. [Schemes](schemes.md) is how to design
a record family. This page is the question those two leave open: **given a
project, what should its record actually look like?**

Three of them exist and they disagree about nearly everything except the engine.
That disagreement is the guidance — luria is a shape, not a template.

## The three

| | **luria** | **strata-g** | **mathematics-of-meaning** |
|---|---|---|---|
| The record is about | the tool itself | a running application | *someone else's* corpus of arguments |
| Schemes | ADR, DP | ADR, DP | ADR, DP, CLM, ARG, CON, POS |
| Records | 58 ADR, 12 DP | 212 ADR, 21 DP | 51 CLM, 24 ARG, 13 CON, 12 ADR |
| Layout | `record/` + `docs/` split | collocated — `docs/decisions` is both | split |
| Scanned for citations | itself | `app.py`, `scripts/`, `tests/`, `web/src/`, workflows | prose corpora |
| Journal | daily | monthly | daily |
| `fail_on` | none — reports only | none — reports only | `retired-citations`, `unresolved-codes` |
| `stale_days` | default (90) | default | 14 |
| `allocate` | filing | filing | `merge`, on three schemes |
| `tag_groups` | — | — | ARG strength / failure |
| `statuses.yaml` | — | — | CLM, ARG, CON |
| `requires` | — | — | CLM: `source`, `locus` |

Everything below is one of those rows, explained.

## What the record is about drives everything else

This is the choice that determines the rest, and it is worth naming explicitly
before touching a config.

**A tool documenting itself** (luria) has a small, dense record where nearly
every decision is cited by code that implements it. Citations point inward.

**A running application** (strata-g) has a large record — 212 decisions over
months — where the citations live in *source*: a decision number in a comment
is the strongest form of the claim being checked, because it is the stated
reason the code is shaped that way.

**A corpus you are reading** (mathematics-of-meaning) inverts the usual
relationship. The record is not about the project; it is about material the
project did not write. That is why it needs schemes nothing else needs, and why
it is the only one of the three that enforces anything.

## Layout: collocated or split

The `record/` + `docs/` split is the default and the better shape: a writer
edits sources, a reader browses views, and a stale view fails the lint.

strata-g does not use it. Its decisions live in `docs/decisions`, which is both
the source directory and the rendered view:

```toml
[luria.schemes.ADR]
dir = "docs/decisions"
output = ""          # unsets the split-view default
```

Not an oversight — it had 200 decisions there before luria existed, and moving
them would have rewritten every inbound link in the repository and in every
issue thread that ever cited one, to buy a tidier tree.

**Rule: use the split if you are starting; keep what you have if you are not.**
Luria supports both natively, and a layout migration is a cost with no finding
at the end of it.

## Point the globs where the reason is stated

`[luria.code] globs` decides where a retired decision does damage. The
instinct is to point it at documentation. Usually that is wrong.

strata-g points it at code, tests and CI workflows, because that is where its
decisions are *invoked*:

```python
# Retries are the worker's own business, not the queue's (ADR-019).
```

Retire [ADR-019](../record/decisions.d/ADR-019.md) and that comment becomes a finding — the code is now shaped by a
reason nobody holds. A documentation-only glob would never have seen it.

**Rule: scan wherever someone would write "because of X".** For an application
that is source. For a corpus project it is the corpus. For a library it may
genuinely be the docs.

`historical` is the escape hatch on the same setting: a changelog citing a
since-retired decision is not a defect, it is a record of what was true then.
All three declare their changelog historical; strata-g also declares its frozen
pre-migration devlog archive.

## Two schemes is the common case

Both software projects run exactly two: decisions and principles. That is
probably right for most repositories, and a third scheme should have to justify
itself.

Six is right for mathematics-of-meaning because its material genuinely has
kinds that retire independently: a *claim* can be refuted while the *argument*
that used it survives on other grounds, and a *concept* can be refined while
both stand. Those are three retirement lifecycles, so they are three schemes.

**Rule from [schemes](schemes.md), restated because it is the whole test:**
write the finding sentence you would want to see. If *"CLM-018 is Rejected,
cited 4× in 3 files"* would be useful, the scheme is real. If you cannot imagine
retiring one on its own, you want tags.

## Enforcement is the last dial, not the first

Only one of three sets `fail_on`, and it is the one whose entire purpose is
enforcement — mathematics-of-meaning adopted luria *because* it wanted an
argument resting on a refuted premise to fail the build.

The two software projects report and do not fail. That is not laziness. A
report you read every week does most of the work, and promoting a class before
its findings are clean means either a permanently red build or a rash of
acknowledgements written to make it green — which is the one way an
acknowledgement must never be used.

**Rule: promote a class the day it reads clean, and only the class you came
for.** There is no prize for enforcing all of them.

## Match the cadences to how fast work arrives

Two settings are about *rate*, and both are commonly left at a default that
does not fit.

`stale_days` decides when an undecided document is called overdue.
mathematics-of-meaning runs at 14 rather than the default 90, because an agent
produces a fortnight of backlog in an afternoon and a 90-day window would never
flag anything. A human-paced project is right to leave it alone.

Journal `granularity` decides how entries collect into books. strata-g uses
`month` and produces a few entries a week; the other two use `day` and can
produce several in an hour. Pick so a book is a readable sitting.

**Rule: set these from your observed rate, not from what looks tidy.**

## `allocate = "merge"` only when collisions happen

Two projects take the next free number. mathematics-of-meaning mints temporary
codes on its three extraction schemes, because parallel extraction produces
genuine collisions.

The cost is real — temporary codes are ugly in review, and sequential numbering
carries information, since it is the order things were decided.

**Rule: default to `filing`. Switch when two branches actually collide, not in
anticipation.**

## What only shows up at scale

Some things do not appear until a record is large, and all three sizes are
represented here.

**At ~10 records**, nothing has been retired yet and that is fine. Do not read
a uniform status field as a problem this early — the `inert-status` report has a
floor of ten for exactly this reason.

**At ~50**, the first retirement lands and the propagation earns its keep.
mathematics-of-meaning's first wave produced 27 findings from 23 retirements,
and roughly two thirds of the findings across all its records were legitimate
citations needing acknowledgement rather than repair. Budget for that.

**At ~200** (strata-g), the record is a corpus of its own. All five statuses
are in use — 196 active, 6 proposed, 5 superseded, 3 deferred, 2 rejected — and
the interesting failure changes: it is no longer "nothing is retired" but
"nobody can find the relevant decision". Tag vocabularies stop being decoration
at this size.

Meanwhile its 21 design principles are *all* `Active`, and correctly so —
principles are revised in place rather than retired, which is why the
`inert-status` report exempts a `render = "document"` scheme. A rule that would
have fired on a real record is how that exemption got its shape.

## Things all three do the same way

Short list, and worth treating as settled:

- **The changelog is fragments**, collected on a cadence. Nobody edits a shared
  file per contribution.
- **The devlog is a journal**, not a scheme. Dated, historical, never
  superseded, and it is where the failed approaches go.
- **Principles render as one document**; decisions render as an index. You read
  principles front to back and arrive at a decision by link.
- **Cross-repo citation uses a registered remote prefix.** strata-g cites
  `LU-ADR-013`; luria cites `SG-DP-18` back. A prefix makes the namespace
  explicit at the point of use rather than guessed — an unprefixed `ADR-032` is
  a claim about *this* project's thirty-second decision.

## The shortest version

Copy the two-scheme shape and change three things: point `globs` where your
reasons are stated, write `statuses.yaml` on day one, and leave `fail_on` empty
until a class reads clean.

Everything else in the table above is a response to something specific about
that project. If you cannot say what in yours would drive a setting, the
default is the answer.
