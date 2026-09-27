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

The goal is not to redesign the corpus before Luria can help. Start with one useful semantic distinction and add governance incrementally.

That follows DP-14: Luria should meet the project where it is ([DP-14](../../record/principles.d/DP-014.md)).

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
schemes:
  RFC:
    dir: docs
    active: Accepted
```

If the existing layout already collocates sources and views, you do not need to force an immediate source/view split just to “look like Luria.” The record model can be introduced before a structural reorganization.

## 3. Inspect initialization before changing anything

```console
$ luria init --dry-run
```

Review what Luria would add.

Then:

```console
$ luria init
```

The configuration is the declaration of the record shape; initialization should follow it rather than inventing another shape ([ADR-048](../../record/decisions.d/ADR-048.md)).

## 4. Add metadata incrementally

Do not require a flag day where every old document becomes perfect.

Add stable identity and standing to the subset that matters first.

Run:

```console
$ luria lint
```

Use the findings as an inventory of what remains, not as proof that adoption failed.

Luria's warn-first enforcement model exists specifically so a pre-existing corpus can expose a backlog before turning every class into a build gate ([ADR-035](../../record/decisions.d/ADR-035.md)).

## 5. Add one relation that answers a real question

For example:

```text
Which RFC replaced this one?
```

Declare `superseded_by`.

Or:

```text
Which decision did this implementation realize?
```

Declare a typed `decision` reference.

Prefer one relation that pays rent over a large graph nobody uses.

## 6. Generate one projection

Choose a view currently maintained by hand, such as an RFC index.

Generate it with `luria index`.

This is often the easiest place to demonstrate immediate value: the projection stops being a second source that can drift ([DP-3](../../record/principles.d/DP-003.md)).

## 7. Tighten only when the corpus is ready

A typical progression is:

```text
visible finding
    ↓
known backlog
    ↓
baseline or acknowledgements
    ↓
repair the corpus
    ↓
promote the class when zero/new-regression is meaningful
```

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
