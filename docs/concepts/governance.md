# Concept: Record theory and self-governance

Some knowledge describes a subject.

Some knowledge describes how knowledge about that subject should be represented, interpreted, and changed.

That distinction gives Luria a natural two-level interpretation.

## Subject record

Call the subject-level knowledge \(R\).

Examples:

```text
Use renewable leases for durable jobs.
Paper LIT-042 supports technique X.
Policy P applies to contractors.
```

## Governing knowledge

Call the governing knowledge \(M\).

Examples:

```text
Every superseded decision identifies a successor.
A SOTA recommendation requires evidence.
Generated views are not authoritative sources.
```

Then the rough judgment:

\[
M;R \vdash x
\]

means:

> under the current record and its current governing rules, does this object or relation remain admissible?

## Governance can be proactive or reactive

A process rule does not have to wait for repeated failure.

It may arise from:

- an incident,
- a near miss,
- a foreseeable vulnerability,
- experience elsewhere,
- repeated friction,
- a deliberate policy.

The important move is making a consequential norm explicit when doing so helps.

## Executable and discursive rules

Some governance can become mechanism:

```text
Superseded decisions must name a successor.
```

Other principles require judgment:

```text
Introduce a new abstraction only when it reduces more complexity than it creates.
```

A mature record theory contains both.

[DP-5](../../record/principles.d/DP-005.md) describes the progression from prose toward convention, mechanism, and guarantee when that promotion is warranted ([DP-5](../../record/principles.d/DP-005.md)).

## Self-amendment

Once process rules themselves have identity and standing, the record can preserve how its governance evolves.

A process rule may even govern how process rules are changed.

That does not require an infinite tower of meta-records. In practice, a corpus can support controlled self-governance.

## Documentation as a governed dependent

Luria's own docs participate in this layer.

A sentence saying:

> `luria init` scaffolds from configuration

depends on [ADR-048](../../record/decisions.d/ADR-048.md).

If [ADR-048](../../record/decisions.d/ADR-048.md) becomes inactive, the sentence should be surfaced for review.

Documentation citations are therefore maintenance edges, not bibliography.
