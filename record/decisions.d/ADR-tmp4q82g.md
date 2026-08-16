---
status: Proposed
title: A link target is checked from where the prose renders
version: 1
tags:
- record
- mechanism
date: '2026-08-16'
issue: '#100'
summary: >-
  Every reference check asks about a code — does [ADR-035](ADR-035.md) name a document, what
  is its status, how is it spelled. None asks whether the path wrapped around
  it goes anywhere, so a hand-written target could be dead through ninety-nine
  links and eleven clean lints. `broken-targets` resolves each relative target
  from `link_base` — where the prose renders, not where the file sits — and
  reports what does not exist. A report rather than a lint error, because
  unlike a bare code a wrong path is not mechanically fixable: the fixer owns
  codes, and an arbitrary path is a typo only its author can resolve. Rejected:
  checking anchors too (a different and much noisier question), and resolving
  from the source directory (the frame a reader never uses).
---

# ADR-tmp4q82g: A link target is checked from where the prose renders

## Context

Record prose is rendered into views in other directories. A journal entry lives
in `record/reading.d/2026/08/16/` and is assembled into
`docs/reading/2026-08-16.md`; a document-rendered scheme's source is collected
into one page; a stub's prose lands in the index it introduces. So a relative
link target has to resolve from where the text *lands*, and the depth counted
from the file's own directory is a different number.

The rule follows, and has been in `CLAUDE.md` since early on: never hand-write
a target, write the bare code and let `luria link --fix` spell it, because only
the fixer knows the frame. The affordance works. What was missing was anyone
checking the targets the fixer did not write.

An adopting project ran into it at full scale. Reading-journal entries carried
hand-written targets from the first commit — the arithmetic feels checkable,
which is exactly the trap — and **99 of them resolved to nowhere across eleven
commits, every one of which linted clean** ([#100](https://github.com/dmarx/luria/issues/100)).

Nothing was going to catch it. The reference checks are all about the *code*:
`unresolved-codes` asks whether [ADR-035](ADR-035.md) names a document, `retired-citations`
asks what its status is, `legacy-spellings` asks how it is spelled. A dead path
wrapped around a live code passes every one.

Firing the check on this repo's own scaffold showed the same defect shipped:
`template/record/decisions.d/README.stub` links to `[_template.md](_template.md)`
and `[design-principles.md](../design-principles.md)`, and the stub renders at
`docs/decisions/README.md` where neither exists. This repo's own copy of that
stub had been repaired by `luria link --fix` at some point, which is what hid
the divergence. Same shape as the scaffolded fixture codes fixed in [#96](https://github.com/dmarx/luria/issues/96), where a fresh
`luria init` reported five unresolved ones: the scaffold is prose nobody
re-reads, so a defect in it survives indefinitely.

## Decision

A `broken-targets` status class. Every relative markdown link target in a
scanned document is resolved against `cfg.link_base(path)` — the same authority
`luria link --fix` uses to *write* a target — and reported when it does not
exist. `target-ok:` acknowledges the deliberate ones.

The parts that are load-bearing rather than incidental:

**`link_base`, not `path.parent`.** This is the whole decision. The two frames
disagree by five directories for a journal entry, and the one a reader follows
is the view. Resolving from the source directory would accept exactly the
targets that are broken and reject the ones that work.

**Resolution is textual (`os.path.normpath`), not `Path.exists()` on the raw
join.** A view directory need not exist yet — `luria index` creates it — and
`..` traversal through a missing directory fails on the filesystem while
resolving fine for a reader. Text is also what a markdown renderer does.

**A report, not a lint error.** [ADR-035](ADR-035.md)'s test is whether the violation is
always wrong *and* mechanically fixable. This one is always wrong and is not
fixable: the fixer owns codes, and an arbitrary path is a typo only its author
can resolve. Nameable in `fail_on` for a project that has cleaned up.

**Targets carrying regex or format metacharacters are patterns, not paths.**
`uid = "(\d{4})[.:](\d{4,5})"` in a config example is link-shaped by accident,
and this repo's own record contains two such lines.

## Alternatives considered

- **Extend `luria link --fix` to repair paths instead of checking them.** It
  cannot: the fixer knows how to spell a target for a *code*, and a broken path
  that names no code carries no information about what was meant. Repairing
  only the code-shaped ones would leave the rest silently dead while looking
  like a complete sweep — the failure mode [DP-1](../../docs/design-principles.md#dp-1) objects to.
- **Detect indented code blocks rather than screening for metacharacters.** The
  correct discriminator, and markdown makes it genuinely ambiguous: four spaces
  inside a list item is a continuation, not code. A wrong answer there silences
  real prose. The metacharacter screen is cruder, states its own limit, and
  cost one line.
- **Check the `#anchor` too.** A different question, an order of magnitude
  noisier, and heading text moves for reasons that have nothing to do with the
  link. Dropping the fragment and checking the file it hangs off keeps the
  class at one meaning. Appending an anchor deliberately does *not* silence a
  missing file — that is a test.
- **Status quo.** The rule stays documented and unenforced, which is the state
  this record objects to everywhere else. The measured cost is 99 dead links in
  one downstream project and two in the shipped scaffold.

## Consequences

An adopting project turning this on for the first time should expect findings
proportional to how much prose it has hand-written, which is why the class is a
warning by default rather than a failure.

`target-ok:` joins the acknowledgement vocabulary and is the first directive
whose argument is a **path** rather than a code. The parser did not need
changing, and `directives.problems` reports one that no longer covers a link,
so the annotation still reports itself the day it stops applying.

The check knows only that a target is not anything, never what it should have
been. Someone who hand-writes a target that happens to resolve to the wrong
existing file gets no finding, and that residual hazard is still carried by the
ground rule alone.
