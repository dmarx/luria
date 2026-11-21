---
status: Proposed
title: 'luria new refuses a title that cites a code, since the repair links the code in the heading and not in the title'
version: 1
tags:
- mechanism
date: '2026-11-21'
summary: >-
  A title that cites a code scaffolds a document the lint rejects after
  the first repair: the repair links the code in the body heading, which
  repeats the title, and leaves the `title:` field bare, so the
  title-matches-heading check fails. In Nucleation it failed docs-check
  twice in one night, the second time after a postmortem had recorded the
  rule. `luria new` now refuses such a title with a message that says why
  and what to do. A code in backticks is a mention and passes, and only
  this project's schemes and remotes count as codes. Rejected for now:
  changing the repair or the check; either would let the title keep a code
  that reads as a citation in one place and not the other.
---

# ADR-tmp648gb: luria new refuses a title that cites a code, since the repair links the code in the heading and not in the title

## Context

A scheme document's heading repeats its title, `# CODE: title`, and the lint
holds the two equal. The repair links bare codes in prose, which includes
the heading and excludes the front matter. So a title that cites a code
leaves the document consistent until the first repair, and inconsistent
after it: `title: '… as ADR-068 does …'` against
`# ADR-x: … as [ADR-068](ADR-068.md) does …`.

Nucleation hit this twice on 2026-11-21, on an argument's title and then on
a decision's, each failing its pull request's docs-check. The postmortem of
the first recorded the rule, no code in a title, and the second came from a
script that did not know it. By this project's own working agreement, a
guard that keeps catching you is a bug report about the workflow: the fix is
to remove what generates the mistake.

## Decision

`luria new` refuses a `--title` that cites a code, before writing anything,
with a message naming the code, saying why, and offering the two ways out:
name it in words, or put it in backticks as a mention. What counts as a
citation is what the repair would link: `find_refs` on the title, so a code
of this project's schemes or remotes, not any word shaped like one
(`GPT-4` passes), and not a code in backticks.

## Alternatives considered

- **Have the repair leave a heading's codes alone.** It would keep the two
  equal, but the heading would then show an unlinked citation the lint
  elsewhere reports, and a reader would get no link from it.
- **Compare title and heading with links stripped.** The check would pass,
  but the title would cite a code that resolves in the heading and not in
  any view that renders the title, such as an index row.
- **Leave it to the rule.** The status quo, which failed twice.

## Consequences

- A filer who wants to cite a code in a title is told at once, and the code
  goes in the body.
- Documents written by hand or by other tools are not checked at filing;
  the lint still catches them after the repair.
- The other two fixes stay open if titles that cite codes turn out to be
  wanted.
