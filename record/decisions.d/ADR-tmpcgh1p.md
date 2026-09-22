---
status: Proposed
title: 'Unbound relations reach the lint, so an invariant can be declared over a residue'
version: 1
tags:
- record
- ci
date: '2026-09-22'
issue: '#311'
summary: >-
  `unbound-relations` and `unbound-lines` are lint classes, so `lint.baseline`
  can hold a declared invariant to a residue a project has read and accepted.
  This removes the all-or-nothing adoption cost without giving any individual
  row a third reading — `ADR-049`'s two-readings rule is untouched. Rejected:
  an `unbound-ok:` directive, which would retire a row and is the move
  `ADR-049` refused; and closing the issue, which leaves the cost standing.
---

# ADR-tmpcgh1p: Unbound relations reach the lint, so an invariant can be declared over a residue

## Context

A relation that declares an `invariant:` asserts its two ends have something
in common. `reports.unbound_lineage()` finds where they do not.

[#311](https://github.com/dmarx/luria/issues/311) asked for an `unbound-ok:` directive, on the grounds that every other
warning class has a way to say "looked at, deliberate" and this one does not
— which makes an invariant declarable only over a corpus already at zero.
`anthology-of-the-sota#202` is the worked case: declaring `invariant: tags`
on `SOTA.source` surfaced 60 rows, and the sequencing had to be *work all 60
to zero first, declare second*. It worked because the residue happened to
reach zero. Had five been genuinely unbound, the choice would have been
between an all-clear that lies and a report nobody reads.

`ADR-049` had already rejected such a directive: a row has exactly two
readings — the invariant is missing, or the relation is wrong — and never a
third. That rule held for all 60 rows, and [#311](https://github.com/dmarx/luria/issues/311) concedes it, asking whether
it is exceptionless.

**Both sides of that argument missed the same fact.** The unbound findings
were a *report and nothing else*. No lint class, so `lint.fail_on`,
`lint.mute` and `lint.baseline` all passed them by, and declaring an
invariant had no build consequence at all. The question was never whether a
row can be retired; it was that a project could not say anything about the
finding as a whole.

## Decision

**`unbound-relations` and `unbound-lines` are lint classes**, in `FAILABLE`
like every other, fed by `invariants.lines()`.

A project with a residue it has read and accepted declares the invariant and
writes it down:

```yaml
lint:
  baseline:
    unbound-relations: 5
```

Five rows report as standing; a sixth is a violation naming both figures.
The residue lives in `luria.yaml`, where anyone can see it and a reviewer can
ask about it, rather than in a report that says a number nobody can act on.
`baseline` shipped in [#307](https://github.com/dmarx/luria/issues/307) and was not available when [#311](https://github.com/dmarx/luria/issues/311) was written.

**No row is retired, so `ADR-049` stands unamended.** Every row still has
exactly two readings, and a baseline asserts something different from a
directive: not "this row is fine" but "this record has *this many* rows it
has not resolved." One is a claim about a relation, the other a claim about
the backlog — and the second is the one a project actually wanted to make.

**Two classes, not one.** `unbound-lineage.md` already distinguishes them and
says which is weaker: an unbound *edge* is two documents joined directly with
nothing in common, while an unbound *line* is a whole sequence with no value
common to every member — which happens while every single step is expressed,
because a component's intersection only shrinks as the component grows. A
project that wants the strong signal in `fail_on` and the weak one at a
baseline has to be able to name them apart.

## Alternatives considered

- **`unbound-ok:`, as asked.** It would retire an individual row, which is
  exactly the move `ADR-049` refused and for a reason that still holds: a
  directive saying "these two share nothing and that is fine" asserts a third
  reading nobody has produced an instance of. [#311](https://github.com/dmarx/luria/issues/311)'s own candidate —
  `SOTA-060 → LIT-043`, a layer-norm setting sourced from a 3D-parallelism
  paper — was resolved by adding `model-stability` to that paper, a tag that
  is *true*. That is reading one, not a third.
- **Close it and note the absence in the report.** The cheapest option, and
  it leaves the adoption cost exactly where [#311](https://github.com/dmarx/luria/issues/311) found it: an invariant you
  can only assert once you have already fully satisfied it, which is the
  opposite of how warn-first works everywhere else.
- **One class covering both findings.** Simpler config, and it forces a
  project to treat a directly unbound pair and a long line's empty
  intersection as the same severity. They are not, and the report has said so
  since it was written.
- **A `--check` mode on `luria reports`.** Puts a gate in a command whose job
  is to render, and gives a project no dial: it would be fail-or-nothing,
  which is the all-or-nothing problem again with an exit code attached.
- **Status quo.** The findings stay unreachable by every dial the record has,
  and the next project to declare an invariant faces `#202`'s choice with a
  residue that might not reach zero.

## Consequences

**A record that already declares an invariant may see new warnings.** This is
the intended effect and it is not free: `anthology-of-the-sota` goes from a
clean lint to one standing row — `SOTA-036, SOTA-037, SOTA-038, SOTA-279,
SOTA-280, SOTA-281 share no tags across the whole line` — which was in its
report all along and had never been in its lint. Measured, not predicted: 0
unbound relations and 1 unbound line, exactly what the report said.

**The row has to carry its own evidence**, because the lint prints lines and
not tables. Each one names the documents, the field, what declared the
invariant, and what each side actually holds — enough to choose between the
two readings without opening either file.

**Declaring nothing still reports nothing**, silently. A record that has not
said which field its relations mean reads the same as one with no relations
at all, which is what makes the whole feature opt-in.

**This does not answer whether the two-readings rule is exceptionless.** It
makes the question stop blocking adoption, which is what [#311](https://github.com/dmarx/luria/issues/311) was really
about. If a genuine third reading turns up, `unbound-ok:` can be argued on
its own merits, with an instance to argue from.
