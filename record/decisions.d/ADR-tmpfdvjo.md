---
status: Proposed
title: 'A chain may walk a named path pattern'
version: 1
tags:
- record
- mechanism
date: '2026-10-13'
issue: '#371'
summary: >-
  A record may declare named path patterns in Cypher's pattern syntax, such
  as `(a:CLAIM)-[:premise_of]->(i:INF)-[:concludes]->(b:CLAIM)`. Node labels
  are schemes, edge types are reference fields, and an edge is a relation as
  `held/4` reads it. luria parses patterns with its own lark grammar for
  the subset and lowers them to clingo rules over the record's facts, so
  the logic core stays the one engine. A chain names a pattern in `relation` or `sibling` as it names a
  field. The pattern's end nodes are the step and its named intermediates
  render as "through". The subset is checked against the schema at load and
  is stratified by construction. Rejected: a field list on the scheme,
  clingo rule bodies as queries, a graph engine, grand-cypher over
  networkx, Raqlet, and GraphGlot as the parser.
influenced_by:
- ADR-106
- ADR-125
- ADR-126
- ADR-127
---

# ADR-tmpfdvjo: A chain may walk a named path pattern

## Context

A chain walks reference fields: `relation` names one field or several
([#211](https://github.com/dmarx/luria/issues/211)), `sibling` one more, all declared on the chain's own scheme. A chain
is a sequence within one scheme ([ADR-106](ADR-106.md)), and [ADR-126](ADR-126.md) kept it so: a chain
walks a relation only if its own scheme is the sole target, because
skipping the edges that leave would drop steps without a finding.

That leaves lines the record states and no chain can draw. [ADR-127](ADR-127.md) names
one: in a downstream record an argument runs claim → inference → claim, and
the chain stops at the inference. A larger one is on the way. A record
that develops arguments wants a view that walks from a question, through
its candidate answers, the objections to them and the replies, to what was
concluded. Such views are the units a manuscript could later be composed
from.

[ADR-127](ADR-127.md) left "user-facing queries … and chains over a derived relation" for
after the logic core. It rejected Cypher as an *engine* ("it needs an
engine luria would have to ship"), but said its path patterns read well.
[ADR-125](ADR-125.md) sets the bar for anything in `luria.yaml`: a reader sees the rule in
the line. A path pattern meets that bar. A clingo rule body does not.

The questions these views ask are path questions: which documents connect
by this sequence of typed hops, through what. Path patterns are the
notation built for that, and the translation from a pattern to Datalog is
mechanical:

- a hop is a join;
- alternation is a union;
- variable length is transitive closure;
- `WHERE NOT` over a pattern is stratified negation.

## Decision

**A record may declare named path patterns**, and a chain may walk one.

```yaml
patterns:
  leads_to: (a:CLAIM)-[:premise_of]->(i:INF)-[:concludes]->(b:CLAIM)
  answered: (q:Q)<-[:answers]-(c:CLAIM)
  unchallenged: (c:CLAIM) WHERE NOT (c)<-[:challenges]-(:OBJ)

chains:
  argument:
    scheme: CLAIM
    relation: leads_to
    output: docs/arguments.md
```

### What a pattern means

- **A node label is a scheme.** A node carries exactly one label, or none
  when it refers back to a variable bound earlier in the pattern (`(c)` in
  `WHERE NOT (c)<-[:challenges]-(:OBJ)`) and inherits that node's scheme.
  So each document's scheme is known at every position.
- **An edge type is a reference field** declared on the scheme of the node
  the arrow leaves. `(a:S)-[:f]->(b:T)` holds when `held(S, f, a, b)`
  does. That is the reading every chain and invariant already uses, so a
  hop stated only on its converse side counts.
- **`<-[:f]-` reads the same field from the other end.** `(q:Q)<-[:answers]-(c:CLAIM)`
  holds when `c`'s `answers` names `q`.
- **The target label filters.** A field that may name several schemes
  ([ADR-126](ADR-126.md)) is a valid hop if the next node's label is one of its targets.
  Codes landing in the other targets are not matches, and that is visible
  in the line. This is not the silent drop [ADR-126](ADR-126.md) refused for chains: the
  pattern names the scheme it follows.

### The subset

**In:**

- one label per node, or a bare reference to a node already bound;
- edge types with direction, and `|` between field names;
- variable length on a single edge (`-[:extends*1..]->`, a lower bound of
  at least 1);
- literal equality on a node's frontmatter (`{status: 'Active'}`);
- `WHERE NOT` followed by a pattern that is not itself variable-length.

**Out**, refused at load:

- `RETURN`, aggregation and ordering;
- `OPTIONAL MATCH`;
- several `MATCH` clauses;
- undirected edges;
- shortest path;
- any write clause.

A pattern is written without `MATCH`. The grammar has no production for
anything outside the subset, so an out-of-subset pattern fails to parse.
The refusal names the construct for the keywords and shapes people will
reach for (`MATCH`, `RETURN`, `OPTIONAL`, an undirected edge). Anything
else gets the parse position.

### How patterns are parsed and evaluated

- **Parsing:** a [lark](https://github.com/lark-parser/lark) grammar for
  the subset, in `luria/`, parsed LALR. The grammar is the subset's
  definition: what it accepts is what this decision admits, and widening
  the subset is a reviewed change to one file.
- **Lowering:** luria lowers the parse tree to a clingo program over
  `held/4`, `doc/2` and `value/4`, one derived predicate per pattern. The
  logic core stays the one engine ([ADR-127](ADR-127.md)).
- **Dependency:** `lark`, a core dependency. It is pure Python with no
  dependencies of its own, stable at 1.x, and small enough that an extra
  with an install-line refusal would cost more than it saves.

### Checked at load

- each label is a declared scheme;
- each edge type is a reference declared on the node it leaves, and the
  next label is among that field's targets;
- each property is a field the node's scheme can hold;
- the construct is in the subset.

These join the refusals in `consistency.lp`.

### Stratified by construction

The subset admits no recursion through negation. `WHERE NOT` takes only
patterns that are not variable-length, and variable length is positive.
So every lowered program has one answer set, and the views it feeds are
deterministic, as [ADR-127](ADR-127.md) requires.

### How a chain uses a pattern

- **The ends are the step.** A chain may name a pattern in `relation` or
  `sibling`, alone or beside fields in one spine ([#211](https://github.com/dmarx/luria/issues/211)). The pattern's
  first and last nodes must both be labelled with the chain's scheme. They
  are the edge the chain walks.
- **Named intermediates are "through".** A variable bound on an inner node
  (`i` above) is what the step renders as "— through INF-004". An
  anonymous inner node (`(:INF)`) is matched and not shown.
- **A match that stops partway is shown.** A document of the chain's
  scheme from which at least one hop of the pattern matches, and the whole
  pattern does not, is listed on the chain's page as "open at" the
  furthest node reached. An inference with premises and no conclusion yet
  is a legitimate state, so this is not a lint finding. Not drawing it
  would read exactly like a line that ends there ([DP-15](../principles.d/DP-015.md)).
- **A chain's `invariant` is checked between the two ends**, as for any
  edge it walks.

Read-only throughout: a pattern is never written into frontmatter, has no
converse, and is never completed by `luria link --fix`.

## Alternatives considered

- **A field list on the scheme** (`composed: {leads_to: [premise_of,
  concludes]}`), the first draft of this decision. It is a path pattern
  with fixed length, no alternation, no variable length and no negation, in
  a syntax of luria's own that the first need beyond it would have to
  replace.
- **clingo rule bodies as queries.** These are the most general and need
  no parser. They fail [ADR-125](ADR-125.md)'s test of a rule read in the line. They can
  recurse through negation and lose determinism. And luria cannot check
  their endpoints at load, or name an intermediate, because it does not
  know what the rule means.
- **A graph engine** (an embedded graph database executing Cypher).
  [ADR-127](ADR-127.md) rejected this for the engine it ships. The decision here takes
  the syntax and leaves the engine.
- **[grand-cypher](https://pypi.org/project/grand-cypher/)**, which executes
  a Cypher subset over networkx graphs. It is a second evaluation engine
  beside clingo, with results outside the logic core. Negated patterns and
  `OPTIONAL MATCH` are listed there as unimplemented, and the first is
  needed now, the second for the outline view.
- **[Raqlet](https://arxiv.org/abs/2508.03978)**, a research compiler from
  Cypher and SQL/PGQ to Datalog (CIDR 2026). It is the closest thing to a
  ready-made translation. No public release was found, it targets
  Soufflé-style Datalog over a schema-generated EDB rather than clingo over
  `held/4`, and it covers full Cypher, aggregation included, which is more
  than this needs. The lowering here is small, because the subset is.
- **[GraphGlot](https://github.com/averdeny/graphglot) as the parser.**
  It is a pure-Python, sqlglot-style parser for GQL and Cypher, and it
  parsed every pattern here. But it does no translation to Datalog or SQL,
  so luria would write the lowering either way. What it would add is a
  parse tree shaped like a full GQL program, fifteen levels of wrapper
  above the path, for a lowering that reads only the path. It is pre-1.0
  with releases days apart, so its shapes would need pinning. And it
  accepts all of Cypher, so the subset would be enforced by a second pass
  over a tree that had already said yes. A grammar of luria's own is about
  fifteen lines, accepts only the subset, and hands the lowering the tree
  it reads.
- **GQL syntax instead of Cypher.** GQL is the ISO standard (39075:2024).
  Cypher is the one people know, and its variable-length (`*1..` against
  `->{1,}`) and negation forms are shorter. Admitting GQL spellings later
  is a grammar change, not a design change.
- **Status quo.** Records that argue through intermediate documents keep
  writing their lines in prose, one paragraph per participant, which is
  the duplication chains were built to end ([#171](https://github.com/dmarx/luria/issues/171)).

## Consequences

- **A new dependency**, `lark`, pure Python with none of its own.
- **luria owns the grammar and its error messages.** The subset is small
  on purpose, and the grammar is where that is enforced. A request to
  widen it is a change to the grammar, the lowering and this decision
  together.
- **Fired before writing this.** A scratch grammar of 15 rule lines (lark
  1.3.1, LALR) parsed every pattern in this decision, plus the
  variable-length and property-map forms. It refused `OPTIONAL MATCH`, an
  undirected edge, `MATCH … RETURN` and a trailing `RETURN`. The first try
  caught a rule this decision had wrong: `WHERE NOT (c)…` refers to a bound
  node without a label, so "every node carries a label" became "a label,
  or a reference to a node already bound". Its refusals are lark's
  "unexpected token at column N", which is why naming the common
  constructs is a separate step. The lowering is not written yet.
- **The facts become an interface.** Patterns lower to `held/4`, `doc/2`
  and `value/4`, so changing those predicates changes what patterns mean.
- **Parity.** Records that declare no pattern are unchanged. Under
  [ADR-127](ADR-127.md)'s rule, the change merges only if `luria lint` and `luria index`
  output is byte-identical on luria's own record, every example,
  dmarx/nucleation and dmarx/anthology-of-the-sota.
- **Chain code** must accept a pattern name in `relation`. Today that
  touches the chain loader, `consistency.lp`'s `walk_undeclared` and
  `walk_leaves`, the chain facts, and the page's intro sentence, which
  should print the pattern.
- **One name, one meaning:** a pattern and a reference field may not share
  a name on a scheme a chain walks.
- **The chain page grows "through" and "open at".** Both need tests against
  a real record, and an example that declares the shape. `examples/` has
  none today.
- **Not decided here, and made possible by it:**
  - an outline view that walks a pattern from a root across schemes, which
    is where `OPTIONAL MATCH` would earn its place;
  - transcluding document bodies, so views can compose into a manuscript;
  - patterns rendered as reports, such as `unchallenged` above.

  Each is its own decision. This one keeps named intermediates and partial
  matches available to them.
