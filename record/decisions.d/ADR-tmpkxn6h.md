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

# Active | Proposed | Deferred | Superseded | Rejected. Supersede when the
# CHOICE changes: set the old one to `status: Superseded`, name the successor
# in `superseded_by: ADR-tmpkxn6h` (a reference field: checked, resolved, an edge
# the index and the site render), and leave its body intact. A qualifying
# note for anything the field cannot say goes in `status_note:` — prose,
# like `summary:`, so a code in it is a citation. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Active'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpkxn6h:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'A scheme can require one of several fields'

# Which revision of this decision's claim you are reading. Standard frontmatter
# for every scheme, and it moves rarely here: a decision that CHANGES is
# superseded by a new one, not edited. Bump it when the same choice is restated
# more broadly — scope widened, wording generalized — and say what changed in a
# `history:` entry. Shown in the index only when it is not 1.
version: 1

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
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
  `requires = ["arxiv"]` on a paper demanded the wrong thing: a report
  never posted to arXiv but carrying a DOI, or only a URL, has a source
  all the same. A field group names the need and the fields that satisfy
  it — `[field_groups.source]` over `arxiv`, `doi`, `url`, `require =
  "at-least-one"` — and the lint asks for one, naming all of them when
  none is there. Opt-in per scheme, shaped after tag groups ([ADR-054](ADR-054.md)).
  Rejected: keeping `arxiv` required; a list-valued entry inside
  `requires`; and typing each field as a source, which is the
  field-typing decision and not this one.

---

# ADR-tmpkxn6h: A scheme can require one of several fields

## Context

`requires` demands every field it names ([ADR-040](ADR-040.md)). The
knowledge-base example used it for a paper's provenance —
`requires = ["arxiv"]` — and review of [#144](https://github.com/dmarx/luria/issues/144) named what that gets wrong: a
paper is not its arXiv identifier. A journal article has a DOI and may
never have been posted to arXiv; a lab's technical report may have
neither and still be the paper a practice rests on. What the record
actually requires of a paper is *a source*, and several different fields
are one.

`requires` has no way to say that. A field group for tags exists
([ADR-054](ADR-054.md)) because a tag vocabulary is sometimes an axis; a
requirement is sometimes a disjunction for the same reason, and nothing
could say so.

## Decision

**A scheme may group fields under a name and require some of them.**

```toml
[luria.schemes.LIT.field_groups.source]
fields  = ["arxiv", "doi", "url"]
require = "at-least-one"          # or "exactly-one", "at-most-one"
```

The group is named for the need — *a source* — and lists the fields that
satisfy it. `at-least-one` is the default and the motivating case; the
other two rules exist for the same reason they do on a tag group, and
cost nothing beside it. An empty value does not count as present.

The finding names the need and every field that would have met it:
*no `source` — one of `arxiv:`, `doi:`, `url:` — the LIT scheme requires
it (luria.toml: schemes.LIT.field_groups.source)*. The record page lists
the group under *what an entry must carry* with the same words. Validated
at load like a tag group: a group naming no fields, or a rule that is not
one, is a configuration error rather than a group that constrains nothing.

The example now has a third paper, a technical report with only a
`url:`, which the old requirement would have refused.

## Alternatives considered

- **Keep `arxiv` required.** Simplest, and wrong about papers; the example
  was teaching a rule the anthology it models would break on the first
  journal article.
- **A list inside `requires`** — `requires = ["published", ["arxiv",
  "doi", "url"]]`. No new table, and no name: the finding could say only
  "one of arxiv, doi, url", not what the three have in common, and the
  record page could not describe the need. A mixed-type array is also the
  kind of shorthand [ADR-063](ADR-063.md) declines to store.
- **Type each field as a source and require one of that type.** The
  reviewer's phrasing, and the more principled shape: `arxiv`, `doi` and
  `url` each declare what they are, and the scheme requires a field of
  that kind. It needs the field-typing work that [#141](https://github.com/dmarx/luria/issues/141)'s later phases
  describe — a `fields` table with a type per field — and that decision
  has not been made. The group states the same need in the tables that
  exist, and reads naturally as one of those types once they do.
- **Status quo.** A rule that fails the first real journal article.

## Consequences

`requires` keeps its meaning — every field named — and the group is the
word for *any of these*. A scheme declaring neither is unchanged.

The group is a need with a name, which is what a type would be. When
fields carry types, `require one field of type source` and this group say
the same thing, and the group can become sugar for it rather than a
second mechanism.
