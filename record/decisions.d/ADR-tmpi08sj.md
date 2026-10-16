---
status: Active
title: 'A view may be a Jinja template over the record'
version: 1
tags:
- architecture
- config
- mechanism
date: '2026-10-15'
summary: >-
  A record may declare `views`: a Jinja template, rendered by `luria index`
  into any file in the repository, with the record as its context. A
  template selects documents with `doc`, `docs` and `vocabulary`, and walks
  the graph with `match`, a path pattern written inline in [ADR-129](ADR-129.md)'s
  syntax. It writes codes bare, and the output passes through the link fixer
  in the output's own frame, so no template spells a link target. Templates
  compose with Jinja's own `include`, `import` and `extends`, so a
  hand-written file with a generated region is a template that holds the
  prose. The environment is sandboxed, strict about undefined names and
  blind to the clock, so a view stays a pure function of the tree.
  Rejected: generated regions in hand-written files, `str.format`, a
  logic-less engine, a Python hook, a `link` filter, named patterns only,
  and a manuscript scheme.
influenced_by:
- ADR-012
- ADR-035
- ADR-125
- ADR-129
---

# ADR-tmpi08sj: A view may be a Jinja template over the record

## Context

Every view luria renders is a Python generator: the index and its tag pages,
the document scheme ([ADR-012](ADR-012.md)), the journal books, the chains, the reports, the
record description. A project that wants any other projection of its record
writes it by hand. That is the drift [DP-002](../principles.d/DP-002.md) names, and the
two downstream records show it.

- nucleation's `CLAUDE.md` restates its `luria.yaml`: which directory holds
  which scheme, which fields are required, that tags come from a closed
  vocabulary. Each sentence is true until the config changes.
- nucleation's notes, claims and arguments cite the sections of a paper by
  number, about 450 times, as prose ("Section 5.6"). The paper's outline is
  copied into every one of them, and none would notice it moving.
- [ADR-129](ADR-129.md) gave the record path patterns, so a chain can walk claim →
  argument → claim. It left two things open, both of them views: an outline
  that walks a pattern across schemes, and transcluding document bodies "so
  views can compose into a manuscript".

A manuscript, an agent's bootloader, a project's documentation and a
reading list for one question are the same thing at different scales: prose
someone writes, around facts the record already holds. Each needs the facts
derived and the prose free. No fixed generator gives both, and one more
generator per shape is a generator per project.

## Decision

**A record may declare views.** Each is a template and an output:

```yaml
views:
  bootloader:
    template: record/views.d/CLAUDE.md.j2
    output: CLAUDE.md
```

`luria index` renders every view with the others, and `luria index --check`
reports a stale one, so a view is held to what every view is held to. The
output can be any path in the repository, a root file included.

**The engine is Jinja**, in its sandbox, with `StrictUndefined`. Templates
load from the project root, so a template can `include`, `import` or
`extends` any file in the repository. Composition is Jinja's, not luria's.

**The record is the context.** A template reads it through a small API:

- `doc(code)`: one document, or a render error if the code resolves to none.
  **A document's attributes are its scheme's fields**, not a list luria
  keeps. They are what the scheme's contract declares (`requires`,
  `references`, `fields`, derived fields), the keys every scheme carries
  (`title`, `status`, `summary`), and anything else its frontmatter holds.
  Each is read as the contract reads it:
  - a status is its value, without its note;
  - a vocabulary field left unwritten is its default;
  - a reference field holds documents, so `c.rests_on[0].title` works;
  - a prose field is rebased;
  - a declared field left unwritten is empty.

  A name the scheme does not have is Jinja's undefined. It is an error when
  used, and the error lists the fields the document has, but `is defined`
  and `| default` work on it. Besides its fields a document has `code`,
  `body` (the text below its title heading), `part(heading)` for one
  section with its subsections, and `fields()`. Item access reads the same
  fields, which reaches a field named like one of those.
