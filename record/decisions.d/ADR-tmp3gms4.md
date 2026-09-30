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
title: 'A citation can name the relation it stands in, and a relation can require prose'

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
  A citation may name the relation it stands in, as `[[extends::X]]` or a
  link titled with the field name, `[X](X.md "extends")`. The name is a
  reference field of the citing document, declared or built in, so a
  relation read the other way is named by its converse. A named relation
  missing from frontmatter is `unrecorded-relations`, and `luria link --fix`
  writes it. A reference declared `explain: true` wants each code it holds
  cited in the body with the relation named: a plain citation is
  `unannotated-relations` and the fixer names it, and an uncited code is
  `unexplained-relations`, a report acknowledged with `unexplained-ok:`. A
  named relation the record cannot hold is `bad-annotations`. Rejected: an
  arrow notation after the link, requiring prose for every relation, and
  writing citations into prose.
---

# ADR-tmp3gms4: A citation can name the relation it stands in, and a relation can require prose

## Context

A reference field says *that* two documents are related. The body is where
a reader learns *why*, and nothing connected the two ([#333](https://github.com/dmarx/luria/issues/333)). A citation in
prose was always a mention, even when the sentence around it said "this
builds on that", and a relation in frontmatter could stand with nothing in
the body explaining it. The issue asked for both directions: state a
relation inline and have it pushed up into frontmatter, and have a declared
relation pushed down into prose. It proposed an arrow notation after the
link, `[[X]]{--F-->here}`, and left the notation open.

## Decision

A citation names its relation with the field that holds it in *this*
document's frontmatter:

- `[[extends::X]]` or `[[extends::X|label]]` as a wikilink. `F::` ahead of
  the target is Semantic MediaWiki's spelling of a typed link.
- `[label](X.md "extends")` as a markdown link. This is what the link fixer
  expands the wikilink into, and it can be written by hand. The title counts
  as a relation only when it is shaped like a field name. A title with a
  space or a capital is an ordinary tooltip.

Any reference field is a relation here, the declared ones and the built-in
successor alike. Nothing in the mechanism knows one relation's name.

- **Push up** is mechanical. A named relation missing from frontmatter is
  `unrecorded-relations`, and `luria link --fix` writes it into the citing
  document. The converse completion ([ADR-084](ADR-084.md)) writes the far side in the same
  run.
- **Push down** is opt-in per reference (`explain: true`) and splits in two.
  A code the field holds that the body cites plainly is
  `unannotated-relations`, and the fixer names the relation on the first
  such citation. A bare code becomes a typed wikilink, which the same run
  links. A code the body never cites is `unexplained-relations`. That one is
  a report, acknowledged per code with `unexplained-ok:`, because the prose
  that explains a relation is a person's to write.
- A named relation the record cannot hold as written is `bad-annotations`:
  a relation the scheme does not declare, a code in a scheme the field does
  not hold, a code naming no document here, or a single-valued field that
  already holds another code. None of these has a right answer the machine
  can pick.

All four are ordinary warning classes, so `fail_on` and `mute` reach them.

## Consequences

- The relation renders as a link title: invisible in the running text,
  shown on hover, and understood by every markdown renderer. The link
  patterns that assumed a link has no title are widened, including the
  target checker, which used to skip a titled link without saying so.
- A relation whose field lives only on the *cited* document, with no
  converse declared, cannot be named from this side. That is deliberate.
  To state it from here, declare the converse. An undeclared converse is a
  reverse edge the record has chosen not to know ([ADR-084](ADR-084.md)).
- The issue's last example shows the fixer writing a whole citation into a
  body that had none. That was not done. Which sentence the citation
  belongs in is the non-deterministic part the same issue says must be a
  report, so the fixer only names relations on citations that exist.
- One citation names one relation. When two explained relations hold the
  same code, the fixer names one and reports the other until the author
  cites the code a second time.

## Rejected

- **The arrow notation, `[[X]]{--F-->here}` / `[[X]]{here--F-->}`.** It was
  built first and replaced before review. It needs a direction the author
  has to get right, and a relation already carries its direction in its
  name (`extends` vs `extended_by`). It also rendered as literal braces in
  every view, and it put the relation in a slot that no markdown renderer
  knows.
- **Making every declared reference owe prose.** Every existing record
  would get one finding per edge on upgrade, and most relations need no
  explanation beyond their name.
- **Naming the field on the cited side.** That would edit a file the author
  was not working in. The field on this side is the one the prose is
  about.
