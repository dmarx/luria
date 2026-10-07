---
status: Proposed
title: 'A logic core in clingo, behind a procedural shell'
version: 1
tags:
- architecture
- mechanism
date: '2026-10-07'
summary: >-
  The parts of luria that decide things about the record's graph —
  converse pairs, invariants, chain edges, contract checks on references,
  config consistency, retired citations — move from hand-written Python
  walks to Answer Set Programming rules evaluated by clingo, over facts the
  Python extracts. Python keeps parsing, rendering, editing, git and the
  network, and turns derived facts into findings, edits and pages. The move
  is one subsystem at a time, each held to byte-identical `luria lint` and
  `luria index` output against the last release on every real record.
  Rejected: a full rewrite, Cypher or an embedded graph database, SQLite
  recursive CTEs, a hand-rolled Datalog evaluator, and staying in Python.
influenced_by:
- ADR-060
- ADR-097
- ADR-106
- ADR-125
- ADR-126
---

# ADR-tmp8z08x: A logic core in clingo, behind a procedural shell

## Context

[ADR-126](ADR-126.md) let a reference name several schemes. Within a day it surfaced three
defects and two limits, all in code that walks the record's graph:

- A symmetric relation crossing schemes was read as held on neither side,
  because two relations were kept in a dict keyed by field name and the
  names collided ([#358](https://github.com/dmarx/luria/issues/358)). The fixer then appended a duplicate edge on every
  run.
- A chain page called every second parent "also extends", whatever the chain
  walked ([#359](https://github.com/dmarx/luria/issues/359)).
- A chain cannot walk a relation that may leave its scheme, and cannot hop
  through an intermediate scheme, so a downstream record's lines of
  argument stop wherever an inference document sits between two claims.
- The reports that downstream record wanted next — a thesis no objection
  challenges, a conceded claim not in force — would each be another
  hand-written walk.

Each was a special case added to a hand-written walk, and each fix invited
the next. The work these walks do is relational: joins, transitive
closure, and "no such edge exists". That is what Datalog-family languages
are for. A rough census of the 22,300 lines puts that kind of decision at
about a quarter to a third of the code: `contract`, `relations`,
`invariants`, the walk in `chains`, `ref_status`, `statuses`, `edges`, the
graph checks in `lint`, and the consistency checks in `config`. The rest
parses text, renders pages, edits files, or talks to git and the network,
and is better as Python.

[ADR-125](ADR-125.md) rejected a predicate language for conditions because a reader
should see the rule in the line. That concern is about what a person writes
in `luria.yaml`, and nothing here changes it: the configuration stays
declarative. The logic programs are luria's implementation, not its
configuration.

## Decision

**A logic core behind a procedural shell.**

1. **Facts.** Python reads the configuration, every document's frontmatter
   and the HEAD baseline, and emits facts: `scheme/1`, `ref/2`,
   `ref_target/3`, `ref_converse/3`, `doc/2`, `value/3`, `edge/3`,
   `head_value/3` and so on. `luria facts` prints them, so a person or an
   agent can query the record without luria.
2. **Rules.** Each ported subsystem is a `.lp` program in `luria/logic/`.
   clingo grounds it against the facts and returns derived atoms.
3. **Shell.** Python turns derived atoms into the findings, repairs and
   pages it produced before, in the same words. Provenance stays: a rule
   derives the "because" a finding prints.

**clingo**, from the Potassco project, is the engine. It is actively
maintained, ships manylinux wheels for every Python luria supports (2.2 MB
for 5.8.2), and evaluates stratified Datalog as a subset of Answer Set
Programming. Programs here stay in that stratified subset: one answer set,
no choice rules, so evaluation is deterministic, as generated views must
be.

**The migration is one subsystem at a time, each under parity.** A port
merges only if `luria lint` output and every file `luria index` writes are
byte-identical to the last release's on luria's own record, each example,
dmarx/nucleation and dmarx/anthology-of-the-sota — or the difference is a
known defect the port fixes, named in its PR. The Python path is deleted in
the same PR, so there is never a second implementation to drift from.

Order, smallest and purest first:

1. invariants and the edges a chain walks;
2. converse-pair decisions in `relations` ([#358](https://github.com/dmarx/luria/issues/358)'s class);
3. config consistency (converses, invariants, chain scope, declared
   schemes);
4. reference checks in `contract`;
5. retired-citation status in `ref_status`.

User-facing queries (a `queries:` table, and chains over a derived relation
rather than a field) follow once the engine is in place. They are outside
this decision.

## Alternatives considered

- **A full rewrite in a logic language.** Rendering, prose scanning, file
  editing, git and network work are procedural, and a logic language does
  them worse. Most of the code would get harder to read in exchange for
  purity.
- **Cypher, or an embedded graph database.** Its path patterns read well,
  but it needs an engine luria would have to ship, the embedded options are
  heavy for a lint CLI, and named rules that build on one another are
  clumsier than in Datalog.
- **SQLite recursive CTEs.** No dependency, since SQLite is in the standard
  library, and enough for transitive closure and `NOT EXISTS`. But rules do
  not compose by name, and the programs would be harder to read than the
  Python they replace.
- **A hand-rolled Datalog evaluator.** No dependency, but luria would then
  maintain an evaluator: semi-naive evaluation, stratification, error
  reporting. clingo is that, maintained by people whose subject it is.
- **Staying in Python, fixing each case as it comes.** This is what produced
  the context above.

## Consequences

- **A new dependency**, `clingo`. It is binary wheels only; a platform
  without one would need to build from source.
- **Contributors meet a second language** for the core. The programs are
  short and the shell keeps every user-facing string in Python.
- **Kill criteria, stated before the work:** stop and revert a port if its
  findings or "because" lines get worse, if lint on the anthology becomes
  materially slower, or if the rules read worse than the Python they
  replace.
- **Tracking.** One pull request into `main` tracks the project, and each
  step is a pull request into the tracker's branch.
