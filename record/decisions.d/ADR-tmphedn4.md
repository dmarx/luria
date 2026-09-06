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
# in `superseded_by: ADR-tmphedn4` (a reference field: checked, resolved, an edge
# the index and the site render), and leave its body intact. A qualifying
# note for anything the field cannot say goes in `status_note:` — prose,
# like `summary:`, so a code in it is a citation. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: Proposed

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmphedn4:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'A relation declares its converse; symmetry is the self-converse case'

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

date: '2026-09-06'

# Optional. The issue(s) this decision came from: '#123'.
issue: '#000'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
summary: >-
  One-paragraph description of the decision, the cost that motivated it, and the
  alternatives that lost. Written to be read in a table row.
---

# ADR-tmphedn4: A relation declares its converse; symmetry is the self-converse case

## Context

`[luria.chains]` shipped a check for a symmetric relation held by one side,
and [#178](https://github.com/dmarx/luria/issues/178) turned that check into a fixer: `luria link --fix` writes the
missing back-reference. The mechanism was scoped to a chain's `sibling`
field, and it refused to touch the `relation` field on this reasoning:

> `relation` is directed — A extends B does not make B extend A — and
> mirroring it would manufacture the cycle the lint reports.

The first half is true. The conclusion does not follow from it.

Review caught the gap. What is never valid is mirroring a relation into
*its own* field: writing `extends: A` onto the document A extends asserts
that B extends A, which is false, and surfaces as a 2-cycle. That is a
constraint on **the field written into**, not on the relation's direction.
A directed relation completes perfectly well — into its converse, where the
fact is true. If A `extends` B then B is `extended_by` A, and nothing about
that is a guess.

And once the converse is the unit, symmetry stops being a separate kind of
thing. `compared_against` is the relation whose converse is itself. The
mechanism shipped in [#178](https://github.com/dmarx/luria/issues/178) was the self-converse special case, presented as
the general rule.

## Decision

A reference field may declare its `converse`: the field holding the same
relation read backwards.

    [luria.schemes.LIT.references]
    extends          = { scheme = "LIT", many = true, converse = "extended_by" }
    extended_by      = { scheme = "LIT", many = true, converse = "extends" }
    compared_against = { scheme = "LIT", many = true, converse = "compared_against" }

Four rules follow.

**The declaration licenses the write.** A relation with no declared converse
is left entirely alone — nothing completed, nothing reported. Its reverse
edge would be a guess, and a guess in the record is worse than an absence,
because an absence at least looks like one ([DP-15](../../docs/design-principles.md#dp-15)).

**A pair is mutual, same-scheme, and plural on both sides.** The converse of
the converse is the relation, so half a declaration is refused rather than
completing in one direction only. Either side is written into, and several
documents can stand in one relation to the same one, so both need
`many = true`.

**Symmetry is self-converse.** One rule covers both cases, and
`chains.sibling` keeps only its rendering job — which relation draws
"alongside" rather than nesting. What is symmetric is a property of the
relation, so it is declared on the relation.

**A contradiction is not a completion.** A document naming another in both
directions of one pair, or two documents each claiming to come first, has
nothing missing: two incompatible things are present. Reported, never
written.

The check moves out of `broken-chains` into its own class,
`one-sided-relations`, and out of `chains.py` into `relations.py`. A
declared pair is one-sided or it is not, whether or not any chain walks it —
so neither the check nor the fixer belongs to a view. `broken-chains` keeps
the cycle, which is genuinely about a sequence and is the one finding no
fixer can repair.

Chains read both relations through `relations.edges()`, which unions a
relation with its declared converse. A one-sided declaration therefore
renders correctly before anyone runs the fixer; completion makes the
documents agree on disk afterwards.

## Which side changed, not which side is empty

The first implementation of this was monotonic, and that made it hostile:
delete `extends: LIT-001` from the document that declared it, run
`luria link --fix`, and it came back. The record fought the author, silently.

The cause is that a one-sided pair has two opposite readings — a write the
other side has not caught up with, or a deletion the other side is stale
about — and **the working tree holds neither**. Which side *changed* does,
and that lives in the last committed state. This record is in git, the
workflow is branch-then-pull-request, and `luria` already shells to git in
five modules, so HEAD is available and is the right baseline: it is the last
state the record was consistent in.

So the rule is about change, not about state:

| since HEAD | the fixer |
|---|---|
| a side gained the relation | writes it to the other side |
| a side lost it | removes it from the other side |
| one gained while the other lost | reports; touches nothing |
| nothing changed | writes the missing side |

The last row is the migration path — a corpus predating the fixer is
one-sided at HEAD too — and it is the one reading that can be wrong: a
deletion committed *before* the fixer ran looks like nothing changed, and
gets written back. It is self-correcting rather than sticky, because
deleting it a second time is a change and prunes both sides. Stated here
because it is the sharp edge, not because it is acceptable in silence.

No repository, or no commit yet, means no baseline, and everything reads as
added. That is right for a document git has never seen and keeps the fixer
working outside a repository rather than refusing to.

### Alternatives for this half

**A separate `--prune` flag.** Rejected: the failure it guards against is
silent re-addition, so it is the flag you only learn to pass after it has
already bitten you — the same argument that made completion the default
rather than an opt-in.

**Make one side authoritative and the other derived.** Rejected: it gives up
the symmetric case, where there is no canonical side, and it gives up
declaring the relation from whichever document you happen to be holding —
which is most of the value.

**Report a one-sided pair and never write it.** Rejected: honest, but it
gives up the whole mechanism to avoid one ambiguous case, and leaves every
pre-existing one-sided pair permanently on the report.

## A repair never breaks the document it lands in

The fixer writes and deletes frontmatter, and frontmatter is what the
contract judges. So a repair can move a document from satisfying its scheme
to violating it, in either direction — and both are reachable with legal
configuration:

- a back-reference **added** into a field group that permits only one of two
  fields;
- a stale back-reference **removed** out of a field the document's status
  requires (`required_when`).

Neither is the author's mistake, and a fixer that manufactures a lint
failure and exits zero is the silent failure this whole decision is about.

**A repair that would introduce a new violation is not applied.** The pair
stays one-sided, and the finding names both rules, because a relation that
must be written and a contract that forbids writing it is a genuine conflict
between two things the project declared — not something a tool should
resolve by picking one.

The property this buys is worth stating plainly: **running `luria link
--fix` never makes `luria lint` worse.**

Only *new* violations block. A document already in breach somewhere else
still gets its back-references; otherwise one unrelated mistake would freeze
every relation that document stands in.

The check is written against the compiled `Contract` rather than against any
particular rule, so it covers `requires`, `field_groups` and `required_when`
alike, including rules added later.

## Consequences

A project that declares a converse opts into stored redundancy, and should
know it. With a symmetric relation there is no canonical home for the fact —
either document is an equally natural place to state it — so writing both
sides is the only way to hold it in per-document frontmatter. With a
directed pair there *is* a canonical side, and the converse is derivable, so
storing it buys one thing: the fact is legible when reading that document
alone. This record has taken the other option before and should keep taking
it where it fits — `superseded_by` is stored with no `supersedes`, and the
site derives the reverse.

The migration is opt-in and silent in the wrong direction: a project that
had a symmetric field completing under [#178](https://github.com/dmarx/luria/issues/178) stops completing until it adds
`converse` to the declaration. That is the cost of making the declaration
the licence, and it is the right cost — but it is a change in behaviour with
no error attached, so it is called out here and in the changelog rather than
discovered.

## Alternatives

**Delete the symmetry check.** Rejected in [#178](https://github.com/dmarx/luria/issues/178) and still rejected: a page
that groups a family correctly from a one-sided declaration is a page whose
data is half-written.

**Complete only symmetric relations** (what [#178](https://github.com/dmarx/luria/issues/178) shipped). Rejected: it
mistakes a constraint on the target field for a constraint on direction, and
leaves the general mechanism unavailable for the relation — succession —
that every chain is actually built on.

**Infer the converse without a declaration.** Rejected: naming the reverse
of `extends` requires knowing the project calls it `extended_by` and wants
it stored at all. Inventing either is a guess written into the record.

**Declare the converse on the chain** (`[luria.chains.lineage] converse =
…`). Rejected for three reasons: a converse does not depend on which chain
walks the field, so two chains over one field would repeat it and could
disagree; a field with a converse and no chain would never complete; and it
puts a fact about a relation inside a view's configuration ([ADR-004](ADR-004.md)).
