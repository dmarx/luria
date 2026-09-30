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
title: 'A relation is stated in prose as a directive named by its field'

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
  A relation is stated in a document's body with the comment-directive
  grammar every acknowledgement uses, named by the reference field that
  holds it (`<!-- extends: LIT-007 -->`), so it inherits line, block and file
  scope, a reason and an expiry. `[[extends::X]]` is shorthand the link
  fixer expands into a link plus that statement. A statement missing from
  frontmatter is `unrecorded-relations`, and `luria link --fix` writes it. A
  reference declared `explain: true` wants each code it holds explained in
  the body, by a citation in a statement's scope or by the statement's
  reason: a bare citation is `unannotated-relations` and the fixer writes
  the statement, and a code with neither is `unexplained-relations`, a
  report. A statement the record cannot hold is `bad-annotations`. Rejected:
  an arrow after the link, the relation as a link title, a separate
  acknowledgement for unexplained relations, and requiring prose for every
  relation.
---

# ADR-tmp3gms4: A relation is stated in prose as a directive named by its field

## Context

A reference field says *that* two documents are related. The body is where
a reader learns *why*, and nothing connected the two ([#333](https://github.com/dmarx/luria/issues/333)). A citation in
prose was always a mention, even when the sentence around it said "this
builds on that", and a relation in frontmatter could stand with nothing in
the body explaining it. The issue asked for both directions: state a
relation inline and have it pushed up into frontmatter, and have a declared
relation pushed down into prose. It proposed an arrow after the link,
`[[X]]{--F-->here}`, and left the notation open.

Luria already has one grammar for an author saying something to the tooling
from inside prose: the comment directive ([ADR-006](ADR-006.md), [ADR-035](ADR-035.md)), with its
scopes, its `— reason` and its expiry ([ADR-095](ADR-095.md)). An acknowledgement is a
claim about a citation ("this retired document is cited on purpose, because
…"). A relation stated in prose is the same kind of thing ("this citation is
the `extends` relation, because …"), so it gets the same grammar rather than
a second one.

## Decision

A relation is a directive named by the reference field that holds it in
*this* document's frontmatter:

    The recovery path is LIT-007's, generalised. <!-- extends: LIT-007 -->
    <!-- extended_by-block: LIT-012, LIT-015 — both carry the retry loop on -->

Any reference field works, whether declared in `references:` or the built-in
successor. Nothing in the mechanism knows one relation's name. Direction is
the field's name, so the other direction is written with the converse. The
directive grammar's name pattern now admits `_`, because field names use
it. A reference field may not take a name the directive vocabulary already
spends (an `-ok` acknowledgement, a `-block`/`-file` scope suffix,
`unlinted`, `unexempt`, `pin`), and `luria.yaml` refuses one that does.

`[[extends::X]]` (Semantic MediaWiki's typed-link spelling) is shorthand for
a citation plus its statement. The link fixer expands it to
`[X](X.md)<!-- extends: X -->`. A shorthand naming a field the document
cannot hold is not expanded: it would become a comment nothing reads. The
wikilink lint fails on it instead.

- **Push up** is mechanical. A statement missing from frontmatter is
  `unrecorded-relations`, and `luria link --fix` writes it. The converse
  completion ([ADR-084](ADR-084.md)) writes the far side in the same run.
- **Push down** is opt-in per reference (`explain: true`). A code the field
  holds is explained when a statement of it governs a citation of the code,
  or when the statement has a `— reason`. A citation with no statement is
  `unannotated-relations`, and the fixer writes `<!-- F: X -->` after the
  first citation. A code with neither is `unexplained-relations`, a report,
  because the explanation is prose only a person can write.
- A statement the record cannot hold as written is `bad-annotations`: an
  argument that is not a code, a code naming no document here, a code in a
  scheme the field does not hold, a document naming itself, or a
  single-valued field that already holds another code.

All four are ordinary warning classes, so `fail_on` and `mute` reach them.

## Consequences

- A statement is invisible in every rendered view, like every other
  directive. The prose around the citation is what a reader sees, and the
  statement is what the tooling reads.
- The acknowledgement and the statement are one directive. A statement's
  reason is its explanation, so `<!-- cites-file: LIT-001 — the method
  section is its -->` both states the relation and says it needs no more
  prose. No separate "unexplained-ok" is needed.
- A citation can carry any number of statements, so two explained relations
  holding one code no longer compete for a single citation.
- A misspelt field in a hand-written statement (`<!-- extnds: X -->`) is
  read as no directive at all, the same as a misspelt acknowledgement is
  today. The shorthand is checked; the long form is exactly as checked as
  the rest of the vocabulary.
- The issue's last example has the fixer writing a whole citation into a
  body that had none. That was not done. Which sentence the citation
  belongs in is the non-deterministic part the same issue says must be a
  report.

## Rejected

- **The arrow notation, `[[X]]{--F-->here}` / `[[X]]{here--F-->}`.** It
  needs a direction the author has to get right, when a relation already
  carries its direction in its name. It also rendered as literal braces in
  every view.
- **The relation as a link title, `[X](X.md "extends")`.** This was the
  second draft. It rendered well, but it was a second annotation grammar
  beside the directive one: no scope, no reason, no expiry. It also gave a
  meaning to a slot that markdown authors use for tooltips.
- **A separate acknowledgement for an unexplained relation.** The
  statement's own reason says the same thing in the same place.
- **Making every declared reference owe prose.** Every existing record
  would get one finding per edge on upgrade.
