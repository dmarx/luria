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
# in `superseded_by: ADR-tmpq8zru` (a reference field: checked, resolved, an edge
# the index and the site render), and leave its body intact. A qualifying
# note for anything the field cannot say goes in `status_note:` — prose,
# like `summary:`, so a code in it is a citation. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: Proposed

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpq8zru:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'The TOML crossing carries comments, because a comment is not a value'

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

date: '2026-09-14'

# Optional. The issue(s) this decision came from: '#123'.

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
summary: >-
  `luria upgrade yaml` parsed a TOML config with `tomllib` and wrote the
  values, which is right — a regex in a `uid` does not survive a byte copy.
  But a config is documented in its comments, and `tomllib` never sees them:
  the crossing dropped 273 comment lines in one record and 85 in another,
  and reported only what it had folded. Comments are now carried to the key
  they documented, the vocabulary files are round-tripped rather than
  re-parsed, and the handful whose key does not exist on the far side are
  printed in full. Rejected: leaving them in git history, which is not where
  anyone reads a config.
---

# ADR-tmpq8zru: The TOML crossing carries comments, because a comment is not a value

<!-- inactive-ok-file: ADR-098 — Proposed. Named as the decision whose
     crossing this one repairs; the citation is to its reasoning, not a claim
     it is settled. -->

## Context

`luria upgrade yaml` is the only way across the boundary [ADR-098](ADR-098.md) drew: the
new version does not read TOML at all, so a record that has not crossed
cannot be linted, indexed or repaired. Every project on luria runs it exactly
once, and what it does is what that project's config becomes.

It parsed with `tomllib` and wrote with a YAML emitter, for a good reason its
own docstring gives: a regex in a `uid` does not survive being moved as
bytes, because the two formats escape differently. Every value has to be
re-encoded by a writer that knows its own rules.

Comments are not values, and nothing carried them. `tomllib` returns a dict;
the comments are gone before any writer is chosen. The crossing printed what
it folded and what nothing read any more, and said nothing at all about the
prose it had just dropped.

The amounts are not incidental. This record's own config lost 85 comment
lines when it crossed. `anthology-of-the-sota`, which had not crossed yet,
carried 273 — why each reference field is declared rather than merely
required, what `promote_when` is for, why `contested_by` is held to the same
standard as `source:`, what each of the two chains is. That is the reasoning
a config needs most, because a config's values say what and almost never why.

Nor is the loss confined to the TOML. Each scheme's vocabulary file was read
with `yaml.safe_load` before being inlined into `vocabularies:`, so the prose
above the thirteen topics went the same way.

## Decision

The crossing carries comments.

A comment block is a run of comment lines plus the path of the first key or
table that follows it — that is all `toml_comments.blocks` recovers, and all
it needs to. The values still go through `tomllib`; the prose is attached
afterwards, to the key it was written above, through the ruamel API
`yaml_edit` already wraps.

Three details are load-bearing:

**The document is round-tripped once before the comments go on.** The values
come back from `tomllib` as plain dicts, and a plain dict has nowhere to hold
a comment. Dumping and reloading is what turns them into structures ruamel
can annotate.

**A dotted key is a path.** `uris.title = "..."` nests exactly as
`[remotes.ARXIV.uris]` plus `title` would. Read as a single key named
`uris.title`, its comment lands nowhere — which is how the real config's one
stranded block was found, and it was the only one.

**Prose that cannot be placed is printed in full, not counted.** `tags`,
`statuses` and `tag_groups` do not exist on the far side: each splits into a
vocabulary named centrally and a field that names it. Comments on those
follow the field where the mapping is unambiguous; anything left is printed
whole, because a count tells you something was lost without telling you what,
which is the failure this whole change exists to stop ([DP-1](../principles.d/DP-001.md)).

## Alternatives considered

- **Leave them in git history.** The TOML is not deleted by the upgrade, and
  `git show` can recover any of it. But a config is read in the editor that
  has it open, and reasoning that requires knowing to look for a deleted file
  is reasoning nobody reads. The comments were written next to the keys
  because that is where they work.
- **Move the prose into `blurb:` fields.** This is what luria's own config
  did after it crossed, and for vocabulary entries it is the right answer —
  a blurb is structured, and it renders into the docs. It does not generalize:
  there is no field on `references.contested_by` whose value is "why this is
  held to the same standard as `source:`", and inventing one for every key
  that might want a paragraph is a schema for prose.
- **Copy the comment bytes along with the value bytes.** Rejected for values
  for a reason that does not apply to comments — escaping — but the shape is
  tempting because it is one pass. It would mean a TOML-shaped emitter
  writing YAML, which is how the escaping bug gets in through the back door.
- **Status quo.** Every project on luria crosses this boundary exactly once,
  and each one silently loses everything it wrote about its own config. Two
  had already paid it when this was written.

## Consequences

The anthology's crossing now carries all 42 of its blocks; before the
dotted-key fix it carried 41 and reported the 42nd. Its `luria.yaml` has 375
comment lines against the TOML's 273 — the difference is the vocabulary-file
prose, which now survives too.

A paragraph break inside a block needed one more thing: ruamel writes an
empty comment line as an empty *line*, which is not a comment, so the prose
below it detached from the key it documented. `toml_comments.rejoin` puts the
bare `#` back. Cosmetic in a ten-line config and not in a 490-line one.

`convert_config` returns a fourth value, which is a signature change to a
function two callers use, both in this repository.

What this obliges: the carry is best-effort by construction, and it says so.
A record whose TOML puts comments somewhere this does not look — inside a
multi-line array, say, where a comment documents an element rather than a
place — still loses them. That is a narrower hole than "all of them", and the
report is what makes it visible rather than silent.
