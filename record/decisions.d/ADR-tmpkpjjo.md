---
status: Proposed
title: A scheme whose status never varies is reported
version: 1
tags:
- record
- mechanism
date: '2026-08-16'
issue: '#104'
summary: >-
  `active` is what `retired-citations` reads, so a scheme where nothing is
  ever retired has an enforcement mechanism that cannot fire — and its build
  is green because nothing is being judged rather than because nothing is
  wrong. Downstream that state cost thirteen green builds over a scheme with
  fifty-one records at one status, twenty-three of which its own bodies
  refuted. Reported, not failed: there is no correct proportion. Exempt below
  ten records, for a document-rendered scheme, and for a project that has
  declared exactly one status on purpose.
---

# ADR-tmpkpjjo: A scheme whose status never varies is reported

## Context

A status field where every record agrees is indistinguishable from no status
field. That would be a cosmetic observation if nothing read it — but `active`
decides what counts as retired, and `retired-citations` fires off that. So a
scheme in this state has an enforcement mechanism that **cannot fire**, and
there is currently no signal at all: the build is green *because* nothing is
being judged.

The downstream case is precise. `dmarx/mathematics-of-meaning` names
`retired-citations` in its `fail_on`, which is the reason it adopted luria: it
records the claims of a corpus of arguments, and wants an argument resting on
an abandoned premise to fail the build. Extraction files a claim at `Active`
and nothing contradicted it, so **fifty-one of fifty-one claims sat at
`Active`** — including twenty-three whose own bodies exhibited a counterexample
and two that said "It is false as stated" in as many words. Thirteen documents,
thirteen green builds, and the mechanism had never once run.

The same project's argument scheme was 23 of 24 at one status for a different
reason, and its concept scheme is 13 of 13 today.

All three were found by a person re-reading, which
[ADR-003](ADR-003.md)'s audit is the standing argument against.

## Decision

A status report class, `inert-status`: one line per scheme whose records all
share a status.

```
luria: 2 scheme(s) file every record at one status, so nothing there can ever
       be retired and the citation checks cannot fire
  ADR: 12/12 at `Active`
  CON: 13/13 at `Active`
```

**A report, not an error** ([ADR-035](ADR-035.md)). There is no correct
proportion of retired records, and a corpus whose claims all survive is a
legitimate outcome. The finding is narrower and is a fact: *nothing here has
ever been judged*. A human reads that and may reasonably dismiss it — the ADR
row above is a young decision record with nothing superseded yet, and clears in
two seconds. Nameable in `fail_on` for a project that wants it enforced once
clean.

Three exemptions, each for a different reason:

- **Below ten records.** Uniformity in a young scheme is evidence of nothing.
- **A `render = "document"` scheme.** A design-principles page where every
  principle is in force is the expected state; principles move by `version:`,
  not by status.
- **A scheme declaring exactly one status** ([ADR-056](ADR-056.md)).
  A project that has said "this scheme uses one status" has answered the
  question, and reporting it would be telling it off for configuring correctly.

The comparison drops a trailing ` — note`, so `Superseded — by X` and
`Superseded — by Y` count as one status rather than as variety.

## Alternatives considered

- **Fail rather than report.** There is no threshold to fail against. Failing
  on uniformity would break every project on the day it adopts a new scheme,
  and the remedy — retire something — is exactly the judgment a tool must not
  make.
- **Check the proportion instead** (warn below some retirement rate). Invents
  a number nothing supports, and would nag a project whose claims genuinely all
  survive. Uniformity is the one state that is *always* uninformative,
  whatever the subject matter.
- **Leave it to projects.** The downstream project did write this check, as a
  test, after being bitten — which is the usual signal that a check belongs in
  the tool rather than in each project that eventually needs it.
- **Status quo.** The failure is silent by construction and stays that way. It
  cost thirteen builds' worth of unfired enforcement in the one project we can
  measure.

## Consequences

The first run on this repo reports nothing: `ADR` has variety and `DP` is
document-rendered. The first run on the downstream project reports two schemes,
one of which (`CON`) its own decision record had already flagged in prose as
"either correct or the next instance of this" — so the check's first act is to
turn a written suspicion into a standing finding.

A project adopting a new scheme will see it appear once the scheme passes ten
records and before anything is retired. That window is real and the report is
correct during it: nothing *has* been judged yet.
