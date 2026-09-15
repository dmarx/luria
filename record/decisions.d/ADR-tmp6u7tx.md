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
# in `superseded_by: ADR-tmp6u7tx` (a reference field: checked, resolved, an edge
# the index and the site render), and leave its body intact. A qualifying
# note for anything the field cannot say goes in `status_note:` — prose,
# like `summary:`, so a code in it is a citation. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: Proposed

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmp6u7tx:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'Register the directive vocabulary, and report a near-miss'

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
issue: '#271'

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
---

# ADR-tmp6u7tx: Register the directive vocabulary, and report a near-miss

## Context

There is no one place that says what directive names exist. Each consumer owns
a constant — `TARGET_OK` in `link_targets.py`, `ACK` in `narrow_titles.py`,
`DIRECTIVE` and two siblings in `ref_status.py`, and five more — and the
vocabulary is the union of nine constants across eight modules, discoverable by
grep. `docs/directives.md` documents the table by hand beside them.

Nothing validates a name. `DIRECTIVE_RE` accepts `[a-z][a-z-]*` before the
colon, so a misspelling parses as a directive and then finds no consumer. It
fails twice over, which is measured rather than assumed:

```
TYPO  parses as a directive: True
TYPO  blanked by shaped_spans: False
```

The acknowledgement does not suppress the finding it was written for — and
because the name is unrecognised its argument list is not blanked either, so
the codes it names are read as ordinary citations. A comment written to silence
a finding adds references instead. That is the same self-citation shape [ADR-104](ADR-104.md)
decided the boundary for, reached from the other direction.

Every signal in this record predicts a registry. Argument validation already
exists (`problems(directive, valid_args)` reports unknown arguments), so the
harder half is built. [DP-001](../principles.d/DP-001.md) forbids a silent refusal and [DP-015](../principles.d/DP-015.md) says an
absence must not read like a success. [ADR-003](ADR-003.md) closed the status vocabulary and
enforced it by lint, on the explicit reasoning that an open vocabulary drifts
into synonyms. [ADR-098](ADR-098.md) made vocabularies configuration, declared once.

## Decision

**Proposed, not settled.** Two separable parts, and the case against the second
is strong enough that it is worth reading before agreeing.

1. **Register the names in one place.** A module that names the vocabulary,
   with each consumer importing its own word from it. This is bookkeeping and
   the argument for it is only that the union of nine constants is currently a
   fact you recover by grep, and `docs/directives.md` restates it by hand —
   which is the shape [DP-003](../principles.d/DP-003.md) says will drift.

2. **Report a name that is a near-miss for a registered one.** Not an unknown
   name: a name within a small edit distance of one luria knows. `inactve-ok`
   is reported and suggests `inactive-ok`; `noqa` and `Note:` are ignored.

## The case for

A misspelled acknowledgement is the worst failure mode this vocabulary has,
because it is silent in the direction that matters. You wrote the comment, the
finding stayed, and nothing connects the two — the report names the citation,
never the unrecognised comment three lines above it. The diagnosis is entirely
on the reader, and the reader is usually the person who just made the typo.

It also compounds, per the measurement above: the unblanked argument list turns
a failed suppression into new citations. That is worse than a no-op.

And it is cheap to detect. Near-miss detection over this corpus:

```
corpus false positives under near-miss: 0
  'inactve-ok'    -> suggests inactive-ok
  'unresolvedok'  -> suggests unresolved-ok
  'targe-ok'      -> suggests target-ok
  'noqa'          -> ignored
  'one'           -> ignored
```

## The case against

**The obvious version of this check is unusable, and the numbers are not
close.** Reporting every directive-shaped comment whose name is not registered
flags **87 comments across 35 distinct names** in this repository, and
approximately none of them are typos. They are `noqa` (25), prose beginning
"config:" (17), `pragma: no cover`, `type: ignore`, and a long tail of ordinary
English: "why", "note", "one", "reasons", "before", "acknowledgement",
"opportunity". `DIRECTIVE_RE` matches `word:` at the start of a comment body,
and that is simply how people write.

**The registry already exists, and validation is not what it is for.** The
`names` set handed to `find` and `shaped_spans` is the vocabulary, and it is
load-bearing as a *recognizer*: because the shape is indistinguishable from
prose, being a known name is what makes something a directive at all. A
validator needs to tell a misspelled directive from a sentence, and the shape
cannot. Near-miss detection is a heuristic standing in for an intent the syntax
never recorded.

**Zero false positives today is not zero forever.** The measurement is against
one corpus at one moment. A project whose prose happens to contain a word near
a directive name gets a finding it cannot act on, and the cutoff that produced
zero here is a tuned constant, which is the kind of thing this record is
usually suspicious of.

**The failure may not be worth the machinery.** It is not fully silent: the
finding you meant to suppress reappears, so something visible happens. Nobody
has reported hitting this. The evidence for the failure mode is one constructed
example, not an incident.

## Alternatives

- **Status quo.** Costs nothing and has no known victim. The argument against
  is that the absence of a report is not evidence of absence when the symptom
  is "the acknowledgement I wrote did nothing".
- **Part 1 alone — register, do not check.** Removes the grep-to-discover
  problem and lets `docs/directives.md` be derived rather than restated
  ([DP-003](../principles.d/DP-003.md), rung 1), without adding a heuristic. Much the safest subset, and the
  likely answer if part 2 does not convince.
- **Make the syntax unambiguous instead.** Require a sigil, so a directive is
  recognisable without knowing the vocabulary and an unknown name is reportable
  with no heuristic at all. Rejected here as far too large: it breaks every
  existing directive in every record on luria, to fix a failure nobody has
  reported.

## Consequences

If both parts land, a typo is reported at the site with a suggestion, and the
vocabulary has one home that `docs/directives.md` can be generated from. The
cost is a tuned cutoff in the lint and a new report class to keep honest.

If only part 1 lands, the record still gains a single source for the vocabulary
and loses nothing.

If neither lands, this document is the answer to the next person who notices
the missing registry and expects it to be an oversight — which is how it was
found. The measurement is the part worth keeping either way: the naive check is
not merely imperfect, it is 87 to nothing against.
