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

Create an entry with `luria new devlog` (the journal is also the default kind, so plain `luria new` does the same):

```console
$ luria new devlog --title "Noticed the index is slow on large records"
record/devlog.d/2026/09/27/215242.md
```

It prints the path of the entry it wrote, under a directory for its date. `luria index` renders the entries into the books at `output`, one per `granularity` period.

A journal entry normally means:

> this was observed then.

That is why historical journals should not be treated like current doctrine merely because they contain references that later become inactive: a journal is historical for reference-status purposes, so its entries are not scanned for citations of retired documents ([ADR-020](../../record/decisions.d/ADR-020.md)).

## Fragment directories

Use fragments for distributed contributions to a shared artifact.

Example:

```yaml
fragments:
  record/changelog.d:
    file: CHANGELOG.md
    style: changelog
```

The default `style` appends each fragment in order; `changelog` inserts each collection under a dated heading, newest first.

Contributors write independent fragment files instead of editing the shared target. `luria new changelog` writes one (named for its filing moment) from the directory's `_template.md`; edit it, and commit it with the change it describes.

`luria collect` assembles them into the target and deletes the fragments it collected. It inserts at a marker, so the target has to exist and carry one — `luria init` creates neither. Create it once, with the marker where collected entries belong:

```console
$ printf '# Changelog\n\n<!-- luria-insert-here -->\n' > CHANGELOG.md
$ luria collect
Collected 1 fragment(s) from record/changelog.d into CHANGELOG.md.
```

Collection is deliberately not per-merge. A bot commit on every merge races in-flight rebases: a branch rebased onto the pre-collection main conflicts in exactly the file fragments exist to keep conflict-free. So it runs on a cadence or on demand — the scaffolded `docs.yml` runs `luria collect --commit` weekly and from a manual dispatch ([ADR-002](../../record/decisions.d/ADR-002.md)). One writer for the shared artifact is [DP-2](../../record/principles.d/DP-002.md)'s rule.

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
