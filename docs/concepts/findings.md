# Concept: Findings and truth maintenance

Luria's lint is not only a style checker.

It is a mechanism for making changes in the record produce visible consequences elsewhere.

## Contextual invalidation

At time \(t\):

```text
IMPLEMENTATION-004 → DECISION-012 [Active]
```

At time \(t+1\):

```text
DECISION-012 [Superseded]
```

The implementation file did not change.

Its context did.

A truth-maintenance system needs to surface that difference.

## Findings are observations

A finding can indicate:

- malformed metadata,
- invalid standing,
- missing required fields,
- unresolved codes,
- suspicious inactive citations,
- broken targets,
- stale generated views,
- relation/converse inconsistencies,
- invariant violations,
- stale or expired acknowledgement directives,
- unbound chains,
- other declared contract failures.

Not every finding has the same epistemic force.

## Warn first, enforce deliberately

Luria's enforcement dial separates:

```text
reported
```

from:

```text
fatal
```

A project can promote selected warning classes to failures when that class is ready to become a guarantee ([ADR-035](../../record/decisions.d/ADR-035.md)).

Baselines support a related statement:

> this is the known residue; do not allow regression beyond it.

That is often more useful for an adopting corpus than either “fail immediately” or “hide the class.”

## Acknowledgements

Sometimes the finding is real and the use is intentional.

An acknowledgement should say:

- which condition is being accepted,
- where,
- why.

[DP-1](../../record/principles.d/DP-001.md)'s corollary is important: a suppression must not become silence. Acknowledged findings remain countable, and stale acknowledgements should themselves become visible ([DP-1](../../record/principles.d/DP-001.md)).

## Mechanical repair versus human judgment

A useful operating distinction:

```text
mechanically determined repair
```

versus:

```text
semantic decision
```

`luria repair` can apply source changes the tool can determine safely.

`luria ack` can write an acknowledgement from an actual finding when the user supplies the reason.

The linter should not invent semantic conclusions merely because it discovered the condition.

## Findings can challenge the ontology

A chain invariant failure may mean the metadata or relation is wrong.

It may also mean the vocabulary lacks the concept that actually binds the line.

That matters: Luria validates records against an ontology, but some findings can become evidence that the ontology itself should change.

## The loop

```text
change
  ↓
lint
  ↓
finding
  ↓
repair / acknowledge / revise model
  ↓
lint again
```

The point is not zero warnings at any cost.

The point is that changes which matter become inspectable.
