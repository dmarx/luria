# Concept: Findings and truth maintenance

Luria's lint is not only a style checker.

It is a mechanism for making changes in the record produce visible consequences elsewhere.

## Contextual invalidation

At one time:

```text
IMPLEMENTATION-004 → DECISION-012 [Active]
```

Later:

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
- invariants nothing binds (`unbound-relations` for an edge, `unbound-lines` for a whole chain line),
- other declared contract failures.

Not every finding has the same epistemic force.

## Violations and warnings

`luria lint` prints two kinds of finding.

**Violations** always fail the build. They are the checks whose failure is always wrong and mechanically fixable: a value outside a closed vocabulary, a missing required field, a superseded document with no `superseded_by:`, a `title:` that disagrees with the heading, a code cited in prose without a link, a docs page missing from its index, a hand-written file inside a generated view. No setting turns them off.

**Warnings** belong to named classes — `retired-citations`, `unresolved-codes`, `broken-targets`, `remote-drift`, `one-sided-relations`, `unbound-relations` and the rest — and by default they are reported without failing.

## Warn first, enforce deliberately

Warning classes sit on an enforcement dial ([ADR-035](../../record/decisions.d/ADR-035.md)), set under `lint:` in `luria.yaml`:

- `fail_on` promotes a class to a failure, when that class is ready to become a guarantee;
- `baseline` holds a class to a count — the build fails only when the class grows past it;
- `mute` stops the lint printing a class. `luria reports` still renders the full accounting, so muting changes what the command prints, not what the record says.

A baseline states:

> this is the known residue; do not allow regression beyond it.

That is often more useful for an adopting corpus than either “fail immediately” or “hide the class.” The full list of violations and warning classes is under [`luria lint`](../cli.md#luria-lint); the syntax for the dials is in [Configuration](../configuration.md).

## Acknowledgements

Sometimes the finding is real and the use is intentional.

An acknowledgement should say:

- which condition is being accepted,
- where,
- why.

[DP-1](../../record/principles.d/DP-001.md)'s corollary is important: a suppression must not become silence. Acknowledged findings remain countable, and stale acknowledgements should themselves become visible.

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

An acknowledgement divides the work the same way: *which* condition is accepted is mechanical, so `luria ack` takes it from the finding itself; *why* it is acceptable is judgement, so the reason comes from a person. A hand-transcribed acknowledgement is the one place a suppression can be silently wrong — it can vouch for the wrong code and quiet nothing. The directive syntax is in [Comment directives](../directives.md); the workflow is in [Resolve, repair, and acknowledge findings](../how-to/findings.md).

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
