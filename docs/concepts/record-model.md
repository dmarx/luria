# Concept: The Luria record model

A Luria record is a repository-native body of knowledge with declared structure, relationships, standing, checks, and projections.

A useful abstraction is:

```text
K = (O, M, R, E)
```

where:

- `O` — ontology: what kinds of things and distinctions exist,
- `M` — governing knowledge: rules about how the record is interpreted and changed,
- `R` — subject-level knowledge,
- `E` — executable machinery: lint, indexing, chains, reports, publication, export.

You do not need this notation to use Luria. It helps explain why the tool is more than a document generator.

## Four record families

### Schemes

Schemes hold referable objects with stable identities, standing, structured fields, and typed relations.

Examples:

```text
ADR-019
RFC-004
LIT-112
POLICY-008
```

Use a scheme when identity and lifecycle matter.

### Journals

Journals hold dated observations.

Their semantic claim is usually:

> this was observed at this time.

A journal entry's identity is temporal rather than a sequential scheme number. Its source persists.

Historical observations should not become stale merely because current doctrine changes, and Luria treats them that way: journal entries and the books they render into are exempt from the reference-status report, so citing a decision that has since been superseded is not reported against a dated entry ([ADR-020](../../record/decisions.d/ADR-020.md)). The same exemption covers uncollected fragments and any file listed in `code.historical`, such as `CHANGELOG.md`.

### Fragment directories

Fragments are distributed contributions to a shared artifact.

Examples:

```text
changelog.d/fix-timeout.md
changelog.d/add-search.md
```

which can be assembled into:

```text
CHANGELOG.md
```

Fragments solve a different problem from journals: their source contributions may be consumed into the shared artifact. [DP-2](../../record/principles.d/DP-002.md) captures the broader concurrency principle: hand out independent contributions and generate/collect the shared artifact where merges serialize ([DP-2](../../record/principles.d/DP-002.md)).

### Remotes

Remotes bring identities owned elsewhere into the local reference model.

A remote may be:

- another Luria record,
- arXiv IDs,
- issue keys,
- standards identifiers,
- any namespace that can be recognized and resolved.

The local record can depend on foreign authority without pretending to own it.

## Identity

Identity answers:

> Which object is this?

Standing answers:

> What authority or status does it have now?

Those must not be conflated.

See [Identity, standing, and history](identity-standing-history.md).

## Fields and vocabularies

Structured fields preserve distinctions that matter to the record.

A vocabulary-backed field can constrain values and make their meaning explicit.

Independent axes should remain independent when their answers can diverge legitimately:

```text
status
consensus
review_state
implementation_state
confidence
```

## Relations

A typed reference is a semantic edge.

It says not just that a string looks like a code, but what scheme the target belongs to and what the field means.

Relations are the substrate from which Luria can derive higher-order structures such as chains.

## Findings

Findings are observations about the record:

- malformed structure,
- invalid standing,
- unresolved relations,
- stale generated views,
- suspicious citations,
- invariant violations,
- stale acknowledgements,
- invariants nothing binds.

Some of these point past the document at the model: an invariant that nothing binds may mean the vocabulary lacks a concept, not that the document is wrong. That is a way of reading findings, not a separate kind of finding.

A finding is not necessarily a verdict. Luria's design intentionally leaves contextual judgment with humans while making the condition visible.

## Projections

Indexes, reports, chain pages, published sites, and exports are derived from the record.

The source remains authoritative.

[DP-3](../../record/principles.d/DP-003.md) gives the general rule: derive projections from the source rather than maintaining parallel copies that drift ([DP-3](../../record/principles.d/DP-003.md)).