- `docs(scheme, in_force=None, **where)`: a scheme's documents in code
  order, filtered on fields read the same way. A list field matches when it
  holds the value. `in_force=True` keeps the documents whose status is the
  scheme's own `active` word, and `False` keeps the rest, so a template
  iterating "the principles in force" does not spell a word each scheme
  chooses for itself.
- `vocabulary(name)`: a vocabulary's values in their declared order, each
  with its `label` and `blurb`.
- `schemes()` and `journals()`: each with its title and blurb, the
  directory it is filed in and where its view renders, so a bootloader
  can say where things are without restating `luria.yaml`.
- `match(pattern)`: every match of a path pattern written inline, in
  [ADR-129](ADR-129.md)'s syntax, as rows mapping each named node to its document. The
  pattern is parsed and checked against the schemes exactly as a named one
  is. A pattern the record declares can be named instead of spelled. Rows
  are ordered by their codes, taken in the order the nodes are named. An
  anonymous node is matched and not shown, and a pattern that names no
  node is refused, since its rows would be empty. The lowering shows one
  more predicate for a view, `pattern_row(P, Match, Var, X)`, and only when
  a view asks, so the programs a chain solves are unchanged.

**A template never spells a link target.** It writes codes bare. The output
passes through the link fixer in its own frame, the directory the output
lands in. Any body, part or summary a template transcludes is rebased from
its source's frame first, so the links it already carries still resolve.
There is one link resolver, and it is the one `luria link --fix` uses.

**A view is a pure function of the tree.** The sandbox exposes no clock, no
environment, no filesystem beyond the loader and no network. Iteration
order is the record's: code order, then declared order. This is
[ADR-035](ADR-035.md)'s rule for reports, applied to every view.

**A broken template fails `luria lint`.** Views are not rendered on a
branch, so the lint renders each template to discover failures and discards
the output. A typo in a code, a field or a pattern then fails the
contribution that made it, not the job on the default branch after it has
merged.

**A markdown output carries the generated stamp**, naming its template, so a
reader of the file knows where to edit.

**A view's output is generated**, for the citation scan as for the fixer,
like a chain page. A code in it was put there by a template, so a finding
sited in the output would name a line nobody can annotate.

**What a view reads is recorded, by template line.** Each read of a
document is sited at the template file and line it ran on, found through
the mapping Jinja's own tracebacks use, so a read inside an `include`d file
is sited there. A read is either a *transclusion* or a plain *read*. A
transclusion carries the document's assertion into the output: its `body`,
a `part`, its `summary` or `origin`. A plain read names the document: its
code, its title, its status, a reference. Two things follow from the
record:

- **`retired-transclusions`**, a lint warning that `fail_on` can promote
  like the other reference findings. It reports a transclusion of a
  document whose status is its scheme's `retires_on`, naming its
  successor. It is acknowledged in the template, with `inactive-ok:` in a
  Jinja comment on the site's line or the line above. Naming a retired
  document is not a finding, because that is what a page about revisions
  does.
- **"Rendered into"** on each document's page in `luria site`: the outputs
  of the views that read it, so a reader about to change a claim learns
  where else its words appear.

**A view can be pinned, so its output stops moving once it is published.**
This follows the model of `pins.py`, pointed inward. `pin: true` on the
view registers the pin. `luria views --pin NAME` endorses it: it renders
the view, writes the output, and records in a committed `views.lock.json`
a hash of the output and, per document, a hash of every value the render
read from that document, in the order it read them. After that:

- `luria index` leaves the committed output alone;
- `luria lint` re-renders the view and reports `view-drift`, a failable
  warning, naming each document whose read values changed. It reports a
  template change as one, and a committed output that is not the one
  endorsed as another;
- re-endorsing after review is the acknowledgement, and it re-renders.

Because the hashes are of what the view read, not of the files, an edit
to a part the view does not quote is not drift. A registered pin that has
no endorsement renders as any other view and is reported until someone
endorses it.

### Phasing

