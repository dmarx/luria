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
# `Superseded — by [ADR-tmpiggbw](ADR-tmpiggbw.md)` and leave its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Active'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpiggbw:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'A finding names the key that declared its obligation; the record page lists the contract; no explain verb'

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
  A lint finding said "(luria.toml)" and no more, which is one file today
  and the wrong table the day a second authoring surface exists. Findings
  now cite the key that declared the obligation, the generated record page
  lists each scheme's whole contract from the same renderer, and there is
  no `luria explain` verb: provenance belongs where a surprised author
  meets it, and [ADR-030](ADR-030.md) retired the last standalone report commands
  nobody ran. Rejected: the verb, a verbose lint mode, and a separate
  explanation renderer that would drift from the findings.

---

# ADR-tmpiggbw: A finding names the key that declared its obligation; the record page lists the contract; no explain verb

## Context

The proposal in [#141](https://github.com/dmarx/luria/issues/141) asked for `luria explain CODE` early — before any new
semantics — as the test of whether a compiled contract stays
comprehensible. The instinct is right: distributed obligations are only
ergonomic if the tool can always answer *why does this rule apply?* The
verb is the wrong shape for it.

Two facts from this record decide that. [ADR-030](ADR-030.md) retired `luria ref-status`
and `luria pending`, standalone report commands whose information had
already moved into `luria lint` and `luria reports`, on the finding that a
command nobody runs is a surface nobody maintains. And the findings the
contract pass already printed carried provenance — but only as the word
"luria.toml", which names one file and no key. With one authoring surface
that is harmless. The proposal's later phases would add a second, and
"declared in luria.toml" would then send a reader to the wrong table.

## Decision

**Provenance lives in the finding.** Every contract finding cites the key
that declared the obligation, every key when more than one did:

```text
no `source:` in frontmatter — the SOTA scheme declares it a LIT reference
  (luria.toml: schemes.SOTA.requires, schemes.SOTA.references.source)
`primary_topic` wants exactly one of … — has none
  (luria.toml: schemes.SOTA.tag_groups.primary_topic; members from `record/topics.yaml` `primary_for`)
```

**The whole contract renders on the record page.** `docs/record.md` gains
a section, *What an entry must carry*, listing each scheme's obligations
with the same citations — generated by `luria index` like the rest of that
page, so a project that declares a table gets the description for free.

**One renderer.** The finding's citation and the page's line come from the
same functions in `luria/contract.py`. The page cannot say one thing and
the lint another, which is the [DP-4](../../docs/design-principles.md#dp-4) requirement and the reason the second
consumer was cheap.

**No `luria explain`.** Whole-entry explanation, if it ever proves wanted,
hangs off an existing workflow. Nothing today asks for it: a surprised
author meets the finding, and a reader wanting the whole picture has the
page.

## Alternatives considered

- **`luria explain CODE`**, as proposed. A verb that renders one entry's
  contract with provenance. It is [ADR-030](ADR-030.md)'s retired shape exactly — a
  report nobody runs, because the moment a rule surprises someone they are
  looking at a lint line, not typing a command. Its content is now split
  between the finding (the rule that fired) and the record page (all of
  them).
- **A verbose lint mode** (`luria lint --explain`). Keeps the CLI surface
  flat and still asks the author to re-run. The finding is the one output
  they already have; making it self-explanatory costs a parenthetical.
- **Leave "(luria.toml)".** Enough while there is one file. The proposal's
  own gate says no second authoring surface without a measured failure,
  and if that failure arrives the citation has to already be key-precise
  or every existing finding gets rewritten at the same time as the
  semantics change.
- **A separate description renderer for the page.** Prettier prose,
  written once, and the first change to a finding's wording leaves the
  page describing a rule the lint no longer states that way.

## Consequences

Findings are longer by one parenthetical. Existing tests matched on the
wording before the citation and were unchanged; the citation is appended.

The record page for this repository says *nothing beyond the standard
fields*, truthfully, and names the three tables that would change that.
The knowledge-base example, which declares all three, renders a full
section — and its `source` is now a declared `LIT` reference rather than a
bare `requires`, which [#141](https://github.com/dmarx/luria/issues/141) named as the second dogfooding experiment: the
untyped form accepted a decision's code and a sentence as a paper
([ADR-060](ADR-060.md)), and the example was still teaching it.

When a second source of obligations arrives, `Field.because` is where it
goes, and the citation renders it without this decision being reopened.
