---
status: Proposed
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
  A document gives `code`, `title`, `status`, `version`, `summary`, `meta`
  (its frontmatter, derived fields included), `body`, and `part(heading)`
  for one `##` section of the body.
- `docs(scheme, **where)`: a scheme's documents in code order, filtered by
  frontmatter equality. A list field matches when it holds the value.
- `vocabulary(name)`: a vocabulary's values in their declared order, each
  with its `label` and `blurb`.
- `match(pattern)`: every match of a path pattern written inline, in
  [ADR-129](ADR-129.md)'s syntax, as rows mapping each named node to its document. The
  pattern is parsed and checked against the schemes exactly as a named one
  is. A pattern the record declares can be named instead of spelled.

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

### Phasing

1. `views`, `doc`, `docs`, `vocabulary`, `part`, the link pass, the
   staleness check and the lint render.
2. `match`, which needs the pattern lowering to return every named node
   rather than a chain's two ends.
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
- **A `link` filter.** It would be a second link resolver beside the fixer,
  and the two would disagree about frames. Running the output through the
  fixer means a template cannot get a target wrong.
- **Named patterns only.** That would keep every pattern in `luria.yaml`.
  But a pattern used by one view reads best where it is used, and an inline
  pattern goes through the same parser and the same checks, so nothing is
  lost by allowing it.
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
- What a view depends on is unknown until phase 3. Until then, a view that
  transcludes a superseded claim renders it without comment.
