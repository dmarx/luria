# Findings and directives reference

This page defines the documentation shape for Luria's finding and acknowledgement system.

The exact finding-class inventory should ideally be generated from the implementation so class names cannot drift from the code.

## Finding reference template

Every finding class should document:

| Field | Meaning |
|---|---|
| Code/class | Stable machine-facing name |
| Trigger | Exact condition |
| Default posture | error / warning / report |
| Repairable? | whether `luria repair` can fix it |
| Acknowledgeable? | whether a directive can accept it |
| Scope | line / block / file / syntactic region |
| Typical resolution | what the author normally does |
| Related doctrine | ADR/DP explaining the behavior |

## Common categories

The implementation currently includes checks in categories such as:

- malformed scheme/frontmatter metadata,
- invalid standing/vocabulary values,
- required and conditionally required fields,
- group/cardinality constraints,
- reference shape/scheme/resolution,
- inactive or unresolved citations,
- relation converse/invariant consistency,
- journal timestamp/path consistency,
- generated-view drift,
- bare reference / link normalization,
- remote verification,
- chain/invariant consistency,
- stale/expired directives.

## Enforcement controls

The `lint` configuration can:

```yaml
lint:
  fail_on: []
  mute: []
  baseline: {}
```

See [ADR-035](../../record/decisions.d/ADR-035.md) for the warn-first enforcement model.

## Acknowledgement directives

An acknowledgement records:

```text
this finding is understood here, for this reason
```

rather than:

```text
disable the check globally
```

Directives may be scoped to a line, block, file, or syntax-aware region depending on the class.

Some directives may carry expiry semantics.

A stale acknowledgement should itself become visible rather than remaining as permanent dead suppression. This follows [DP-1](../../record/principles.d/DP-001.md).

## Common acknowledgement intents

Examples of semantic intent include:

- inactive citation is intentionally historical,
- unresolved identifier is knowingly provisional,
- a code-looking token is a mention/example rather than a citation,
- a handwritten URL is intentional,
- a target check is intentionally bypassed,
- a whole file is outside lint responsibility,
- pinned external content is intentionally bound to a particular content identity.

Use the installed version's directive reference/help for exact spelling. The generated/current implementation should remain authoritative for syntax.
