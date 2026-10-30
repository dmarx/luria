---
status: 'Proposed'
title: 'A pattern node may test its own field for inequality or membership'
version: 1
tags:
- record
- mechanism
date: '2026-10-30'
summary: >-
  The path-pattern subset of ADR-129 gains one comparison per node, written
  inside the node in Cypher's inline node predicate:
  `(p:CLAIM WHERE p.status <> 'Active')`, `(o:CLAIM WHERE o.status IN
  ['Proposed', 'Active'])` and `(n WHERE NOT n.status IN [...])`. The
  comparison tests the node's own field, so it stays local to the node and
  readable in the line. It lowers to the `status/2` and `value/4` literals
  the property map already uses, plus negation over facts, so every program
  stays stratified. A document without the field matches no comparison, as
  with Cypher's null. Rejected: a list-valued property map
  (`{status: ['Proposed', 'Open']}`), a path-level `WHERE` clause with
  `AND`/`OR`, `=` as a second spelling of the map, nested `WHERE NOT`, and
  keeping the subset and a script beside it.
influenced_by:
- ADR-129
- ADR-125
- ADR-131
---

# ADR-tmpofn2g: A pattern node may test its own field for inequality or membership

## Context

ADR-129 limited a pattern's node test to literal equality, through a
property map (`{status: 'Active'}`). It added nothing beyond that because
nothing needed more at the time. It did not reject predicates on the
merits. What it set was a bar inherited from ADR-125: a reader sees the
rule in the line. ADR-125 rejected a *general* predicate language (`and`,
`or`, `not`, comparisons) for conditions. That same decision accepted a
condition that is "one field, a set of literal values", which is membership.

ADR-131 made a pattern with `report: true` a lint warning class. That is
what turned the subset into a limit. dmarx/nucleation keeps
`record/status-review/worklist.py`, a Python script beside its record. The
script holds checks that a reported pattern would carry if it could say
"not equal" or "one of":

- **Ready for a ruling.** A Proposed CLAIM where no premise reached by
  `rests_on`, `grounds` or `uses` is non-Active, and no live objection
  stands against it. A live objection is Proposed or Active.
- **Grounded on an unread work.** A live CLAIM `grounds` a LIT, and no NOTE
  whose status is Read or Skimmed names that LIT in `paper`.

`WHERE NOT (g {status: 'Rejected'})` already says "not equal" about a node
of the match. It cannot say it about a node *inside* a `WHERE NOT`, which
is where both checks need it ("no premise that is non-Active"), because
`WHERE NOT` does not nest. "One of" has no spelling at all short of a
pattern per value.

## Decision

**A node may carry one comparison of its own field, written inside the
node after its label and map:**

```
(p:CLAIM WHERE p.status <> 'Active')
(o:CLAIM WHERE o.status IN ['Proposed', 'Active'])
(n:NOTE WHERE NOT n.status IN ['Read', 'Skimmed'])
(c:CLAIM {role: 'thesis'} WHERE c.status <> 'Rejected')
```

This is Cypher's own syntax: the inline node predicate (`(n:Label WHERE
...)`, Neo4j 5 and GQL), with Cypher's `<>`, `IN` and `NOT ... IN`. A
pattern written here is still a Cypher pattern.

### What it means

- **`<>`** holds when the document has the field and no value of it is the
  literal.
- **`IN [...]`** holds when some value of the field is listed.
- **`NOT ... IN [...]`** holds when the document has the field and none of
  its values is listed.
- **A document without the field matches no comparison.** This follows
  Cypher's null, which compares neither equal nor unequal. A pattern that
  wants "no status at all" is out of scope, as before.
- **A list field reads as membership.** That is how the property map
  already reads one (`value(V, F, _, X)`), so `IN` is "any listed" and
  `<>` is exactly the negation of the map's equality.

### What stays out

Each of these is refused at load, by name:

- a comparison naming another node (`(a:LIT WHERE b.status <> 'x')`). A
  condition across two nodes is a hop.
- a comparison on an anonymous node. The node must be named to be tested.
- `AND`, `OR` and `XOR`. The map is the conjunction, and a disjunction is
  two patterns.
- `=`. Equality is the property map. One meaning gets one spelling.
- any other operator: `<`, `>`, `STARTS WITH`, `IS NULL` and so on.
- a path-level `WHERE` that is not `WHERE NOT (pattern)`. The refusal points
  at the inline form.

### How it lowers

The comparison reads the facts the map reads: `status/2` for `status`, and
`value/4` for any other field. `value/4` is built only when some pattern
reads a field other than `status`, as before.

- `IN` is a clingo pool of the literals.
- `<>` and `NOT ... IN` are the field present
  (`status(V, _)` / `value(V, F, _, _)`) and a negated literal per value.

Negation is over facts only, never over a derived predicate. So the
lowering adds no recursion through negation, and every program stays
stratified with one answer set (ADR-127). A comparison inside a `WHERE NOT`
lands in that negation's helper rule, like the map does.

The consistency check that a map's key is a field the node's scheme can
hold covers the comparison's field too.

## Alternatives considered

- **A list-valued property map, `{status: ['Proposed', 'Open']}`.** It is
  the shortest way to write "one of". But in Cypher that map means equality
  with a list. A record author who knows Cypher would read it wrongly, and
  it has no matching spelling for "not". The inline predicate costs a few
  more characters and means what Cypher means.
- **A path-level `WHERE` clause with `AND`/`OR`/`NOT` over properties of
  any node** (`... WHERE p.status <> 'Active' AND o.status IN [...]`). This
  is Cypher's other place for the same test. It is a general predicate
  language, the thing ADR-125 rejected: the condition leaves the node it
  is about, it can join two nodes, and the reader has to assemble the rule
  from parts. The inline form keeps one test next to the node it tests.
- **`=` inside the node as well.** This would mirror Cypher more closely
  but gives one meaning two spellings, and diagnostics and documentation
  would have to say they are the same. It is refused, and the refusal names
  the map.
- **Nested `WHERE NOT`** (`WHERE NOT (c)-[:rests_on]->(p) WHERE NOT (p
  {status: 'Active'})`). This is more general. It is also harder to read,
  and for these checks it says no more than `<>` does.
- **Status quo: patterns for equality, a script for the rest.** The script
  is a second implementation of the record's checks. It reads the
  frontmatter its own way and drifts from the lint (DP-004). It also reports
  nowhere that `fail_on`, `baseline` or `pattern-ok:` can reach.

## Consequences

- **The grammar, the lowering and ADR-129 change together**, as the
  grammar's header requires. ADR-129's list of what the subset admits now
  names this decision.
- **Fired on dmarx/nucleation.** The two worklist checks were written as
  reported patterns and solved against a scratch copy of the record. The
  devlog entry for this change holds the numbers. Grounded on an unread
  work matched the script's section exactly. That was zero rows on the
  live tree, and two rows, the same two, on a copy with one NOTE retired as
  a positive control. Ready for a ruling matched 84 claims against the
  script's 101 unblocked ones. Every difference is a part of the script's
  rule that is not a comparison on one node:
  - 20 claims whose only live objection is already *written in*. The script
    decides that by comparing history dates and body text.
  - 3 claims with no premises of their own, which the script holds back
    through the arguments that conclude them. That is a negation nested
    under another negation.

  The subset still cannot express either.
- **Not decided here:** `IS NULL` / `IS NOT NULL`. A record that wants "has
  no such field" has no case yet.
