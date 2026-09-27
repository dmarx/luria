# How to use journals and fragment directories

Journals and fragments are different because they make different claims about time and source retention.

## Journals

Use a journal for dated observations whose source entries persist.

Example configuration:

```yaml
journals:
  devlog:
    dir: record/devlog.d
    output: docs/devlog
    granularity: month
    title: Development log
```

Create entries through `luria new` using the configured journal workflow.

A journal entry normally means:

> this was observed then.

That is why historical journals should not be treated like current doctrine merely because they contain references that later become inactive.

## Fragment directories

Use fragments for distributed contributions to a shared artifact.

Example:

```yaml
fragments:
  record/changelog.d:
    file: CHANGELOG.md
    style: changelog
```

Contributors write independent fragment files instead of editing the shared target.

`luria collect` assembles them into the target.

The current CLI treats collection primarily as a CI/serialization-point operation, which aligns with [DP-2](../../record/principles.d/DP-002.md): one shared artifact should have one writer where merges serialize ([DP-2](../../record/principles.d/DP-002.md)).

## Choose by semantics

Use:

```text
scheme
```

when stable identity/standing matters.

Use:

```text
journal
```

when temporal observation is the identity and the source persists.

Use:

```text
fragment
```

when a contribution exists to be assembled into another artifact.

Do not choose based only on directory layout.
