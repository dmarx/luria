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
# in `superseded_by: ADR-tmp3gms4` (a reference field: checked, resolved, an edge
# the index and the site render), and leave its body intact. A qualifying
# note for anything the field cannot say goes in `status_note:` — prose,
# like `summary:`, so a code in it is a citation. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Proposed'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmp3gms4:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'A citation can state the relation it stands in, and a relation can require prose'

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
- load-bearing
- docs

date: '2026-09-29'

# Optional. The issue(s) this decision came from: '#123'.
issue: '#333'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
summary: >-
  A citation may carry an annotation naming the relation it stands in,
  `[[X]]{--F-->here}` or `[[X]]{here--F-->}`. An annotated edge missing from
  frontmatter is `unrecorded-relations`, and `luria link --fix` writes it,
  as this document's converse when one is declared. A reference declared
  `explain: true` wants each code it holds cited in the body: a plain
  citation is `unannotated-relations` and the fixer annotates it, and an
  uncited code is `unexplained-relations`, a report acknowledged with
  `unexplained-ok:`. An annotation the record cannot hold is
  `bad-annotations`. Rejected: requiring prose for every relation, always
  writing into the cited document, and an annotation without a direction.
---

# ADR-tmp3gms4: A citation can state the relation it stands in, and a relation can require prose

## Context

A reference field says *that* two documents are related. The body is where
a reader learns *why*, and nothing connected the two ([#333](https://github.com/dmarx/luria/issues/333)). A citation in
prose was always a mention, even when the sentence around it said "this
builds on that", and a relation in frontmatter could stand with nothing in
the body explaining it. The issue asked for both directions: state a
relation inline and have it pushed up into frontmatter, and have a declared
relation pushed down into prose.

## Decision

A citation may carry an annotation naming the relation it stands in:
`[[X]]{--F-->here}` (X stands in `F` to this document) or
`[[X]]{here--F-->}` (this document stands in `F` to X). `F` is a declared
reference field on the scheme at the arrow's tail. The annotation attaches
to a wikilink, a markdown link or a bare code, so the link fixer rewriting
the first into the second leaves it in place.

- **Push up** is mechanical. An annotated edge missing from frontmatter is
  `unrecorded-relations`, and `luria link --fix` writes it. For
  `{--F-->here}` with a declared converse, the fact is written *here*, as
  the converse, so the document whose prose asserted it is the one that
  changes. The converse completion ([ADR-084](ADR-084.md)) writes the far side in the same
  run. Without a converse there is no field here to hold it, so it goes
  into the cited document's `F`.
- **Push down** is opt-in per reference (`explain: true`) and splits in two.
  A code the field holds that the body cites plainly is
  `unannotated-relations`, and the fixer annotates the first such citation.
  A code the body never cites is `unexplained-relations`. That one is a
  report, acknowledged per code with `unexplained-ok:`, because the prose
  that explains a relation is a person's to write.
- An annotation the record cannot hold as written is `bad-annotations`: it
  follows no citation, names an undeclared relation, points into a scheme
  the relation does not hold, names no local document, or contradicts a
  single-valued field that already holds another code. None of these has a
  right answer the machine can pick.

All four are ordinary warning classes, so `fail_on` and `mute` reach them.

## Consequences

- An annotation renders literally in every view that shows the body
  (`{--extends-->here}` after the link). That is legible, but it is noise
  in a published page. Stripping or styling it in views is left for when
  someone uses annotations enough to mind.
- The issue's last example shows the fixer writing a whole citation into a
  body that had none. That was deliberately not done. Which sentence the
  citation belongs in is the non-deterministic part the same issue says
  must be a report, so the fixer only annotates citations that already
  exist.
- One citation carries one annotation. When two explained relations hold
  the same code, the fixer annotates one citation and reports the other
  relation until the author cites it a second time.

## Rejected

- **Making every declared reference owe prose.** Every existing record
  would get one finding per edge on upgrade, and most relations need no
  explanation beyond their name.
- **Always writing push-up into the tail document.** For `{--F-->here}`
  that edits a file the author was not working in, while the converse
  exists so the fact can be held on either side. The tail is used only
  when there is no converse.
- **Annotating by field name alone (`[[X]]{extends}`).** That form cannot
  say which way the edge runs, and the direction is the one thing the
  field name does not carry.
