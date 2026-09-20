---
status: Active
title: '`--body` hands the prose to the caller, but never the heading'
version: 1
tags:
- record
- mechanism
date: '2026-09-20'
summary: >-
  `luria new --body TEXT` (and a draft's `body` key) hands over a document's
  prose, so a tool holding a finished document can file it through the CLI
  instead of writing markdown itself. The `# CODE: title` heading stays
  derived from `title:` — a body that opens with one has it dropped rather
  than doubled — because the lint holds the two equal. Rejected: letting
  callers write the file and validating afterwards, which makes every tool
  re-derive the numbering, the heading and the frontmatter shape.
---

# ADR-tmptzmd6: `--body` hands the prose to the caller, but never the heading

## Context

`luria new` fills in what a machine can compute and leaves the prose to an
editor ([ADR-036](ADR-036.md)): the scaffold's body is the template's instructions, and a
human replaces them where replacing them is comfortable. That holds for a
human at a terminal. It does not hold for a tool that already has the prose —
strata-g's drop dialog authors a whole document on its canvas, frontmatter and
body together, and files it with `luria new --draft`. Before this change the
draft path accepted every field the scheme declared and refused the one thing
the dialog could not express, so the document arrived with its text still
reading "What was true that made this a question."

The alternative on offer was for the caller to write the file itself. That is
the boundary this project exists to hold: luria owns the files, a tool owns the
intent, and a tool that writes markdown has to re-derive the heading rule, the
numbering mode and the frontmatter shape — and will drift from them.

## Decision

`--body TEXT` (and a draft's `body` key) hands over the prose. It replaces the
template's body below the `# CODE: title` heading of a scheme document, the
placeholder paragraph of a journal entry, or the whole of a fragment — the
three kinds that have a body at all; a migration is YAML and ignores it, as it
ignores every other field flag.

**The heading is not the caller's to write.** It is derived from `title:`, and
`luria lint` holds the two equal, so `--body` never replaces it: the scaffolder
writes the heading from the title as it always did, and the body lands beneath.
A body that opens with its own level-one heading has that line dropped rather
than doubled — a tool that composed a whole document (the dialog previews one,
heading and all) would otherwise file two headings and a lint finding.

`body` joins the universal fields, which is what makes the draft path accept
it: a draft is refused any key the scheme has no opinion about, and without
that entry the key was exactly such a refusal.

## Alternatives considered

- **Let the caller write the file and have luria only validate it.** The
  boundary inverted: every tool re-implements the numbering mode, the
  `allocate: merge` temporary code, the derived heading and the frontmatter
  order, and each drifts separately. Validation after the fact tells a tool it
  got it wrong; scaffolding tells it nothing was ever its to get wrong.
- **`--body-file PATH` instead of inline text.** Better shell ergonomics for a
  long document and worse for everything else, and the caller that motivated
  this — a JSON draft — carries the text inline anyway. `--body "$(cat f.md)"`
  covers the file case with no new surface.
- **Keep the heading if the body supplies one.** Tempting, because the tool
  that composed the body knows the title too. It makes the lint's invariant
  (`title:` equals the heading) depend on the caller agreeing with itself, and
  a caller that disagrees files a broken document rather than a fixed one.
- **Status quo — a scaffold, then an editor.** Still the default and still the
  right shape for a person. It is the wrong shape for a tool with the prose
  already in hand, which is the only case this adds.

## Consequences

A tool can now file a complete document through the CLI, so strata-g's drop
dialog can author the body and never write markdown itself. The heading rule is
now enforced in two places — `new_scheme_doc` derives it, `replace_body`
refuses to let the body override it — and both have to keep agreeing; the tests
cover the pair together (a body with its own heading files exactly one).

The scaffold templates now serve two audiences: they remain the instructions a
human overwrites, and they are what a tool offers as the body's starting text.
Nothing in luria changes for that second use, but a template written purely as
a set of instructions to delete reads oddly when it is the draft a user starts
editing.
