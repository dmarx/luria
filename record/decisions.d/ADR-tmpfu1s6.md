---
status: Active
title: 'A citation that needs no acknowledgement may be declared once, as a pattern'
version: 1
tags:
- config
- mechanism
date: '2026-10-21'
summary: >-
  `lint.inactive_ok` is the config-level form of the `inactive-ok`
  directive: a list of one-hop path patterns over the reserved `cites` edge,
  each with a mandatory reason. A citation of a retired document is
  sanctioned when the document it sits in matches the citing node and the
  cited document matches the other, by scheme and by literal equality on
  any frontmatter field. A citation from anywhere else is judged as before.
  An `inactive-ok` the rule made redundant, and a rule that sanctions
  nothing, are both reported stale. The pattern is read by the grammar
  `patterns.X` uses, and anything beyond one `cites` hop is refused by
  name. Rejected: `active` as a list, per-site annotations only, a global
  flag counting a status as in force, and a per-scheme `citable_from`
  keyed by status.
influenced_by:
- ADR-035
- ADR-085
- ADR-105
- DP-010
- DP-015
---

# ADR-tmpfu1s6: A citation that needs no acknowledgement may be declared once, as a pattern

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

**A record may state the acknowledgement once, in its lint settings.**

```yaml
lint:
  inactive_ok:
    - match: "(:QUESTION {status: 'Open'})-[:cites]->(:QUESTION {status: 'Answered'})"
      reason: a split parent cites the Answered child split off it
```

The entry is the config-level form of the `inactive-ok` directive, and is
named for it. A directive says why at one site; a rule says why once, for
every site it matches.

**The pattern is a path pattern, over one reserved edge.** `cites` means
"this document's text cites that one", the citation the lint already reads
out of a document. It is not a reference field, which is why a rule is not
a `patterns.X` entry. The arrow points from the citer to the cited, either
way round (`<-[:cites]-` reverses the roles). A node's label is a scheme,
and a property is literal equality on any frontmatter field (`status`,
`role`, `warrant`, …), exactly as in `patterns.X`.

**What it sanctions.** A citation of a document that is not in force is
sanctioned when the document the site sits in matches the citing node and
the cited document matches the other. A citation from another scheme,
another status, or a file that is no document of the record is judged as
before. `luria/ref_status.py` states `sanctioned(I)`, and
`luria/logic/acknowledgements.lp` reads a sanctioned site as not retired.
So the site wants no `inactive-ok`, and one written over it answers for
nothing. It is reported stale with the rule that took over ("cited here
where `lint.inactive_ok[0]` allows it"), which is how a record finds the
annotations to delete.

**A rule that sanctions nothing is reported** in the same
`stale-directives` class, with its pattern and reason. A dead rule
otherwise reads exactly like a working one ([DP-015](../principles.d/DP-015.md)).

`Citation.loud`, not acknowledged and not sanctioned, is the one test of
whether a site still wants attention. `flagged`, `luria ack` and the
pending report read it. The export's `excused` column still means "a
directive acknowledges it", as its schema says.

**One grammar, held to what a citation is.** The pattern is parsed by the
grammar every pattern uses (`luria/patterns.lark`), and its labels and
properties are checked by the checks `patterns.X` gets. The loader then
refuses, naming `lint.inactive_ok[N]`:

- anything but exactly one hop;
- a hop typed anything but `cites`, alone;
- a variable-length hop;
- `WHERE NOT`, which could be widened later if a record needs a condition;
- a label that is not a scheme, a property that scheme cannot hold, and an
  unlabelled node;
- a missing or empty `reason`, for the reason a directive's reason is
  mandatory;
- an entry that is not a mapping of `match` and `reason`.

## Alternatives considered

- **`active` as a list.** Counting `Answered` as in force silences the
  parent's citation, and also every citation that should warn: a theory
  still treating the question as open, a note that should cite the answer.
  Those are the warnings the scheme exists for.
- **Per-site annotations only.** This is the status quo, and it works. But
  each annotation restates a rule that holds for every parent and every
  answered child. The record pays for one rule thirteen times, and the
  fourteenth is a warning until someone writes the same sentence again.
- **A global flag that counts a status as in force for some purpose.** It
  has the same defect as the list: it cannot say who the citer is.
- **A per-scheme `citable_from`, keyed by status:** `Answered:
  [QUESTION:Open]` on the cited scheme. It was built first. It could only
  express status: status words are scheme-specific, so a rule over a
  claim's `role` or `warrant` had no spelling, and the `PREFIX:Status`
  string was a second, ad hoc notation for what a pattern node already
  says. The pattern needs no new syntax, reads like every other pattern in
  the config, and takes any field.

## Consequences

- A record states a citation rule once, in its config, and the redundant
  annotations surface as stale findings to delete.
- A rule applies only to record documents. A citation from code or from a
  page outside every scheme cannot match a node, so it is judged as before.
- A pattern with a property map must be quoted in YAML, which reads an
  unquoted `{` as a mapping. The configuration reference's example is
  quoted, and a test parses it.
- A sanctioned site is not counted in the "acknowledged" totals. It is not
  a suppression: the rule and its reason are written in `luria.yaml`.
- Fired on a copy of nucleation with the rule above: the thirteen parent
  annotations went stale, each naming `lint.inactive_ok[0]`, and no other
  finding changed. The tests are in `tests/test_inactive_ok_rules.py`.
