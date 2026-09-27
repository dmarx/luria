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

Mechanically, standing is the document's `status:`, a value from a vocabulary the scheme names in `fields.status.vocabulary` (ADR-085). One word in it — the scheme's `active:`, `Active` by default — means **in force**. Every other value means out of force, and citing an out-of-force document is what the lint reports as a retired citation.

For a decision scheme, `luria init` ships:

```text
Proposed
Active
Deferred
Superseded
Rejected
```

These are defaults, not laws. A scheme whose words are `Kept` and `Dropped` sets `active: Kept` and works the same way. The retirement pair is configurable too: `retires_on` names the status that means replaced (default `Superseded`) and `successor` the field that names the replacement (default `superseded_by`). A document carrying the `retires_on` status must fill that field — a superseded document with no `superseded_by:` is a violation (ADR-071).

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

The document is revised in place, visibly: its `version:` is bumped and a `history:` entry says what the previous version claimed and why that was wrong. The lint checks that `version:` agrees with `history:`. A silent rewrite is what this rules out; being wrong out loud is not.

### Supersede the choice

The choice itself changes.

Create a successor, set the old document's status to `Superseded`, and name the successor in its `superseded_by:`.

The test for which case applies: would a reader who acted on the old version have done something different? If yes, the choice changed — supersede.

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
