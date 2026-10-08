---
status: Active
title: 'A manuscript about the record lives under docs/, so its citations are edges'
version: 1
tags:
- record
date: '2026-10-08'
summary: >-
  A paper about the record is filed under `docs/paper/`, one numbered file per
  section, listed in the docs map, with author-year citations and a
  hand-written reference list. `docs/` is the one place the lint reads prose
  for codes, so the paper's citations of the record become checked edges and a
  retired decision names the paragraph that leaned on it. Rejected: a
  top-level `paper/` (never scanned: a bare code in one produced no finding),
  LaTeX with a bibliography file (no TeX toolchain here, raw citation keys on
  the published site, and a second copy of the reference list), and one long
  file (twelve thousand words, past the size the record keeps files to).
---

# ADR-tmp1pvmy: A manuscript about the record lives under docs/, so its citations are edges

## Context

The record needed a long-form argument about what it is for, written as an
academic manuscript. A manuscript cites the decisions and principles it
rests on, and those citations are dependencies: a claim can go stale without
changing, because the thing it relied on changed instead. Whether a
retired decision would surface the paragraph that relied on it depends on
where the file sits, because the lint reads prose for codes only in places it
is told about.

That was tested before choosing. A scratch file at the repository root's
`paper/x.md` containing a bare `ADR-001` produced no finding and no request to
link it, while the same text under `docs/` is linted, linked by
`luria link --fix`, and checked against the status of what it cites.

## Decision

The manuscript lives in `docs/paper/`: one file per section, numbered in
reading order, a `metadata.yaml` for title and author, a `references.md`, and a
`README.md` that gives the reading order and the pandoc command. Every page is
listed in the docs map, which the lint requires of anything under `docs/`.
Citations of other work are plain author-year text with a hand-written
reference list. Citations of the record are bare codes, linked by the fixer. A
section that cites a retired decision on purpose carries an `inactive-ok-file`
directive with its reason.

Two non-obvious parts. The directives must be file-scoped when a retired
decision is cited more than once on a page, since the default scope covers only
the line and the line below; the first lint of the paper caught exactly that.
And the decisions a hand-written page cites carry the `docs` tag, so the nine
that lacked it were tagged in the same change.

## Alternatives considered

- **A top-level `paper/` directory.** The conventional place for a manuscript,
  and the one that lost: its prose is never scanned, so the paper's most
  load-bearing sentences, the ones that rest on the record, would be the
  unchecked prose the record exists to prevent.
- **LaTeX and a BibTeX file.** The usual academic stack. There is no TeX
  toolchain in the environment, the published site would show raw citation
  keys, and a bibliography file duplicates the reference list the reader
  needs on the page. Pandoc builds HTML and Word from the markdown without it.
- **One file.** Simpler to read in a viewer; the manuscript runs to about
  twelve thousand words, and the record keeps files short so that a partial
  update touches a small file.
- **Status quo: no paper.** Costs the argument itself, which the documentation
  states as a list of mechanisms and nowhere states as a position.

## Consequences

The paper is a dependent of the record: retiring any decision it cites, or the
principle on shared artifacts, names the paragraph. The cost is that the paper
is now subject to the docs house rules, including the map entry for every
section. The in-text author-year citations are not machine-checked against the
reference list, so a dangling citation is possible; they were checked once by
script when the manuscript was written. Figures taken from the record are dated
observations and will drift.
