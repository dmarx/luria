### Added

- **Path patterns** (`patterns:`): a named relation between documents that
  no single field holds, in Cypher's pattern syntax. For example,
  `(b:CLAIM)<-[:concludes]-(i:INF)<-[:premise_of]-(a:CLAIM)` relates a
  claim to the claims it follows from, through the inference that
  concludes it.
  - Node labels are schemes and edge types are reference fields. A hop
    holds when the relation does, read from either side.
  - The subset: one label per node, `|` between fields, variable length
    (`*`, `*2..`, `*..3`), property maps such as `{status: 'Active'}`, and
    `WHERE NOT` followed by a fixed path. `MATCH`, `RETURN`,
    `OPTIONAL MATCH`, undirected and named edges, shortest paths and writes
    are refused at load, by name.
  - Labels, hops and properties are checked against the schemes when
    `luria.yaml` loads.
- A chain's `relation` or `sibling` may name a pattern in place of a field.
  - The step reads like a field: the first node nests under the last.
  - Its page names the document each step went *through*.
  - It lists paths that stop partway under *Open*, such as an inference
    with premises and no conclusion yet.
  - A chain `invariant` covers pattern steps.
- `examples/argument-map`: claims, inferences and objections, with one
  chain over every step and one that drops steps an objection challenges.
- `luria facts` prints `pattern(P)` for each declared pattern.

### Changed

- `lark` is a new dependency; luria parses patterns with its own grammar
  for the subset.
