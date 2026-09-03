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
# `Superseded — by [ADR-tmpvs0gt](ADR-tmpvs0gt.md)` and leave its body intact. When the
# choice stands and only a REASON was wrong, correct this body in place and
# bump `version:` below — the rule objects to silent revision, not to editing.
status: 'Active'

# What the index shows in place of the code. Repeat it as the body's `# ADR-tmpvs0gt:`
# heading — someone reading the file alone needs one — and `luria lint` checks
# that the two agree, because two copies of a string is a projection that drifts.
title: 'A workflow file cites a decision by number or by prose, never by a temporary code'

# Which revision of this decision's claim you are reading. Standard frontmatter
# for every scheme, and it moves rarely here: a decision that CHANGES is
# superseded by a new one, not edited. Bump it when the same choice is restated
# more broadly — scope widened, wording generalized — and say what changed in a
# `history:` entry. Shown in the index only when it is not 1.
version: 1

# Browsing categories, pushed down onto the decision itself. One is normal; more
# than one is fine. A tag not listed in tags.yaml still works.
tags:
- ci
- mechanism

date: '2026-09-03'

# Optional. The issue(s) this decision came from: '#123'.

# Optional but wanted: the one-blob description the index table shows. Without
# it the table falls back to the title, which is usually too terse to browse by.
# Say what was decided AND what was rejected — the index is read far more often
# than the decision, and "why not the obvious thing" is what people come for.
# This field is prose, so it carries links like any other prose; the rest of the
# frontmatter is data and stays plain. (`origin:` on a principle is
# prose for the same reason — the generator renders it.)
summary: >-
  The first merge under [ADR-068](ADR-068.md) left the default branch red with nothing
  wrong in the record: `luria concretize` numbered the decision and rewrote
  its temporary code everywhere the code globs reach, including a comment
  in `.github/workflows/ci.yml`, and GitHub refuses a push from the
  workflow token that modifies a workflow file. A workflow file cites a
  decision by its number or by prose; a temporary code there is a lint
  error naming that remedy. Rejected: a concretizer that skips workflow
  files (leaves a dangling code the record can never resolve), dropping
  workflow files from the code globs (loses the retired-citation check on
  the comments that most need it), and a token with workflow permission (a
  credential the record's correctness would then depend on).
  alternatives that lost. Written to be read in a table row.
---

# ADR-tmpvs0gt: A workflow file cites a decision by number or by prose, never by a temporary code

## Context

A merge-allocated decision carries a temporary code until the push job on
the default branch numbers it ([ADR-049](ADR-049.md)). `luria concretize` then rewrites
the code everywhere the record and the code globs reach — source, tests,
the composite actions, the workflow files — so that no second spelling of
the document survives ([ADR-040](ADR-040.md)). The workflow files are in the code globs
on purpose: their comments cite decisions, and the reference lint should
see a retired one there like anywhere else.

GitHub refuses a push made with the workflow token that creates or updates
anything under `.github/workflows/`, whatever else the commit carries. So
the first merge under [ADR-068](ADR-068.md) — which cited its own temporary code from a
comment in `ci.yml`, as any pending decision would — had its generation
commit rejected whole: views, rename and repairs together, and the lint
job that `needs:` it never ran. The record was correct; the default branch
was red; the only fix was a second pull request.

The hazard is exact. A temporary code is the one kind of citation the job
must later rewrite, and a workflow file is the one place it can never
write. Nothing else in the tree has both properties.

## Decision

**A workflow file cites a decision by its number, or by prose.** A
temporary code under `.github/workflows/` is a `luria lint` error, with
that remedy in the message: cite the number once the decision has one, or
say it in prose. A pull request that cites its own pending decision from a
workflow comment writes the prose form; the number can replace it in a
later change, or not.

This is a lint error rather than a report because the violation is
always wrong — the job's push will be refused — and the fix is mechanical.
It is a lint rather than a change to the concretizer because every
alternative that keeps the code out of the commit leaves it in the file.

## Alternatives considered

- **Have `luria concretize` skip `.github/workflows/`.** The push
  succeeds, and the workflow file keeps a code that names a document
  which no longer exists under that name — a reference the lint reports
  as unresolvable on every run until someone edits the file by hand, and
  `luria concretize --check` has to be taught the same exception. A
  guard that moves the failure from the push to the lint, permanently.
- **Drop workflow files from the code globs.** The concretizer leaves them
  alone, and so does the reference lint: a workflow comment citing a
  decision that has since been superseded stops being caught, in the
  comments that explain why CI is shaped the way it is.
- **Push with a token that has `workflows` permission** — a personal
  access token or a GitHub App installation. Works, and makes the
  record's correctness depend on a credential someone has to create,
  scope, store and rotate; a fresh clone of the scaffold would fail until
  they did. The workflow token is the one every repository already has.
- **Commit workflow files in a separate step, or not at all.** Same as
  the first alternative with more moving parts.

## Consequences

An author citing a pending decision from a workflow comment writes prose
— "the amendment to [ADR-029](ADR-029.md) on where views land" — where a source file
would carry the code. The scaffold's workflow does the same. The guard
fired once on the real case before the fix, naming the file, the line and
the code.

The generation job's commit still touches workflow files whenever a
*numbered* citation there is retired or renamed by a migration
([ADR-040](ADR-040.md)); that push fails the same way, and the migration's pull request
is where the file is edited by hand. This decision covers the temporary
code, which is the case that recurs.
