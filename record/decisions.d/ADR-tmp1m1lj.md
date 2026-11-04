---
status: Proposed
title: 'The record description is rendered from a template luria ships, with its prose in the template and its facts from the config'
version: 1
tags:
- mechanism
date: '2026-11-04'
issue: '#395'
influenced_by:
- DP-003
- DP-015
summary: >-
  `docs/record.md` was built from Python strings: a header constant, eight
  section introductions in a tuple, and a markdown table assembled in each
  section function. It is now `luria:record.md.j2`, rendered in the
  sandbox [ADR-130](ADR-130.md)'s views use. `record_doc.context` gives the template
  facts read from the loaded config and no prose. The template holds every
  heading, introduction, table and empty-state line, so the page's text is
  edited in one place, and a section with nothing to show is left out by
  the template, heading and all. The output was byte-identical on luria's
  record, nucleation's, a fresh init, and three fixtures covering every
  empty and partial case. Rejected: registering the page as a view luria
  supplies, which would link it and so send the luria decisions its prose
  cites to the project's own; letting a project override the template,
  deferred until one asks; and keeping the strings.
---

# ADR-tmp1m1lj: The record description is rendered from a template luria ships, with its prose in the template and its facts from the config

## Context

`docs/record.md` describes a project's `luria.yaml`. Until now
`record_doc.py` built it entirely in Python:

- a `HEADER` constant;
- a `SECTIONS` tuple of eight titles and introductions;
- one function per section, each returning finished markdown with its own
  table, list or empty-state sentence.

Prose and layout were spread across string literals in a dozen places.
Changing the page's wording meant editing code. A rule about the page as a
whole, such as "a section with nothing to show is left out", had to be
enforced in `render()` over strings it could not inspect.

Two reviews on [#395](https://github.com/dmarx/luria/issues/395) showed what that cost. The first fix printed a remedy
into an empty section. The owner answered that "messages like this belong
in the same communication channel the linter uses", which led to the
`undescribed-schemes` class and to the page leaving the section out. Then
the owner asked for the build itself to "use a templated view". [ADR-130](ADR-130.md)
already gives luria a way to hold prose in a template and derive the facts:
a pattern's page is a template luria ships (`luria:pattern.md.j2`).

## Decision

The page is `luria/view_templates/record.md.j2`. `record_doc.context(cfg)`
returns data only:

- rows for the scheme, journal, fragment, remote, filing and settings
  tables;
- the schemes that describe themselves;
- each scheme's contract lines;
- the schema URL.

The template holds:

- every heading and introduction;
- a `table` macro, with `*None configured.*` for an empty table;
- the empty-state lines of the contract and settings sections;
- the rule that "What each family is" renders only when some scheme
  describes itself.

**It renders in the views sandbox** (`views._environment()`): strict about
undefined names, with luria's `luria:` loader and the `cell` filter. A typo
in the template is a render error naming its line, not an empty string.

**It is not linked**, and that is load-bearing. The page is made of example
codes (`LIT-001`, `ADR-012`), and its prose cites luria's own decisions
([ADR-071](ADR-071.md), [ADR-125](ADR-125.md)) and issues ([#279](https://github.com/dmarx/luria/issues/279)). Passed through the link fixer in a
downstream record, those would resolve to that record's documents of the
same number, which is wrong, and silently so. `Config.is_generated` keeps
the page out of the bare-reference lint, as before.

**The page did not change.** The refactor was checked by rendering
before and after, and the two were byte-identical for:

- luria's own record;
- nucleation's record;
- a fresh `luria init`;
- a one-scheme fixture with a vocabulary;
- a bare one-scheme config with every setting at its default;
- a config with a title-only, a blurb-only and a fully described scheme,
  compared against the previous module loaded from `HEAD`.

A test now fails if a heading or `*None configured.*` is written back
into the module.

## Alternatives considered

- **Register the page as a view luria supplies**, as pattern pages are,
  listed in `cfg.views` and rendered by `views.render`. That would bring
  pinning and `luria views` listing for free. But `views.render` links its
  output, which would misdirect the luria citations above. It would also
  need the context built when the config loads, before `contract` and `new`
  can be asked. A view option to skip linking, plus a lazy context, would
  make it possible. That is a change to [ADR-130](ADR-130.md)'s machinery for one page,
  and is left until a second page needs it.
- **Let a project override the template.** That is the obvious next step
  once the prose is a template: a project could word its own record
  description. But `luria:` templates cannot be shadowed by design (a
  project cannot replace one of luria's), and no project has asked. If one
  does, a `paths` or `views` key naming a project template is the shape.
- **Keep the strings.** Each later change to the page's wording or layout
  would have stayed an edit to Python. The rule about empty sections would
  have stayed a `strip()` check over finished markdown.

## Consequences

- The page's text is changed by editing one template. A rule about its
  layout is a template condition over data.
- The empty-state lines are now visible in one file. Two of them still tell
  the reader how to configure more: the contract section's "A scheme asks
  for more with `requires` …" and the settings section's "See the schema
  for what else can be set." By the reasoning that moved the families
  remedy to the lint, they are candidates for removal. That is a wording
  decision, left to the owner.
- `record_doc.py` drops from 345 lines to about 270, and its section
  functions return lists, which a test can check without parsing markdown.
