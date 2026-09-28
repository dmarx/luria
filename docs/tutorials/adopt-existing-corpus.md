# Tutorial: Adopt Luria around an existing corpus

This tutorial assumes you already have a body of documents.

For example:

```text
docs/
  rfc-001.md
  rfc-002.md
  rfc-003.md
  incident-2026-04.md
```

The goal is not to redesign the corpus into a Luria-shaped repository before Luria can help. Identify one distinction or dependency worth making explicit, wrap Luria around it, and add governance as it earns its keep.

This page is the short path. [Adopting Luria](../adopting.md) covers the scaffold and CI in depth, and [Importing an existing corpus](../importing.md) covers converting material in bulk.

That is [DP-14](../../record/principles.d/DP-014.md) made operational: meet the project where it is.

## 1. Inventory what already has meaning

Ask:

- Which documents have stable identities people already cite?
- Which have standing such as active/rejected/superseded?
- Which relations matter?
- Which collections are historical observations rather than current doctrine?
- Which pages are authoritative and which are summaries?
- Which conventions are enforced only by memory?

Do not begin by inventing a complete ontology.

## 2. Write the smallest useful `luria.yaml`

If RFCs are the clearest existing family, declare only them first.

```yaml
vocabularies:
  rfc-status:
    Proposed: {}
    Accepted: {}
    Rejected: {}
    Superseded: {}

schemes:
  RFC:
    dir: docs/rfcs
    active: Accepted
    fields:
      status:
        vocabulary: rfc-status
```

`active` names the status that means *in force*, and it must be a word in the scheme's status vocabulary. Without the `rfc-status` vocabulary, `Accepted` is itself a violation: the default vocabulary is `Active`, `Proposed`, `Deferred`, `Superseded`, `Rejected`. If your corpus already says `Active`, drop both `active` and the vocabulary and use the default.

Give the scheme a directory of its own. Every file in a scheme's `dir` is an entry, and the filename is the code, so move the RFCs there under their codes:

```console
$ mkdir docs/rfcs
$ git mv docs/rfc-001.md docs/rfcs/RFC-001.md
$ git mv docs/rfc-002.md docs/rfcs/RFC-002.md
$ git mv docs/rfc-003.md docs/rfcs/RFC-003.md
```

With no `output`, the scheme's generated index lives beside the sources in `docs/rfcs/`. You do not need to force a `record/` source directory and a separate view just to “look like Luria”; the [collocated example](../adopting.md#shape-the-record-to-the-project) works this way.

## 3. Inspect initialization before changing anything

```console
$ luria init --dry-run
```

Review what Luria would add. Besides the RFC scheme's `_template.md` and `README.stub`, `init` adds two GitHub Actions workflows (`.github/workflows/docs.yml` and `pages.yml`), a `CLAUDE.md` for coding agents, a `docs/README.md` docs index, and the default changelog and devlog directories under `record/`. It writes only what is missing: an existing `CLAUDE.md` or `docs/README.md` is skipped and reported.

Then:

```console
$ luria init
```

The configuration is the declaration of the record shape; initialization follows it rather than inventing another shape ([ADR-048](../../record/decisions.d/ADR-048.md)).

## 4. Give each entry frontmatter

Two things fail the lint from the first run, and neither is a warning you can defer:

- every file in the scheme's `dir` without YAML frontmatter (`no YAML frontmatter (see _template.md)`);
- every page directly in `docs/`, or in a docs subdirectory that is not a scheme or view directory, that `docs/README.md` does not link (`missing index entry for incident-2026-04.md`).

So identity and standing go on each entry as part of adoption. The minimum is `status:` and a quoted `title:`, and a body heading, if the file has one, must read `# CODE: title`:

```markdown
---
status: Accepted
title: 'Durable background jobs'
---

# RFC-001: Durable background jobs
```

Link the remaining pages from `docs/README.md` by adding a line to its list:

```markdown
- [Incident, April 2026](incident-2026-04.md)
```

Then build the views and check:

```console
$ luria index
$ luria lint
```

Run `luria index` first: the scaffolded `docs/README.md` links views that only it writes. A `CLAUDE.md:4: docs/design-principles.md resolves to nothing` advisory is expected: the scaffolded `CLAUDE.md` points at a principles page this config does not generate, so edit that line. It does not fail the lint.

For a corpus too large to edit by hand, write a script and commit it ([Importing an existing corpus](../importing.md)). Three traps from that page are worth knowing before you start:

- `date:` is the *filing* date, not the document's own date. Imported publication dates make every `Proposed` entry look years overdue; put the source date in a field of your own.
- Quote every imported value. Titles contain colons and apostrophes, and an unquoted one parses as something else.
- A template's example reference needs a placeholder code the scheme will never allocate, acknowledged once (see [placeholder codes](../importing.md#placeholder-codes-in-templates)).

What *is* warn-first is everything after that: retired citations, unresolved codes, stale directives and the other warning classes print, and fail only when named in `lint.fail_on` ([ADR-035](../../record/decisions.d/ADR-035.md)). Use those findings as an inventory of what remains, not as proof that adoption failed.

## 5. Add one relation that answers a real question

For example:

```text
Which RFC replaced this one?
```

That one is built in: every scheme has a `superseded_by` reference, and an entry whose `status` is `Superseded` must fill it ([ADR-071](../../record/decisions.d/ADR-071.md)). Record it with `luria relate RFC-001 superseded_by RFC-003`.

Or:

```text
Which decision did this implementation realize?
```

Declare a typed `decision` reference in the implementing scheme's `references` table. The field name becomes the relation, checked for shape, scheme and resolution ([ADR-071](../../record/decisions.d/ADR-071.md)). A declared reference is required unless it says `required: false`.

Prefer one relation that pays rent over a large graph nobody uses.

## 6. Generate one projection

Choose a view currently maintained by hand, such as an RFC index.

`luria index` already generated one: `docs/rfcs/README.md`, with a page per status, and the scaffolded `docs/README.md` links it. Delete the hand-maintained copy (and its entry in `docs/README.md`) and point readers at the generated one.

This is often the easiest place to demonstrate immediate value: the projection stops being a second source that can drift ([DP-3](../../record/principles.d/DP-003.md)).

## 7. Tighten only when the corpus is ready

A typical progression is:

```text
visible finding
    ↓
known backlog
    ↓
baseline (`lint.baseline`) or acknowledgements
    ↓
repair the corpus
    ↓
promote the class (`lint.fail_on`) when zero/new-regression is meaningful
```

Acknowledgements are [comment directives](../directives.md); both settings are in the [configuration reference](../configuration.md).

Do not turn every new signal into an immediate hard failure.

## 8. Let the model emerge from friction

You may discover:

- “review state” and “standing” are different,
- incidents are historical observations and fit a journal better,
- RFCs contain multiple independently citable decisions,
- a hand-maintained lineage should become a chain,
- a category vocabulary is hiding a missing distinction.

Those discoveries are the ontology becoming more explicit.

Adoption is successful when the record gains useful semantics, not when it matches a canonical example.
