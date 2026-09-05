---
status: Active
title: "Read a note's frontmatter comments as directive comments"
version: 1
tags:
- mechanism
date: '2026-09-05'
summary: >-
  A reference field is a citation site — `superseded_by:` naming a document
  that was itself later retired is reported at its line — but the markdown
  scan read only HTML comments, so the finding could be acknowledged only
  file-wide. Whole-line `#` comments inside the frontmatter are now directive
  comments, and in frontmatter a line-scoped directive reaches the whole YAML
  entry below it. Rejected: exempting reference fields from the retired-citation
  report, which would hide the one edge the report exists to question.
---

# ADR-tmpn57wd: Read a note's frontmatter comments as directive comments

## Context

`ref_status` scans every line of a record document for citations, and the
frontmatter is not exempt: `superseded_by:` naming a document that was itself
later `Rejected` is reported at the field's line, as a sentence citing it
would be. That is right — a Superseded→Rejected chain is exactly the kind of
history a reader should be able to find deliberately kept (a downstream
record's DP says so in as many words) — and it is a judgement call, so the
answer is a directive at the site.

The directive parser read comments per file type: HTML comments in markdown,
`#`/`//`/`/* */`/`--` in code. A record document is markdown whose
frontmatter is YAML, and YAML's comment is `#`. So the one spelling that
could answer a frontmatter finding *in place* was never read, and the first
downstream project to hit the case wrote a file-scoped `inactive-ok-file:`
for a one-line finding — broader than the judgement it recorded.

A second, smaller fact shaped the fix. `luria repair` writes `superseded_by:`
as a list, which puts the code on the line *after* the key. A line-scoped
directive above the key, under the rule "this line and the next", covered
the key and missed the citation; firing the new reader on the real case
produced a stale-directive report where a warning had been.

## Decision

1. **Whole-line `#` comments inside a markdown file's frontmatter are
   comment fragments**, read by `directives.find` like any other comment.
   Only the frontmatter span is scanned: a `#` in the body is a heading, and
   a `#` inside a YAML value is data; neither is ever a comment.
2. **In frontmatter, "the line below" is the entry below.** A line-scoped
   directive there governs its own line, the next line, and that entry's
   continuation lines — indented lines and `- ` items. In prose the scope
   is unchanged: its own line and one more.

Nothing about the vocabulary or the other scopes changes. `-block` and
`-file` mean what they meant; the stale-directive report still fires on a
directive that reaches no citation.

## Alternatives considered

- **Exempt reference fields from the retired-citation report.** A
  `superseded_by:` naming a retired document is the field doing its job,
  so why report it? Because the report's question — *did you mean to point
  at something retired?* — applies to a successor that was itself retired
  with more force than to a sentence. A chain nobody noticed is the report's
  reason to exist; a chain somebody kept is one directive. Exempting the
  field hides the first to save writing the second.
- **Keep line scope literal and document "put the comment above the list
  item".** YAML allows a comment between the key and its first item, so it
  works. It puts the directive inside the entry it excuses, and it fails
  silently the first time a repair rewrites the block above it. The entry
  is the unit a reader sees; the scope should be too.
- **A new scope suffix, `-entry:`.** Explicit, and one more thing to
  remember for a distinction that only exists in frontmatter. The scopes
  are meant to be uniform across directives (see `directives.py`); making
  "line" mean the natural unit of the syntax it sits in keeps them so.
- **Status quo.** `inactive-ok-file:` remains the only spelling that
  reaches a frontmatter site. It works, and it acknowledges every citation
  in the file rather than the one being judged.

## Consequences

- A directive above a frontmatter field now excuses the field; the
  downstream record that prompted this can replace its file-scoped
  acknowledgement with a line-scoped one once it takes this release.
- `set_status` rewrites the status block by regex and knows nothing of
  comments. A directive placed between `status:` and `superseded_by:`
  survives a rewrite but may end up below the field it was written above,
  at which point the stale-directive report says so. That is the existing
  guarantee, not a new one.
- Tests pin: a frontmatter directive is found with entry scope; a
  directive-shaped heading in the body does not fire; a file with no
  frontmatter reads no `#` comments; prose keeps one-line scope; and,
  end-to-end, a `superseded_by:` naming a Rejected document is excused by
  the comment above it and reported without it.
