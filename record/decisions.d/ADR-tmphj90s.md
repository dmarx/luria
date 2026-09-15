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

# Active | Proposed | Deferred | Superseded | Rejected. Supersede when the
# CHOICE changes: set the old one to `status: Superseded`, name the successor
# in `superseded_by: ADR-tmphj90s` (a reference field: checked, resolved, an edge
# the index and the site render), and leave its body intact. A qualifying
# note for anything the field cannot say goes in `status_note:` — prose,
# like `summary:`, so a code in it is a citation. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: Active

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmphj90s:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: "A directive's argument list is syntax; its reason is prose"

# Which revision of this decision's claim you are reading. Standard frontmatter
# for every scheme, and it moves rarely here: a decision that CHANGES is
# superseded by a new one, not edited. Bump it when the same choice is restated
# more broadly — scope widened, wording generalized — and say what changed in a
# `history:` entry. Shown in the index only when it is not 1.
version: 1

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
- record
- mechanism

date: '2026-09-15'

# Optional. The issue(s) this decision came from: '#123'.
issue: '#270'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
---

<!-- mention-ok-file: DP-018 — the code quoted in the Context section, shown as the text of the bug. Named, not cited: this document claims nothing about whether it resolves. Deliberately not spelled again in this reason, which is the rule below -->

# ADR-tmphj90s: A directive's argument list is syntax; its reason is prose

## Context

`SHAPED_RE` matches a directive from its name up to the em-dash, and
`shaped_spans` blanks exactly that run before the reference scan runs. The
argument list is syntax — naming a code in a directive is governing it, not
citing it — and everything after the em-dash is ordinary text, scanned like any
other prose.

That boundary is not obvious from the outside, and it has now produced the same
bug twice in one week, both times in an acknowledgement I was editing to *fix*
an acknowledgement. Rewriting a reason, I named the governed code in the
explanation: "the DP pair became visible…" became "DP-018 became visible…". The
argument list was blanked, the sentence was not, and the annotation acquired a
citation that it then excused. The mention existed only because the annotation
explained itself.

The second time was worse in a specific way: the cost-reporting check reported
that self-made citation as a site the annotation was covering, and I read the
number as evidence the acknowledgement was earning its place.

There is a further wrinkle. In the first case the code was on a *continuation*
comment line, which is not part of the directive's matched span at all — it is a
separate comment fragment. So "blank the reason too" would not even have caught
it.

## Decision

The boundary stays where it is: the argument list is syntax, the reason is
prose, and a code named in a reason is a citation like any other.

The rule that follows is the one this exists to write down: **do not name a
governed code in an acknowledgement's reason.** The argument list is where a
code is governed; say "the DP code here" and the sentence reads the same without
creating the citation it is excusing.

## Alternatives

- **Blank the whole comment the directive introduces.** The obvious fix, and
  the one the working agreement points at — a hazard that catches you twice is
  a bug report about the workflow. Rejected on two counts. It would swallow
  genuine citations: an author writing "superseded by [ADR-060](ADR-060.md)" in a reason
  means that reference, and the reference graph should have it. And "the whole
  comment" is not a fact the parser has — a block's end is what `blocks()`
  guesses at and what `syntax.grow` exists to correct, so this would build a
  silencer on top of a guess and silence most reliably where the guess is
  worst.
- **Blank the reason but not continuation lines.** Cheaper and wrong: it fixes
  the case the parser can see and leaves the case that actually bit first,
  which was a continuation line. A fix that covers the easier half of a hazard
  is worse than none, because it retires the vigilance without retiring the
  hazard.
- **Leave it unwritten and rely on care.** The status quo, and its record is
  two for two against a reader who had just finished debugging this exact
  mechanism.

## Consequences

The rule is cheap to follow and costs a reader nothing. What it does not do is
catch you: nothing reports a reason that names its own governed code, so this
is a thing to know rather than a thing that is checked.

That is the follow-up this implies. The violation looks mechanically
detectable — a governed code appearing inside its own directive's comment can
only produce a self-excused citation, which is never informative — and if that
holds it belongs in the report alongside the other annotation findings. It is
not built here, because the same continuation-line problem that defeats the
blanking fix has to be solved to find the text in the first place, and that
deserves its own look rather than riding along with the decision.
