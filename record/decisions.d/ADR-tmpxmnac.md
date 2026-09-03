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

# Active | Proposed | Deferred | Superseded | Rejected, optionally " — <note>".
# Supersede when the CHOICE changes: set the old one to
# `Superseded — by [ADR-tmpxmnac](ADR-tmpxmnac.md)` and leave its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Active'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpxmnac:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'Typed edges are read from what the record already says, never from a new field'

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
  The citation graph had one kind of edge, "A mentions B", while three
  stronger facts sat in the record unread: a `Superseded — by` note, an
  `influenced_by:` list, and any field a scheme declares a reference. They
  are now read as typed edges, the field name being the relation, and the
  site renders each page's edges both ways. Three levels of claim, and
  only the top two are edges: a code in prose is a mention; a typed field
  is a named relation; the canonical `Superseded — by CODE` note is one
  derived relation. Any other code in a status note is a mention with a
  location, not a relation. No new frontmatter field: a `superseded_by:`
  beside the note would be the second copy of one fact. Rejected: that
  field; every code in a Superseded note as a succession; a `status_note`
  relation for the rest, which dresses a location up as a meaning; leaving
  it to Quartz's untyped backlinks; a relations DSL; and a lint for a
  successor-less Superseded, which the record's own audit does not justify.

---


# ADR-tmpxmnac: Typed edges are read from what the record already says, never from a new field

## Context

<!-- inactive-ok-block: ADR-058 — cited for its account of the graph; its rejection was the README's framing, not the account -->
The graph this package maintains has one kind of edge: a document *mentions*
another, found by scanning prose for codes. That is the right primitive —
the graph is a side effect of writing carefully ([ADR-058](ADR-058.md)) — and it is
coarser than what the record already knows.

Three facts in the record are stronger than a mention, and each was written
down long before anything read it as an edge:

| the fact | where it lives | since |
|---|---|---|
| this decision was replaced by that one | the `Superseded — by …` status note | [ADR-003](ADR-003.md) |
| this principle was shaped by those decisions | `influenced_by:` | [ADR-012](ADR-012.md) |
| this practice's evidence is that paper | a field the scheme declares a reference | [ADR-060](ADR-060.md) |

