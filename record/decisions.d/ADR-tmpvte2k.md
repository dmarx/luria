---
# Don't copy this file by hand — run `luria new adr`, which assigns the
# identity and fills in the fields a machine can compute. WHICH identity
# depends on the scheme's `allocate` mode: `filing` (the default) takes the
# next free number on the spot, `merge` mints a temporary code that
# `luria concretize` numbers where merges serialize (ADR-049). The kinds are the
# config: every scheme, fragment directory and journal in luria.toml is one, so
# `luria new <kind>` works for a scheme the moment it is declared.
#
# Numbering is sequential and carries information (it's the order decisions were
# made). The filename is the code and nothing else; the title goes in `title:`
# below, where correcting it costs an edit rather than a rename plus every link
# (ADR-013).
#
# This frontmatter is the ONLY place these facts live. The index and the per-tag
# pages are generated from it (ADR-004) — never edit them by hand; run
# `luria index`.

# Active | Proposed | Deferred | Superseded | Rejected. A qualifying note goes
# in `status_note:` below it — prose, like `summary:`, so a code in it is a
# citation and the fixer links it. Supersede when the CHOICE changes: set the
# old one to `status: Superseded` with `status_note: by ADR-tmpvte2k` and leave
# its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Active'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpvte2k:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'The status note is its own field'

# Which revision of this decision's claim you are reading. Standard frontmatter
# for every scheme, and it moves rarely here: a decision that CHANGES is
# superseded by a new one, not edited. Bump it when the same choice is restated
# more broadly — scope widened, wording generalized — and say what changed in a
# `history:` entry. Shown in the index only when it is not 1.
version: 1

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
- record
- mechanism

date: '2026-09-03'

# Optional. The issue(s) this decision came from: '#123'.
issue: '#141'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
summary: >-
  `status: Superseded — by FX-ADR-032` was one scalar carrying two types: a
  word from a closed vocabulary, and a prose note that was rendered,
  rebased for links, and split off the word in six places. The note is now
  its own field, `status_note:`, and a prose key like `summary:` — a code
  in it is a citation the fixer links. The successor a superseded
  document names is a reference field, `superseded_by:` (ADR-tmpxmnac);
  the note is for what the field cannot say. A note still riding in
  `status:` is a lint finding that `luria index` repairs, the way it fills
  `created:` from a path ([ADR-031](ADR-031.md)). Amends [ADR-003](ADR-003.md), which placed the note
  after an em-dash. Rejected: leaving the scalar and parsing it forever,
  which keeps the field's type a lie; and scanning `status:` as prose
  without splitting it.

---

# ADR-tmpvte2k: The status note is its own field

## Context

[ADR-003](ADR-003.md) closed the status vocabulary to five words and
allowed each "an optional em-dash note". The note was useful from the
first day — every superseded decision in this record names its successor
in one — and it was never the same kind of thing as the word beside it.

The word is data: checked against the closed set, narrowed per scheme by
`statuses.yaml` ([ADR-056](ADR-056.md)), the pivot of every report. The
note is prose: rendered in the index column and rebased there for links,
rendered on the site's record line, hand-linked in this record
(`by [ADR-035](ADR-035.md)`) so the link survives, and free to cite
whatever the author meant. [ADR-051](ADR-051.md)'s rule for which
frontmatter keys are prose is *the ones the generator renders*, and the
note qualified on that rule from the moment the index rendered it. It was
kept out of the prose keys only because it shared a scalar with a value
that had to stay data.

The cost was paid in code. Six places split the word off the note with
three spellings of one regex — the status report, the pending report,
three in the vocabulary module, and the first draft of the typed edges
([ADR-tmpxmnac](ADR-tmpxmnac.md)). Every one of them was a place the
field's two types were being taken apart by hand because the file had
put them together. And a code in the note cited nothing: `Deferred —
parked by WDR-015` in a downstream record named a document the scanner
never saw, because the scanner reads prose keys and this was not one.

## Decision

**The note is its own field.**

```yaml
status: Superseded
superseded_by: FX-ADR-032
status_note: the capital never burned after all
```

`status:` is one word from the closed vocabulary and nothing else.
`superseded_by:` is the successor, a reference field every scheme has
([ADR-tmpxmnac](ADR-tmpxmnac.md)): structure, checked and resolved.
`status_note:` is prose — a prose key beside `summary:` and `origin:`
([ADR-051](ADR-051.md)): scanned for bare references, linked by
`luria link --fix`, checked by the lint, and a citation wherever citations
count. The display form, `Superseded — by …`, is composed from the two
wherever a reader sees a status; nothing changes on a page.

**The combined form is read, reported, and repaired.** A file still
carrying `status: 'Superseded — by X'` parses as before, so nothing
breaks between the field arriving and the file being moved. The lint
reports it — *`status:` carries a note — `luria repair` moves it to
`status_note:`* — and `luria repair` moves it, the way it fills `created:`
from a journal entry's path ([ADR-031](ADR-031.md)): the file already
states both facts, in one scalar, and the tree is made to say so in two.
One function writes the field, and the migration's tombstone goes through
it.

**This amends [ADR-003](ADR-003.md)**, whose choice — a closed vocabulary
in frontmatter, enforced by lint — stands whole. What moves is where the
qualifier lives; that decision carries a `history:` entry saying so.

## Alternatives considered

- **Keep the scalar; parse it everywhere.** What the first cut of the
  typed-edges work did: one `Status(value, note)` parse replacing the six
  splits, storage untouched. It removes the duplication and keeps the lie:
  a field declared as a value from a closed vocabulary that also holds
  prose is not that type, and every new consumer has to learn the parse.
  The parse survives as the reader of the old form; it stops being the
  reader of the canonical one.
- **The successor in the note, the field left out.** What this decision
  first proposed, with the typed-edges work inferring the successor from
  a `by CODE` note. Reversed on review and decided in [ADR-tmpxmnac](ADR-tmpxmnac.md): the
  successor is a relation, and a relation is written as structure — a
  field the tool checks — not as a sentence the tool recognises. The note
  is prose for what the field cannot say.
- **Scan `status:` as prose without splitting it.** [ADR-051](ADR-051.md)
  rejected scanning fields that are parsed by value, and the rejection
  holds: a rewrite that links a code inside `status:` can break the value
  the lint reads. Splitting is what makes the prose safe to touch.
- **Leave the old form forever, unreported.** Two spellings of one thing,
  with the lint indifferent between them — the drift
  [DP-3](../../docs/design-principles.md#dp-3) names, invited in writing.
  The report costs a line; the repair is automatic.

## Consequences

Four decisions in this record and two documents in an example moved on
the first `luria index`. Downstream records move the same way, and the
finding tells them so; the old form keeps reading until they do.

A code in a status note is now a citation: `Deferred — parked by WDR-015`
links, counts, and reports when WDR-015 retires — through the ordinary
scanner, with no relation invented for it. The successor is not a
citation but a field, and the repair drops the note that used to carry it
when the note said only the code.

The ADR template, the scaffold's, the principle templates and the docs
say the three-field form. `luria migrate --strategy supersede` writes the
field. The lint's status pattern is five bare words again.
