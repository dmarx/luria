# Importing an existing corpus

[Adopting Luria](adopting.md) covers a project whose *code* already exists.
This page covers one whose *material* already exists — a YAML registry, a
spreadsheet, a wiki export, a directory of notes — and needs to become a
record without losing what it already knew.

The mechanics are unremarkable: write a script, emit markdown with
frontmatter, run `luria index`. What is worth writing down is everything the
first attempt gets wrong.

## Expect the import to find things

This is the part worth anticipating, because it changes what "done" means.

Structured data tolerates defects that documents do not. A duplicate row is
invisible; two files cannot share a name. A dangling identifier in a field is
inert; a code that resolves to nothing is a reported finding. A status column
that only ever holds one value looks like a working schema right up until
something counts the distinct values.

One 118-entry corpus produced, on the first clean run: two entries with no
identifier at all, one entry present twice under a single identifier with two
different bodies, three cross-references naming entries that were not in the
corpus, a status field with one distinct value across 119 records, and a
retirement pointing at a successor that had itself been retired.

None of that was introduced by the import. All of it had been true for years
and unobservable, because nothing could resolve a reference or count a column.
Budget time to *triage* what the import surfaces, and resist fixing it inside
the migration — a defect discovered during a bulk transform should become a
finding, an acknowledgement, or a decision, not a silent correction.

## Commit the script

Keep the transform in the tree rather than running it once and deleting it. A
few hundred generated documents are unreviewable one at a time; the thing that
wrote them is reviewable in an afternoon, and every judgement it makes — a
category mapping, a status derivation, the individual entries where automation
was overridden — is then a diff a reviewer can argue with.

Put the judgements in data where you can. A mapping table beside the script
reviews better than the same mapping expressed as a chain of conditionals.

## `date:` is the filing date

The single most common import bug, because imported material always carries
its own dates and putting them in `date:` looks obviously correct.

It is not. `date:` is when the entry was *filed into the record*, and the
staleness reporting measures from it — so publication dates make every
`Proposed` entry look years overdue for a decision the moment it is imported.
A warning that is permanently wrong is the kind that gets a check switched
off, which costs more than the field was worth.

Put the filing date in `date:` — everything imported on one day genuinely was
— and give the domain date its own field:

```yaml
date: '2026-08-24'        # when this entered the record
published: '2014-12-01'   # what the material is about
```

Frontmatter beyond the fields Luria reads is yours; nothing objects to it, and
it is the right home for the source's own vocabulary.

## Derive only what you can defend

Automation will happily assign every optional field, and the marginal ones are
where it invents claims.

A category mapping scored primary and secondary tags the same way, and one
paper came out filed under *model architecture* because the generic word
`neural-networks` appeared in its keyword list — as it does in a third of the
corpus. Every vague term in a source vocabulary maps *somewhere*. The primary
assignment survived review; the secondaries were noise on exactly the browsing
pages the exercise existed to make useful.

Emit the fields the material actually determines. Preserve the source's own
terms verbatim in a field of your own, so nothing is lost and a human can add
the judgement later:

```yaml
tags: [model-stability]                    # the controlled vocabulary
keywords: [normalization, neural-networks] # what the source said
```

## Compute statuses before you write bodies

If your import writes acknowledgement directives — and a retirement that names
its successor should, because that citation points at something not in force
by construction — it needs to know the target's status first.

A directive on a target that turns out to be in force is itself a finding
(`stale-directives`), so a single pass that decides status and emits prose
together will produce annotations that immediately report themselves. Resolve
every entry's status first, then write the documents.

## Quote everything

Imported titles are somebody else's prose, and it contains colons, apostrophes
and unicode. A generator that assumes plain scalars will produce YAML that
parses as something else — usually a mapping, occasionally a number:

```yaml
title: 'Adam: A Method for Stochastic Optimization'
```

Watch the source's own typing too. Identifiers that look numeric may arrive
already coerced — an unquoted `1412.6980` in the source YAML reaches you as a
float, and one with a trailing zero loses it silently. Validate the shape
against a pattern and fail loudly rather than writing a plausible wrong value.

## Placeholder codes in templates

A scheme's `_template.md` needs an example reference, and reaching for a real
one makes the template cite it — so a template illustrating citation syntax
with a retired document generates a retired-citation finding against itself
every time the report runs.

Use a code the scheme will never allocate and acknowledge it once at the top
of the file:

```markdown
<!-- unresolved-ok-file: LIT-000 — the placeholder a new note replaces -->
```

For examples in *prose* rather than in your own scheme, the
[fixture codes](directives.md#fixture-codes) exist for exactly this and cannot
collide with anything.

## Afterwards

Expect the first `luria lint` to be noisy, and read the noise as the point.
Leave `[luria.lint] fail_on` empty while you work through it: acknowledge the
citations that are deliberate, fix the ones that are defects, and file
decisions for the ones that are neither. Promote a class into `fail_on` once
its report is clean and you want it to stay that way.

Two questions worth answering explicitly before you call the migration done:

- **What happens to the old source?** Freeze it with a note saying so, or
  delete it and rely on git. What does not work is leaving it live, because
  two structures describing one corpus drift the moment either is edited.
- **What still reads it?** A build step or a downstream consumer pointed at
  the old artifact will keep working and keep serving a snapshot. Decide
  whether it moves to the record or retires, and record which.
