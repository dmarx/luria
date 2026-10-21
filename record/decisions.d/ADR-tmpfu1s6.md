---
status: Active
title: 'A retired status may name the citers that need not acknowledge it'
version: 1
tags:
- config
- mechanism
date: '2026-10-21'
summary: >-
  A scheme may declare `citable_from`, which maps a status of its own to the
  citers that may cite a document at that status with no acknowledgement:
  `Answered: [QUESTION:Open]`. A citer is a scheme and a status of it, and
  a citation from anywhere else is judged exactly as before. Such a site is
  `sanctioned`, so an `inactive-ok` over it answers for nothing and is
  reported stale, which is the migration signal. The loader refuses an
  entry that could exempt nothing. Rejected: `active` as a list, per-site
  annotations only, and a global flag that counts a status as in force.
influenced_by:
- ADR-035
- ADR-085
- ADR-105
- DP-010
---

# ADR-tmpfu1s6: A retired status may name the citers that need not acknowledge it

## Context

Whether a cited document is in force is one word per scheme, `active`. Every
citation of a document at any other status is a `retired-citations` warning
until an `inactive-ok` acknowledges it ([ADR-035](ADR-035.md)). For decisions that is
right: a `Superseded` ADR is cited deliberately or by mistake, and only the
author knows which.

A question record breaks the assumption that every citer is in the same
position. nucleation's `QUESTION` scheme has `active: Open` and the statuses
`Answered`, `Dissolved`, `Deferred` and `Superseded`. An open question that is
too broad is split, and the child gets answered first. The parent still
cites it, because the answered child is part of the parent's argument. That
citation is the record working. Every other citation of an answered
question is still worth a warning: it should cite the claim or theory that
answered it, or it still treats the question as open.

Before this decision the only remedy was an `inactive-ok` at each parent's
site. nucleation carried thirteen of them, one per answered question, each
saying the same thing.

## Decision

**The cited scheme names the citers its retired statuses are citable from.**

```yaml
schemes:
  QUESTION:
    active: Open
    citable_from:
      Answered: [QUESTION:Open]
```

Each entry maps a status word of this scheme to a list of `PREFIX:Status`
citers. A citation of an `Answered` question from a document of scheme
`QUESTION` whose status is `Open` needs no acknowledgement. A citation from
any other scheme, any other status, or a file that is no document of the
record is judged exactly as before.

**A sanctioned site is not retired.** `luria/ref_status.py` works out which
document each site sits in, and states `sanctioned(I)` when the cited
document's status and the citer's scheme and status are a declared triple.
`luria/logic/acknowledgements.lp` reads a retired site as one that is not
sanctioned. So a sanctioned site wants no `inactive-ok`, and one written
over it answers for nothing. It is reported stale, with the reason ("cited
here from where its scheme's `citable_from` allows"). That stale report is
how a record finds the annotations the key has made redundant.

`Citation.loud` is the one test of whether a site still wants attention:
not acknowledged and not sanctioned. `flagged`, `luria ack` and the pending
report read it. The export's `excused` column still means "a directive
acknowledges it", because that is what its schema says.

**A declaration that could exempt nothing is refused when the config
loads**, as `retires_on` is: a status the scheme's vocabulary lacks, the
scheme's own `active` word (a document in force needs no exemption), a
citer scheme that is not declared, and a citer status that scheme's
vocabulary lacks. A malformed shape is refused too, naming the key.

## Alternatives considered

- **`active` as a list.** Counting `Answered` as in force silences the
  parent's citation, and also every citation that should warn: a theory
  still treating the question as open, a note that should cite the answer.
  Those are the warnings the scheme exists for. This was the first idea
  and the reason a narrower key is needed.
- **Per-site annotations only.** This is the status quo, and it works. But
  each annotation restates a rule that holds for every parent and every
  answered child, so the record pays for one rule thirteen times, and the
  fourteenth is a warning until someone writes the same sentence again.
  A rule stated once belongs in the config.
- **A global flag that counts a status as in force for some purpose.** It
  has the same defect as the list: it cannot say who the citer is. Naming
  the citer by scheme and status is what keeps the other warnings.
- **Declaring the exemption on the citing scheme.** The cited scheme is
  the one whose status vocabulary gives the words their meaning, and it is
  where a reader looks to find out what `Answered` permits.

## Consequences

- A record states a citation rule once, in its config, and the redundant
  annotations surface as stale findings to delete.
- The exemption applies only to record documents. A citation from code or
  from a page outside every scheme cannot match a citer, so it is judged as
  before. A rule for those would need another shape.
- A sanctioned site is not counted in the "acknowledged" totals. It is not
  a suppression: the rule is written in `luria.yaml` and the configuration
  reference lists the key.
- Fired on a copy of nucleation with the key above: the thirteen parent
  annotations were reported stale, each naming the answered question, and
  no other finding changed. The tests are in `tests/test_citable_from.py`.
