---
status: Active
title: 'An exported citation states its standing and what clears it'
version: 1
tags:
- mechanism
date: '2026-10-21'
summary: >-
  The export's `citations` table gains `standing`, which is one of
  `in-force`, `acknowledged`, `sanctioned`, `unacknowledged` or `dangling`,
  and `excused_by`, which names the directive (`inactive-ok @ path:line`) or
  the rule (`lint.inactive_ok[N]`) that clears a site. `excused` widens to 1
  when a directive or a rule clears the site. The standing is
  `Citation.standing` in `ref_status`, the reading the lint makes, so the
  export does not derive it a second time. Rejected: keeping `excused` as
  it was and adding only `standing`, and dropping `excused`.
influenced_by:
- ADR-116
- ADR-105
- ADR-tmpfu1s6
- DP-004
---

# ADR-tmptj3j3: An exported citation states its standing and what clears it

## Context

`luria export` writes every citation the lint's scanner counts. Each row
carried `resolves` and `excused`, "1 when a directive acknowledges it"
([ADR-116](ADR-116.md)). Five different situations ended up in those two columns:

- the cited document is in force;
- a directive acknowledges the site;
- a `lint.inactive_ok` rule sanctions it ([ADR-tmpfu1s6](ADR-tmpfu1s6.md));
- the cited document is retired and nothing answers for it, which is the
  case the lint warns about;
- the code names no document here.

An in-force site and an unacknowledged one both exported `excused = 0`.
To tell them apart, a query had to join `documents` and know the scheme's
`active` word. That reconstructs the lint's reading by hand, and it went
wrong once a rule could clear a site without any directive in the text. A
sanctioned site exported `excused = 0` and looked like a warning.

## Decision

**Each citation row states its standing**, as one of these words:

| standing | the site |
|---|---|
| `in-force` | cites a document in force, and needs nothing |
| `acknowledged` | is a finding that a directive answers for |
| `sanctioned` | cites a retired document where a `lint.inactive_ok` rule allows it |
| `unacknowledged` | cites a retired document and nothing answers for it, so the lint warns |
| `dangling` | names no document and nothing answers for it, so the lint warns |

A dangling site under `unresolved-ok` is `acknowledged`, because the
directive answers its finding.

**A `mention-ok` site stands where its target puts it.** The directive
claims nothing about state ([ADR-105](ADR-105.md)). Over a document in force it is
`in-force`: the mention only keeps itself alive. Over a retired or dangling
target it is `acknowledged`, because the mention answered the finding the
site would otherwise be. In both cases `excused_by` names the mention.

**`excused_by` names what clears the site.** For a directive this is its
kind and where it sits, as the stale-directive report already prints it:
`inactive-ok @ docs/x.md:12`, or `inactive-ok-file @ …` for a file-scoped
directive. For a rule it is the rule's key, `lint.inactive_ok[0]`. It is
NULL when nothing clears the site. A rule takes precedence over a
directive. The only directive that can sit over a sanctioned site is a
`mention-ok`, and it claims nothing.

**`excused` is 1 when a directive or a rule clears the site.** This changes
the column's meaning: before, a sanctioned site exported 0.

**There is one reading.** `Citation.standing` and `Citation.cleared_by` in
`luria/ref_status.py` derive both values from the scan the lint reads, and
the export only copies them out ([DP-004](../principles.d/DP-004.md)). The words are constants
(`ref_status.STANDINGS`), so a report that wants them reads the same
values.

## Alternatives considered

- **Keep `excused` as it was and add only `standing`.** Nothing breaks, but
  `excused` would mean "a directive, not a rule". A query that already
  filters on `excused = 0` to find what needs attention would keep finding
  every sanctioned site. A rule is an acknowledgement written once, and
  the column should count it.
- **Drop `excused`.** `standing IN ('acknowledged', 'sanctioned')` says the
  same thing, but removing a column breaks every saved query to tidy a
  redundancy. The flag costs one integer per row.
- **Derive the standing in `export.py`.** That would be a second
  implementation of the lint's reading of a site. It is the drift [DP-004](../principles.d/DP-004.md)
  names, and it is what produced the wrong `excused = 0`.

## Consequences

- A query asks `WHERE standing = 'unacknowledged'` for what the lint warns
  about, with no join.
- A saved query reading `excused = 0` as "not acknowledged" now also
  excludes sanctioned sites, which is what it meant.
- `tests/test_export.py` pins each of the five standings, `excused_by` for
  a directive and for a rule, and the `mention-ok` cases.
  `tests/test_ref_status.py` pins `Citation.standing` directly.
