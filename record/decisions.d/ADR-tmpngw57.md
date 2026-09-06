---
status: Active
title: A field can be required by another field's value
version: 1
tags:
- contract
- config
date: '2026-09-06'
summary: >-
  A record can state what it believes and had no way to state what would
  change its mind, so provisional documents accumulate with nothing saying
  what they are provisional pending. `required_when` demands a field only
  while another field holds one of a listed set of values — one field, one
  set, no expression language, because the value of the rule is that it is
  legible in the line that declares it.
---

# ADR-NNN: A field can be required by another field's value

## Context

Every scheme has a status vocabulary and a lint that checks it. Nothing
anywhere records what would move a document from one status to another.

The consumer project measured what that costs. Across 144 practices, four
stated a promotion condition; all four stated it in prose; none of the four
was re-read when the evidence arrived. Eight practices sit at `Proposed` and
one at `Deferred`, so more than half the provisional entries in that record
say they are provisional and say nothing about what provisional is waiting
for. A reader cannot tell a document genuinely blocked on a specific result
from one filed hesitantly and forgotten, because the two render identically.

Then the predicted thing happened. Two practices filed a day apart carried
near-identical prose conditions — *promote on an independent result*. One
paper satisfied both, on the same day. Only one was acted on, and only
because a person happened to be reading both bodies that afternoon: on
inspection the paper *evaluated* one of them and merely *cited* the other.
The condition was invisible until somebody stumbled over it, and once found
it turned out to be counting papers when what mattered was what the papers
were about.

Only the first half is machinery's to fix. But the first half is what makes
the second invisible: a condition nobody rereads is never revised.

## Decision

A field may be required conditionally on another field's value.

    [luria.schemes.SOTA.fields.promote_when]
    required_when = { status = ["Proposed", "Deferred"] }

`required` stays the unconditional flag and the two are exclusive — declaring
both is a config error, because the condition would say nothing.

Three consequences of putting it where it is:

**It is a property of the field, not of the status.** `required_when` reads
as "this field is meaningful only while something is pending", which is a
fact about the field, and it generalises to conditions with nothing to do
with status. The `fields` table already existed to declare a field's shape
and type; a rule about when the field applies needs no type at all, so a
table declaring only `required_when` is a plain field — any truthy value,
demanded under its condition.

**Every check reads it through one method.** `Field.demanded(meta)` replaces
every direct read of `field.required`. A conditional requirement honoured by
one check and ignored by the next is exactly the failure the compiled
contract ([#141](https://github.com/dmarx/luria/issues/141)) exists to end, and the fix is that there is one place to
ask.

**The comparison is normalised, not literal.** A `status:` carrying a
qualifying note is still that status, and the note is its own field
([ADR-072](ADR-072.md)), so `Proposed — pending a
replication` matches `Proposed`. Comparing raw strings would have read a
qualified status as some other status and exempted the document silently,
which is the class of bug this decision exists to remove rather than
introduce.

## Alternatives considered

**Hang the requirement off the status vocabulary** — `statuses.yaml` naming
which fields each status demands. Reads well for exactly this case and badly
for every other: `statuses.yaml` is a vocabulary file, and making it a
requirements file too gives it two jobs. It also puts the rule somewhere the
person declaring the field would not think to look.

**A general predicate language** — negation, conjunction, comparison across
fields. Rejected. The entire value of this rule is that a reader sees it in
the line that declares it; a config that can state arbitrary predicates is
one nobody reads at a glance. One field against a set of literal values is
enough for every case anyone has produced. A second real case can argue for
more, which is a better way to learn the shape than guessing at it now.

**A machine-checkable condition** — `promote_when = { independent: 2 }`,
verified against the reference graph. Tempting and wrong. A condition a
machine can check is necessarily a *count*, and counting is the exact error
that produced this decision: the two practices' conditions were satisfied,
by the letter, by a paper that did not bear on one of them. A condition that
can be met automatically is a condition that can be met accidentally.

**Require the field of every document, not just the conditional ones.** Most
documents would carry a key with nothing to put in it, and a field that is
usually empty is a field readers learn to skip.

## What this does not do

It cannot check that a condition is a *good* condition — that it names a kind
of evidence rather than a quantity of it. Nothing mechanical can, and a check
that tried would ratify bad conditions by passing them. What it does is make
the condition exist, as a field, on the document, where the next person to
touch that document reads it without needing the coincidence.