1. `views`, `doc`, `docs`, `vocabulary`, `schemes`, `journals`, `part`,
   the link pass, the staleness check and the lint render.
2. `match`, which needs the pattern lowering to return every named node
   of a match rather than a chain's two ends and its inner nodes, which
   cannot be rejoined into rows.
3. Reads recorded per view: a finding when a view transcludes a retired
   document, and each document's page naming the views it renders into.
4. Pinned transclusion, for an output that must stop moving once it is
   published.

## Alternatives considered

- **Generated regions inside hand-written files**, as the README's badges
  are. Jinja already composes. A file that is mostly prose is a template
  that is mostly prose, and a region is a second mechanism for something the
  first already does. The README regions stay as they are, since they
  predate this decision and nothing here needs them changed.
- **`str.format`**, which `derive` already uses. It cannot loop, and every
  view this decision is for loops.
- **A logic-less engine (Mustache).** It is safer, but it pushes selection
  out of the template into config, where the reader of the view cannot see
  it. [ADR-125](ADR-125.md)'s bar is that a reader sees the rule where it is used.
- **A Python hook per view.** It can do anything, which is the problem:
  arbitrary code in a record is not a rule a reviewer reads, and it can
  reach the clock.
- **A fixed set of document attributes** (`title`, `status`, `summary`,
  a raw `meta` mapping). That is a second schema beside the scheme's own:
  a field a project declares would be reachable only through `meta`, read
  raw, so a defaulted vocabulary field would read as absent and a
  reference as a string. The contract already says what each field is.
- **A `link` filter.** It would be a second link resolver beside the fixer,
  and the two would disagree about frames. Running the output through the
  fixer means a template cannot get a target wrong.
- **Named patterns only.** That would keep every pattern in `luria.yaml`.
  But a pattern used by one view reads best where it is used, and an inline
  pattern goes through the same parser and the same checks, so nothing is
  lost by allowing it.
- **Pin a view to a commit**, rendering pinned transclusions from the
  documents as they stood in history. That would let a template say
  `doc('CLAIM-012', at='v3')`. But it puts git history on the render path
  that every lint runs, and it answers a different question. A pin's
  question is "has the published text stopped matching the record?", and
  the committed output already holds the published text. The hashes say
  which documents moved.
- **Hash each read document's whole file.** It is simpler, and it is wrong
  for a paper. Adding a relation to a claim, or editing a section the paper
  never quotes, would read as drift, and a warning that fires on every edit
  teaches people to re-endorse without reading.
- **Report a transclusion of any document not in force**, as the citation
  scan reports any citation of one. On nucleation, a view transcluding one
  line of argument read 28 claims. 14 were Proposed, which in that record
  means held provisionally: the argument in progress. The scan's rule would
  have reported 17 sites, and `retires_on` reports 2. A view of an argument
  is made of claims still in play, so reporting them would bury the two
  that the record has stopped holding.
- **A manuscript scheme**, with sections as documents. A manuscript is one
  template among many. A scheme for it would fix one shape and leave the
  bootloader and the documentation without one.

## Consequences

- `jinja2` becomes a dependency. It is pure Python and stable.
- The link fixer must not scan templates: a code inside an expression, such
  as `doc("ADR-012")`, would be rewritten into a link and break the
  template. Templates sit outside every directory the fixer scans, and a
  test holds that.
- A view's output can sit outside every view directory, so removing a view
  from the config leaves its last output behind. The orphan check does not
  see it. Removing a view means deleting its output in the same change.
- `luria lint` gets slower by one render per view. For the views this is for
  it is milliseconds.
- Retirement is the one word `retires_on` names. A Rejected claim
  transcluded into a view is not reported, because luria has no role
  saying that Rejected means "no longer held". If that is wanted, it needs
  a role of its own, and adding one is a decision for that role, not for
  this one.
- An `inactive-ok:` on a line inside a loop excuses that code wherever the
  loop runs. A loop that transcludes several retired documents names each
  of them there.
