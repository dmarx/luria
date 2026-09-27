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

It links bare codes, fills a journal entry's `created:` from its path, moves a note out of `status:` into `status_note:` and `superseded_by:`, and retires a stale configuration reference; a second run changes nothing. The other side of a declared relation pair is written by `luria link --fix` (see [relations](relations.md)).

Run lint again afterward.

## Violations and warnings

`luria lint` prints two kinds of finding, and only one of them is yours to dial.

- **Violations** always exit 1: a status outside the vocabulary, `Superseded` with no `superseded_by:`, a reference field that does not resolve to a code of the scheme it names, a bare code `luria link --fix` would link, a docs page missing from `docs/README.md`, and the rest of the list under [`luria lint`](../cli.md#luria-lint). Each is always wrong, so none of the dials below apply to it — fix the source.
- **Warnings** print and pass. Each belongs to a named class (`retired-citations`, `unresolved-codes`, `one-sided-relations`, …) and is a judgement call, which is what the rest of this page is about.

## Human acknowledgement

If a warning is real but intentional, acknowledge it where it occurs. For the citation scan — a deliberate citation of a document that is not in force, or a code that names nothing on purpose — `luria ack` writes the directive for you. With no arguments it lists what could be acknowledged and writes nothing:

```console
$ luria ack
RFC-001 — cited but not in force, 1 unacknowledged site(s)
    record/rfcs.d/RFC-003.md:36

luria ack <CODE> --reason "..." writes the directive at each site above.
$ luria ack RFC-001 --reason "the draft this one answers"
acknowledged RFC-001 at record/rfcs.d/RFC-003.md:36
wrote 1 directive(s)
```

It writes `inactive-ok:` or `unresolved-ok:` only, takes the code from the scan rather than from you, and refuses to run without `--reason`. `--scope file` writes one directive per file instead of one per citation; `--until YYYY-MM-DD` gives it an expiry. Every other class that has a directive (`url-ok:`, `target-ok:`, `source-ok:`, …) is written by hand; [comment directives](../directives.md) has the full vocabulary and which class each one answers.

An acknowledgement should carry a reason.

The general rule is:

```text
exception + reason
```

not:

```text
disable the signal
```

[DP-1](../../record/principles.d/DP-001.md) requires suppressions to remain visible in the accounting rather than becoming silence.

## Promote a warning class

When a warning class is ready to become a guarantee, name it in `lint.fail_on` in `luria.yaml`:

```yaml
lint:
  fail_on:
    - retired-citations
```

From then on an unacknowledged finding in that class fails the lint; acknowledged ones still pass, so the directives keep working under enforcement. The name must be a real warning class — `luria lint` lists the known ones if you misspell one, and treats the unknown name itself as a violation.

Luria's warn-first enforcement model is governed by [ADR-035](../../record/decisions.d/ADR-035.md).

## Baseline a known residue

For an adopting corpus, a baseline can express:

> this many findings are currently known; more is regression.

```yaml
lint:
  baseline:
    retired-citations: 12
```

Up to 12 findings in the class print as warnings; a 13th fails the lint, and the run tells you when the count has dropped so you can lower the number. A class may not be both baselined and in `fail_on` (`fail_on` already means a baseline of 0).

This is often more useful than either hiding the class or failing immediately on existing debt.

## Mute only when the signal itself is unwanted

```yaml
lint:
  mute:
    - narrow-titles
```

Muting removes the class from what `luria lint` prints; `luria reports` still carries the full accounting.

Prefer acknowledgement or baseline when the condition is meaningful but currently accepted.

## Treat stale acknowledgements as findings

If the underlying condition disappears, the old acknowledgement should not remain forever as dead documentary residue. A directive that no longer suppresses anything — the document went Active, the citation was deleted — is reported under `stale-directives`, which `fail_on` can promote like any other class. A directive whose `until` date has passed stops suppressing and is reported under `expired-directives`, so the finding it covered comes back with an explanation.

The acknowledgement mechanism itself is governed knowledge and should stay current.
