---
status: Active
title: '`inert-status` measures a distribution, and its threshold is the project''s to set'
version: 1
tags:
- mechanism
date: '2026-09-05'
issue: '#167'
summary: >-
  The check fired only when every record shared one status, on the argument
  that one retirement proves the judgement is live. A 144-document registry
  disproved it: eleven exceptions silenced the check while a quarter of its
  entries went unexamined. `uniform_share` makes the threshold configurable
  and defaults to 1.0, so nothing starts reporting. Rejected: lowering the
  default, and inferring the threshold from scheme size.
---

# ADR-tmpmc2vu: `inert-status` measures a distribution, and its threshold is the project's to set

## Context

`inert-status` ([#104](https://github.com/dmarx/luria/issues/104)) fires when a scheme's every record shares one status.
The reasoning was recorded in a test docstring and is good:

> The distinction is live as soon as anything varies. This is not a rule
> about proportion — a corpus whose claims all survive is legitimate — so a
> single retirement is enough to say a judgment is being made.

`anthology-of-the-sota` is the case that argues with it. Its practice
registry sits at 133 `Active`, 8 `Proposed`, 2 `Superseded`, 1 `Deferred` —
92% uniform, eleven exceptions, and the check permanently silent.

During those two years, a quarter of that registry was discovered to be
sourced to papers that do not exist. All 39 of those practices sat at
`Active` throughout. The status field reported nothing about them, and could
not have, because eleven other documents were not `Active`.

So the premise "one retirement proves the judgement is live" is doing more
work than it can bear. What one retirement proves is that the *vocabulary* is
reachable. It says nothing about whether the other 133 were ever examined,
and at that ratio a reader can predict a status without opening the document
— which is the definition of a field that has stopped carrying information,
and the thing this check exists to name.

## Decision

`uniform()` reports on the **modal** status's share rather than on unanimity,
and the threshold is a per-scheme setting:

    [luria.schemes.SOTA]
    uniform_share = 0.9

**The default is 1.0, which is exactly the previous rule.** A project that
never sets it sees the behaviour it saw before, byte for byte. Lowering it is
opt-in.

Two supporting changes:

- The row shows the distribution it is reporting against — `SOTA: 133/144 at
  Active — 8 Proposed, 2 Superseded, 1 Deferred` — because a finding about a
  proportion that prints only a proportion invites the reply that exceptions
  exist. Naming them answers it in the row.
- `uniform_ok` uses the same rule, so an acknowledgement covers exactly what
  the finding would have reported. The two drifting apart would mean a scheme
  could be acknowledged for unanimity and reported for near-unanimity.

## Alternatives considered

**Lower the default to ~0.9.** The change that would actually help the
projects that need it, and rejected because it would start reporting on every
existing luria record at once, most of them correctly uniform and none of
them consulted. A check that arrives loud and unbidden is a check people
switch off, and this one has no per-site acknowledgement to soften it — only
a config line, which is precisely the friction a surprised user will not pay.
Defaults that change behaviour under people are how guards lose their
credibility.

**Derive the threshold from scheme size.** Tempting, since the argument
against unanimity is really an argument about large schemes: twelve records
all in force is a young project, four hundred is a claim about the world. A
size-scaled threshold would need no configuration. Rejected because the curve
would be invented — there is no principled shape for it, and every project
that disagreed with the curve would have no way to say so. `FLOOR` already
handles the youth case with a number that is defensible because it is crude.

**A separate class for near-uniformity.** Keeps the existing finding exactly
as it is and adds `near-inert-status` beside it. Rejected as two names for
one question; the report would carry both rows for a scheme that crossed from
one to the other, and `uniform_ok` would have to acknowledge each separately.

**Measure transitions instead of the snapshot.** The sharper question is
whether the vocabulary is ever *exercised* — a registry where nothing has
been demoted in two years is making a claim about the world regardless of its
current distribution. That needs git history rather than frontmatter, so it
is a report rather than a lint check, and it is left for [#167](https://github.com/dmarx/luria/issues/167) to take up
separately.

## Consequences

No existing project's output changes. The dial exists for the projects whose
schemes have outgrown the unanimity test, and setting it is a statement about
what that scheme is for — which is the same bargain `uniform_ok` already
strikes, one level down.
