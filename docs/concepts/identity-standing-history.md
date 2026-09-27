# Concept: Identity, standing, and history

Luria separates three questions that document repositories often collapse.

## Identity

```text
What object is this?
```

Example:

```text
ADR-019
```

Identity should remain stable enough that other knowledge can cite it.

## Standing

```text
What is this object's current state or authority?
```

For a decision scheme:

```text
Proposed
Active
Deferred
Superseded
Rejected
```

For another domain, the vocabulary may mean something else entirely.

A paper's `Active` may mean “worth retaining.” A recommendation's `Active` may mean “currently advised.” Same spelling does not imply same semantics unless the record declares that shared vocabulary intentionally.

## History

A superseded record is not deleted because:

```text
no longer current ≠ never existed
```

Historical identity lets the record answer:

- What did we believe then?
- What replaced it?
- Which implementation was justified by it?
- Which incident led to its replacement?

## Correction versus supersession

Luria's own decision doctrine distinguishes two changes ([ADR-019](../../record/decisions.d/ADR-019.md)):

### Correct the record

The choice is unchanged; the historical account is wrong or incomplete.

The document can be revised visibly.

### Supersede the choice

The choice itself changes.

Create a successor and retire the old standing.

This keeps history epistemically honest.

## Provisional identity

A distributed workflow may not have a safe global serialization point when a branch first creates an entry.

For schemes configured with merge allocation, Luria can issue visibly temporary identities and later concretize them where merges serialize ([ADR-049](../../record/decisions.d/ADR-049.md)).

The important principle is not the spelling of temporary codes. It is that the record can represent:

```text
provisional identity
```

without lying that global order is already known.

See [Use merge-time identity allocation](../how-to/merge-allocation.md).
