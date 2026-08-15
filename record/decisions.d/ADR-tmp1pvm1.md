---
status: Active
title: Titles in a transferable scheme are checked against the project's own nouns
version: 1
tags:
- record
date: '2026-08-15'
summary: >-
  A principle stated about the artifact it was first noticed on is one nobody
  applies to the next artifact, and nothing catches it: the document stays true,
  renders, and passes every check while quietly never being cited. The
  `narrow-titles` class reports a title that names one of the project's own
  concrete nouns, in a scheme that opted in with `titles_generalize = true`.
  **Luria ships no vocabulary** — `[luria.lint] narrow_terms` is the project's
  list, and empty means the class never fires, so a project that has not thought
  about this is told nothing rather than told it is clean. Titles only:
  body-linting was measured at 5 of 6 caught against 8 false alarms in 15, and a
  check wrong more often than right gets switched off. Fail-open by choice, and
  another sense is acknowledged with `broad-ok:` rather than by shrinking the
  vocabulary, which would stop the word working everywhere else. Rejected:
  shipping a default noun list (someone else's vocabulary with the authority of
  a default), inferring narrowness from abstraction (fires on exactly the
  phrasings worth keeping), and requiring two worked instances before a
  principle may claim breadth (wants the citation graph, not a title scan).
---

# ADR-tmp1pvm1: Titles in a transferable scheme are checked against the project's own nouns

## Context

A decision is *about* something specific; naming that thing in its title is
correct. A principle is the opposite — and the failure mode is silent.

A principle stated about the artifact it was first noticed on stays true, keeps
rendering, and passes every check this project has. It simply stops being
reached for, because it reads as a rule about a subsystem the next reader is not
in. Downstream, one principle sat saying "a **tool** that explains its refusal
teaches its own model" while six non-tool mechanisms refused silently in a single
day — a guard, a filter, a migration, a DOM query, two path predicates — and not
one of them was a tool, so the principle governing all six was never cited.

Nothing here could see that. The template asks for breadth in prose; prose does
not check.

## Decision

**A new warning class, `narrow-titles`**, reporting a title that names one of
the project's own concrete nouns — in a scheme that asked to be checked.

Two config surfaces, deliberately separate:

- `[luria.lint] narrow_terms` — the project's nouns. One list, because the
  vocabulary belongs to the project, not to a document family.
- `[luria.schemes.X] titles_generalize` — per-scheme opt-in, because *which*
  families claim to transfer is a question only the project can answer. False
  everywhere by default, the shipped ADR scheme included.

**Luria ships no vocabulary, and that is the load-bearing part.** An empty
`narrow_terms` means the class never fires and never appears — a project that
has not thought about this is told nothing, rather than told it is clean. A
shipped list would be some other project's vocabulary wearing the authority of
a default, and the nouns are exactly the part that cannot generalize.

**Titles only.** Measured on the corpus this came from, a title check catches
roughly a third of the genuinely narrow principles — including cases whose
narrowness lived entirely in the body, which it misses. Its value is
prospective: the title is the line an author writes first and every citation
repeats, so it is the cheapest place to be told "widen this".

**Fail-open.** A noun missing from the vocabulary ships a narrow title
unflagged. A miss costs a review comment; a false alarm costs trust in the
check, and the polarity is chosen rather than inherited.

**Another sense is acknowledged, never removed from the vocabulary.** A
`broad-ok: overlay — a verb here` comment exempts that document; deleting the
word from `narrow_terms` would stop it protecting every other document. Same
directive grammar as the `inactive-ok:` family, through the same parser — a new
directive is a name, not a new syntax.

## Alternatives considered

- **Ship a default vocabulary.** Convenient and wrong: the nouns are the one
  part of this that is purely local. A default would fire on projects it does
  not describe and teach authors to distrust the check.
- **Lint the body, not the title.** Measured before being rejected: 5 of 6
  narrow documents caught, but 8 false alarms among the 15 that were fine. A
  check wrong more often than right will be switched off, and deserves to be.
- **Infer narrowness from abstraction rather than a word list.** Fires on
  titles like "One authoritative implementation" — exactly the phrasing worth
  keeping. Polarity matters more than coverage here.
- **Require two worked instances before a principle may claim breadth.** The
  sharper rule, and it needs the citation graph rather than a title scan.
  Deferred, not rejected — it belongs with the reporting verbs.
- **Do nothing; catch it in review.** What the template already asks for. It
  caught neither of the two documented cases, over months.

## Consequences

- **A clean run means "the title is reusable", never "the principle is
  general".** The vocabulary is a symptom detector: renaming "toolbar" to
  "mechanism" satisfies it without broadening anything, and an all-abstract
  title can still be parochial. The check is worth its cost anyway, because it
  fires at the moment of writing.
- **Nothing changes for existing adopters.** No vocabulary, no opt-in, no class
  — verified by a test that asserts the section is absent rather than empty.
- **The class is failable** like every other, so a project that wants it
  enforced names it in `fail_on`.
