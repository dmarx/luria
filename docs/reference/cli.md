# CLI reference

This page describes the intended public command surface at a high level. Command signatures are derived from the current implementation; use `luria <command> --help` for exact flags in the installed version.

The CLI is deliberately driven from the command functions rather than a second hand-maintained argument parser, reducing interface drift.

## Everyday authoring and checking

### `luria init`

Scaffold the record declared by configuration.

Governing decision: [ADR-048](../../record/decisions.d/ADR-048.md).

### `luria config`

Write a starting `luria.yaml` for editing before scaffolding.

### `luria new [kind]`

Create a journal entry by default or a configured scheme/fragment entry.

Governing decision: [ADR-036](../../record/decisions.d/ADR-036.md).

### `luria lint`

Check the record. This is the primary command whose purpose includes failing the record check.

### `luria index`

Regenerate generated views, including chain outputs.

### `luria link [--fix]`

Find/rewrite bare references as hyperlinks using the same reference model the linter reads.

### `luria relate`

Write a declared relation into an existing document's frontmatter or the configured drafts path.

### `luria repair`

Apply mechanical source repairs discovered by the record scan.

### `luria ack`

Write an acknowledgement directive from a concrete finding with a supplied reason.

## Identity

### `luria concretize`

Assign permanent numbers to temporary merge-allocated codes and rewrite the local record accordingly.

`--check` guards a serialized branch against remaining temporary codes.

Governing decision: [ADR-049](../../record/decisions.d/ADR-049.md).

## External records and publication

### `luria remotes`

Inspect/refresh/check foreign records or identifier namespaces used by this record.

### `luria site`

Stage the record for site publication.

Governing decision: [ADR-042](../../record/decisions.d/ADR-042.md).

### `luria export`

Write a SQLite projection of the record for querying/analysis.

## CI-oriented commands

### `luria reports`

Write status/finding reports as Markdown.

### `luria collect`

Assemble fragment directories into their target views. The implementation describes this as primarily a CI caller because local collection can consume contributions a reviewer was meant to see independently.

## Developer convenience commands

The implementation may expose migration/upgrade commands used while Luria itself evolves.

They are intentionally not documented here as part of the stable user model.
