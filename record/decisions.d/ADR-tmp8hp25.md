---
status: Proposed
title: "One config file, one format, vocabularies declared once"
version: 1
tags:
- mechanism
- record
date: '2026-09-13'
issue: '#256'
summary: >-
  Config was TOML, vocabularies were YAML files beside each scheme's records,
  and the lockfile was JSON — three formats for one system, with no reason any
  of them could state. Worse, a vocabulary two schemes share had to be two
  files: in the corpus that motivated this, ten of thirteen entries had
  silently drifted. Moves to one `luria.yaml` with a central `vocabularies:`
  table, omegaconf underneath the existing validation rather than in place of
  it. Rejects keeping vocabularies local, and rejects letting structured
  configs replace the semantic checks.
---

# ADR-tmp8hp25: One config file, one format, vocabularies declared once

## Context

Three formats for one system:

    luria.toml            TOML   the config
    tags.yaml             YAML   per scheme, beside the records
    statuses.yaml         YAML   per scheme, beside the records
    <vocabulary>.yaml     YAML   per scheme, declared by name ([ADR-076](ADR-076.md))
    remotes.lock.json     JSON   generated, committed

Every document's frontmatter is already YAML. The config was TOML for no
reason either format could state, which is one more set of quoting rules to
know and one more parser to reason about when a regex in a `uid` does not mean
what it looks like.

**The vocabulary split was worse than untidy.** A scheme could only name a
file beside its own records, so a vocabulary two schemes share had to be two
files. Measured across the two records running on luria at the time of
writing:

- **Four byte-identical copies** of one `statuses.yaml` — `ADR` and `DP` in
  this repository, and the same pair again in `anthology-of-the-sota`.
- That record's [ADR-026](ADR-026.md) **decided** its practice registry and reading list
  share one topic vocabulary, and says so in its CLAUDE.md. On disk it was two
  files with the same thirteen keys and **ten of thirteen blurbs different**.
  Two edits to one vocabulary, months apart, that nothing could reconcile
  because nothing knew they were the same vocabulary.

This project already knew. `primary_tags`' own docstring records the identical
failure from the other direction: *"seven terms across four places, and the
blurbs for the same tag already disagreed between two of them ([ADR-060](ADR-060.md))"*.
[ADR-060](ADR-060.md) fixed the copies *within* a scheme. The copies *between* schemes were
unreachable, because the config had no way to say "these are the same words".

## Decision

**One `luria.yaml`.** TOML is gone rather than deprecated — see the
alternatives.

**A central `vocabularies:` table**, referenced by name:

    vocabularies:
      statuses:
        Active: {label: Current, blurb: in force}

    schemes:
      ADR:
        statuses: statuses
      DP:
        statuses: statuses          # the same words, said once

A vocabulary's per-value pages render at `<view>/<name>/`, so its **name is
part of a published path**. Luria's own shared vocabulary is called
`statuses` rather than something more descriptive for exactly that reason:
renaming it would move `docs/decisions/statuses/` and leave the old
directory behind as an orphan no generator claims.

`Scheme.tags_yaml` and `Scheme.statuses_yaml` — paths — become `Scheme.tags`
and `Scheme.statuses`, which return values. `Vocabulary.file` becomes
`Vocabulary.values_by_name`. Nothing downstream opens a vocabulary file
because there is no longer one to open.

**omegaconf goes underneath the validation, not in place of it.**
`OmegaConf.merge` replaces the hand-rolled `_merge` over `DEFAULTS`, and the
schema types the result. The 44 `raise ValueError`s stay, and should: they are
cross-field semantic rules — a converse must be mutual and point back at the
declaring scheme, a derivation's `from` must name a real reference,
`cite = "view"` needs `render = "document"` — and a structured config
validates the shape of a value, not a relationship between two.

**`label` has one fallback.** It had three — `tag.title()` in the tag pages,
`""` in the status legend, the raw value in the vocabulary pages — so a scheme
declaring no `label` rendered a title-cased tag heading and an empty legend
cell. `vocabularies.label_of` is the one answer.

**`Reference` gains `label` and `blurb`** ([#254](https://github.com/dmarx/luria/issues/254)), the two keys a vocabulary
value already carried. A relation's meaning lived in a TOML comment, which
nothing could render, quote in a finding, or scaffold from — which is how a
record ended up with fourteen practices citing adoption as evidence while
every mechanical check stayed green.

**A vocabulary-backed field's pages render under the FIELD's name**, not the
vocabulary's. That was the last thing to go wrong here and the least obvious:
pages rendered at `<view>/<vocabulary>/`, so sharing a vocabulary between two
schemes — the entire point of this decision — moved published pages and left
the old directory behind as an orphan. What that broke said nothing about
paths: the bare-reference check skips generated views and recognises them *by
generated-output path*, so an orphan is not one, and pages generated for a
year started being scanned as hand-written prose.

A vocabulary's name is a config detail; a published path is not. Keyed on the
field, no config change can ever move a page. **This moves existing pages
once** — `<view>/statuses/` becomes `<view>/status/` — which is the right
place to spend it: at a format boundary a record crosses deliberately, rather
than in a later release where it would surprise someone.

## Alternatives considered

- **Keep vocabularies beside the records.** The locality argument: a scheme's
  vocabulary is the one piece of config a person editing that directory
  actually reads. It was mine, it was speculation about a user, and the user
  reported the opposite — the files were hard to *locate*. The drift evidence
  above settles the rest.
- **Central by default, with a per-scheme path override.** The compromise, and
  close to what `tags_file` already was. Rejected because the override is the
  thing that permits the drift: two schemes *can* point at one file today and
  simply do not. A mechanism nobody reaches for is not a mechanism.
- **Deprecate TOML over a release or two, dual-reading both.** The careful
  path, and normally right. Rejected on instruction — and the cost is real and
  bounded: two known records, both converted in this change.
- **Let structured configs replace the hand-written validation.** Tempting,
  since it looks like the point of adopting them. It would trade luria's
  errors — *"a converse names the field holding the same relation read
  backwards, and it has to exist to be written into (declared: …)"* — for a
  schema complaint about a key of the wrong type, at exactly the moment a user
  is confused. The plumbing was worth replacing; the checks are the part that
  earns its keep.
- **Key the view path on the vocabulary's name, and have the converter keep
  the old stem.** It would move nothing in the common case. It fails exactly
  where this decision is aimed: a record whose five schemes each have a
  `statuses.yaml` with *different* words cannot keep all five on the name
  `statuses`, so four move anyway — and the rule "your pages move unless your
  vocabularies happen not to collide" is not one anybody can hold.

- **JSON for the lockfile stays.** It is generated, not authored, and machine
  round-tripping is the only thing it is for. Unifying it would be consistency
  for its own sake.

## Consequences

`luria lint` runs end to end on this repository under the new config, and
`ADR` and `DP` now share one status vocabulary declared once — the duplication
that motivated this is gone from the record making the decision.

**This is a breaking change with no migration path in-tree.** Every existing
record has a `luria.toml` and per-scheme vocabulary files. A converter is
owed, and the hazard it has to own is escaping: `uid = "(\\d{4})[.:](\\d{4,5})"`
does not survive TOML → YAML by copying bytes, and that is the kind of thing
that converts silently and breaks at runtime. Round-tripping every `uid` and
`title_re` in a real record is the test, not a fixture.

`primary_for` remains the right mechanism and gets better: it was a way for
one file to say which schemes a tag is primary for, and it now says that
inside the vocabulary every one of those schemes actually shares.