<!-- inactive-ok-block: ADR-007 — the superseded decision is the worked example: being retired is what makes it one -->
Nothing read them. The status report split the note off and discarded it;
the site rendered the status line verbatim; the index only rebased its
link. So a reader of [ADR-035](ADR-035.md)'s page was never told it replaced [ADR-007](ADR-007.md), and
a downstream practice page on a site lost its `source` entirely, because
frontmatter renders as nothing. [ADR-060](ADR-060.md) named typed backlinks as the
obvious next step and deferred them as a rendering change. The proposal in
[#141](https://github.com/dmarx/luria/issues/141) asked for the same edges and, for supersession, proposed a new field:

```yaml
status: Superseded
superseded_by: ADR-035
```

This record's convention is `status: 'Superseded — by [ADR-035](ADR-035.md)'`
— the pointer is in the note, and `luria migrate --strategy supersede`
writes that exact shape. A second field carrying the same code is the
drifting copy [DP-3](../../docs/design-principles.md#dp-3) warns about, and it would need a rule for what happens
when the two disagree.

## Decision

**Typed edges are derived from what the record already states.** A module
reads three of them; the field name is the relation:

```text
A ──source─────────→ B     any declared reference field, named for the field
A ──influenced_by──→ B     the `influenced_by:` list
A ──superseded_by──→ B     derived: status `Superseded`, note `by B`
```

Four details are load-bearing.

**No new field.** The supersession edge is read out of the note.

<!-- inactive-ok-block: ADR-015 — cited as the note that names two codes; it is superseded, which is why it has a note -->
**Three levels of claim, and only the top two are edges.** A code found
in prose is a *mention*: the citation graph, found by scanning, carrying
where it was found as provenance and nothing more. A typed reference field
is a *named relation*: the schema vouches for the field, so the field name
is the relation. A recognised construction in prose is a *derived
relation*, and there is one: `Superseded — by CODE` has a writer — `luria
migrate --strategy supersede` emits exactly that shape — and one meaning,
so the code in that opening position is the successor. Every other code a
status note names — the second code in a note that runs on
([ADR-015](ADR-015.md)'s does), what a `Deferred` was parked by, what a
`Rejected` was overturned by — is a mention with a location. Downstream, a
world-building record found four of its ten non-Superseded notes citing a
code; those are facts worth keeping, and the place that keeps them is the
citation scanner, once the note is read as the prose it already is (a
separate decision on field typing). `Superseded` is itself scheme-relative
([ADR-056](ADR-056.md)), which is one more reason to promote only the shape
with a mechanical writer.

**The status field is read as two things.** One `Status(value, note)`
parse, on the document, replaces the six places that split the word off
the note with three spellings of one regex. The word is data, checked
against the vocabulary; the note is prose, rendered and rebased for links.
Storage is unchanged; whether it should change is the migration decision
above, not this one.

**A remote code is never an edge.** A remote's namespace is theirs
([ADR-016](ADR-016.md)); the graph has no node for the edge to land on.

**Rendered where a document has room, in no stronger English than the
relation guarantees.** The site's record line gains the edges both ways: on
the page that supersedes, *Supersedes*; on the decision a principle cites,
*Influenced*; on a practice, its *Source*; on the paper, *Cited as `source`
by*. A mention gets no line of its own — the note renders with its links,
and the site's own backlinks list it. Composed with wikilinks and expanded by the resolver
that owns every target in the record ([DP-4](../../docs/design-principles.md#dp-4)), so nothing here spells a link.

This reads prose for a fact, which is what [ADR-003](ADR-003.md) chose frontmatter to
avoid — "a regex between a decision and its own metadata". It is the right
call here because the citation graph is already codes found in prose, the
note's shape is written mechanically by the migration machinery, and the
alternative is the duplicated field above. The tension is stated rather
than hidden.

## Alternatives considered

<!-- inactive-ok-block: ADR-007, ADR-015 — the example succession and the example run-on note; retired is the point -->
- **A `superseded_by:` frontmatter field**, as [#141](https://github.com/dmarx/luria/issues/141) proposed. The obvious
  home for a typed fact, and it loses on this record's own rule: the note
  already carries the code, so the field is a second copy that nothing
  relates, and the first disagreement between them has no arbiter. A
  migration writes the note; it would have to learn the field too.
- **Every code in a Superseded note as a succession**, which the first
  draft of this decision did, and a reviewer caught: [ADR-015](ADR-015.md)'s note names
  a second code that is not its successor, and the site would have said
  *Supersedes* of it.
- **A `status_note` relation for every other code in a note**, which the
  second draft did, and a reviewer caught: where a code was found is
  provenance, and naming the location as the relation dresses a location
  up as a meaning. A mention is a mention; the scanner already has a
  representation for one, with a location on it.
- **Leave it to the site's backlinks.** Quartz already lists every page that
  mentions this one. Untyped: "[ADR-007](ADR-007.md) mentions [ADR-035](ADR-035.md)" and "[ADR-007](ADR-007.md) was
  replaced by [ADR-035](ADR-035.md)" render identically, and the second is the fact a
  reader came for.
- **A `[luria.relations]` table** naming relations and their inverses. A
  named non-goal of [#141](https://github.com/dmarx/luria/issues/141), and nothing to configure yet: the field name says
  what the relation is, and the two built-in inverses fit in a dict.
- **Render the edges in the generated index and tag pages.** The index is a
  table with one row per document and no room for a list; the site page is
  where a document has room. Deferred rather than rejected — the graph is
  read once and any view can consume it.
- **A lint for a `Superseded` document whose note cites no code.** The
  check the edge makes possible. Not built: this record has three superseded
  decisions and all three name a successor, so the prose convention is
  holding, and [#141](https://github.com/dmarx/luria/issues/141)'s own gate says no obligation without a convention that
  has already failed.
- **Status quo.** Three facts written down and read by nobody, which is the
  shape this package objects to everywhere else.

## Consequences

Twenty-six of this record's sixty-six decision pages gain a typed edge the
moment the site is next built; every succession and every principle's
lineage now reads in both directions. A downstream record with declared
references gets its citations back on the site, in both directions, with no
configuration change.

The note stays the single source of the supersession fact, and the
derivation is one function that a project can read in full. What it does
not do is as deliberate: *parked by* and *overturned by* are meanings the
tool does not know, and the alternative to leaving them as mentions is the
tool guessing. Until the note is a prose key of its own, the codes in a
Deferred or Rejected note are cited by nothing the scanner sees; that gap
is named in the field-typing decision that closes it.

The lint for a successor-less `Superseded` document is one function away
when a record needs it. The graph is also the natural next consumer of the
compiled contract ([#141](https://github.com/dmarx/luria/issues/141)): an obligation over an edge rather than a field is
the shape the proposal's later phases want, and nothing here forecloses it.
