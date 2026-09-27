# How to resolve, repair, and acknowledge findings

Start with:

```console
$ luria lint
```

Then classify what you learned.

## Mechanical repair

If the correct source change is mechanically determined, use:

```console
$ luria repair
```

This is appropriate for repairs the tool can make without inventing semantic judgment.

Examples can include reference rewrites or missing machine-determinable metadata.

Run lint again afterward.

## Human acknowledgement

If the finding is real but intentional, use:

```console
$ luria ack --help
```

An acknowledgement should carry a reason.

The general rule is:

```text
exception + reason
```

not:

```text
disable the signal
```

[DP-1](../../record/principles.d/DP-001.md) requires suppressions to remain visible in the accounting rather than becoming silence ([DP-1](../../record/principles.d/DP-001.md)).

## Promote a warning class

When a warning class is ready to become a guarantee:

```yaml
lint:
  fail_on:
    - some-class
```

Luria's warn-first enforcement model is governed by [ADR-035](../../record/decisions.d/ADR-035.md) ([ADR-035](../../record/decisions.d/ADR-035.md)).

## Baseline a known residue

For an adopting corpus, a baseline can express:

> this many findings are currently known; more is regression.

This is often more useful than either hiding the class or failing immediately on existing debt.

## Mute only when the signal itself is unwanted

Muting removes the class from ordinary visibility.

Prefer acknowledgement or baseline when the condition is meaningful but currently accepted.

## Treat stale acknowledgements as findings

If the underlying condition disappears, the old acknowledgement should not remain forever as dead documentary residue.

The acknowledgement mechanism itself is governed knowledge and should stay current.
