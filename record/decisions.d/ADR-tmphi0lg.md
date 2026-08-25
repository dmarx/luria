---
status: Active
title: A principle is written as a value, unless it is actually a rule
version: 1
tags:
- record
- process
date: '2026-08-25'
summary: >-
  A principle drafted as "a record must not constrain the project it records"
  could only be satisfied or violated, which loses the state a value spends
  most of its life in — partly met, and moving. Rewritten as "meet the project
  where it is" it kept the same content and gained that reading. Principles
  are written in the aspirational voice by default; the constraining voice is
  reserved for the ones that genuinely are rules, which this record has two
  of. Rejected: requiring the positive voice everywhere, and adding a lint.
---

# ADR-tmphi0lg: A principle is written as a value, unless it is actually a rule

## Context

A principle about environment coupling was drafted as **"a record must not
constrain the project it records"** and reviewed as a prohibition wearing a
principle's clothes. Rewritten as **"meet the project where it is"**, with the
same evidence and the same corollary, it read as something to work toward.

The rewrite was not only a matter of tone. The negative form failed a case
the positive one handles: a self-hosted forge gets a record that works and one
field to fill in by hand. Under *must not constrain*, that is a violation and
has to be argued away. Under *meet the project where it is*, it is the
aspiration partly met, which is what it is.

That is the general shape. **A rule has a boundary you are on one side of. A
value has a direction you are somewhere along.** Stating a value as a
prohibition collapses the second into the first, and the state it deletes —
partly met, and moving — is where a value spends most of its life.

The corpus had already worked this out without saying so. Of fourteen
principles, twelve are positive: an imperative (`Fire before trusting`,
`Culture must be compiled`, `One decision, one thing`), or a diagnosis paired
with a remedy (`A hand-maintained projection of a source of truth will drift —
derive it`). Two are negative — `No silent refusal` and `No private brains` —
and both are genuinely rules: there is a line, and crossing it is the failure.
The pattern was right and unstated, which is the condition where the next
draft goes the other way. One just did.

## Decision

**Write a principle in the voice of what it is.**

The default is aspirational, because most principles are values: state what to
move toward, and let the body carry what goes wrong when you do not. A title
that reads as a direction is also more usable at the moment of citation —
somebody deciding between two designs can ask which one moves toward it, where
a prohibition only answers whether either is forbidden.

**Use the constraining voice when the principle is a rule.** `No silent
refusal` should not become "prefer to explain what was refused"; the whole
content is that there is no acceptable case. Softening a real rule into an
aspiration is the same error in the other direction, and it is worse, because
it makes a hard line look negotiable.

Three shapes, all legitimate, and the record already uses all three:

| shape | example |
|---|---|
| value, as an imperative | `Meet the project where it is` |
| observation, with the remedy attached | `A hand-maintained projection of a source of truth will drift — derive it` |
| rule, stated as a boundary | `No silent refusal` |

The test when drafting: **can this be partly met?** If yes, it is a value and
wants the aspirational voice. If the only states are satisfied and violated,
it is a rule and should say so.

## Alternatives considered

- **Require the positive voice everywhere.** Simpler to state and it would
  have forced `No silent refusal` into a softer sentence than the thing it
  means. A convention that mangles its own best examples is not ready to be
  a convention.
- **Leave it to taste.** What was in force until now, and it worked for twelve
  principles before producing one that had to be rewritten after review. The
  cost of leaving it unstated is not high — a draft and a rewrite — but the
  rewrite happened because a reviewer caught it, which is the surface this
  record elsewhere declines to rely on.
- **Lint it.** The obvious next rung, and it does not reach. Register is not
  regex-judgeable: a pattern for `must not`, `never` and `no` fires on both
  principles where the negative voice is correct, and misses a prohibition
  phrased positively (*"always name the reason"* is a rule). A check wrong
  more often than right gets switched off, which is the same reasoning that
  keeps `narrow-titles` a warning over a vocabulary the project supplies.

## Consequences

This is a convention that stays a convention, which sits against the habit of
walking one up to a mechanism when it matters. The exception is stated rather
than left implied: the judgement is about voice, a machine cannot make it, and
a bad check here would cost more than the mistake it prevents. What can be
done instead is cheap — the question *can this be partly met?* is in the
principle template, where a drafter meets it.

Two existing principles were read against this and left alone. `No silent
refusal` and `No private brains` are rules and keep their voice. Nothing in
the corpus needs rewriting, which is the expected outcome when a decision
records what was already being done.
