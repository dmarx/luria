---
status: Proposed
title: 'A propose mode may search for edits, reading back cautious and brave consequences'
version: 1
tags:
- record
- mechanism
date: '2026-11-01'
summary: >-
  A new command, `luria propose`, runs logic programs that may use what
  [ADR-127](ADR-127.md) keeps out of the core: choice rules, integrity constraints and
  `#minimize`. It never reads back "the model found". It reads back the
  cautious consequences (true in every optimal answer), which it offers to
  apply, and the brave ones (true in some), which it offers as a choice.
  Both are functions of the sources, so [ADR-127](ADR-127.md)'s reason for one answer
  set still holds. It writes a drafts file and never a source. Lint, views
  and `logic.derive` keep the one-answer-set rule unchanged. The first
  program fills an empty vocabulary field from the graph. Rejected:
  keeping edits by hand, taking the first model, pinning a seed or taking
  the least model, writing the search in Python or SQL, and putting
  proposals into lint.
influenced_by:
- ADR-127
- ADR-131
---

# ADR-tmplnpoe: A propose mode may search for edits, reading back cautious and brave consequences

## Context

[ADR-127](ADR-127.md) moved luria's graph decisions into clingo and kept them to
stratified Datalog. `logic.solve` refuses any program with other than one
answer set, because "a generated view that depended on which model the
solver found first would not be a function of the sources". That rule is
right for what it governs: lint findings and views. It also leaves clingo's
other half unused. Choice rules, integrity constraints and optimisation
search for an assignment that meets constraints; they do not derive one.

Records keep needing that search, and today a person does it by hand:

- **Filling a field from the graph.** On 2026-11-01 dmarx/nucleation made
  `line:` required for CASE and inferred the nine missing values, using a
  SQL query over `luria export` and then reading each candidate
  ([NUC-ADR-067](https://github.com/dmarx/nucleation/blob/main/record/decisions.d/ADR-067.md)). The owner asked for that to be mechanical, "maybe even an
  UPDATE statement".
- **Repairing an invariant finding.** The question there is the fewest tag
  or line additions that would bind a chain's unbound edges and lines.
- **Clearing a credence check** ([ADR-131](ADR-131.md)'s reported patterns): the fewest
  status changes that would clear it.

The experiment filed with this decision (`experiments/asp_propose/`, and its devlog entry
"Proposals from clingo: the line inference as choice, constraints and
optimisation") fired the first case on nucleation, with those nine values
removed again:

- seven values are cautious, and all seven match the hand assignment;
- one document, [NUC-CASE-151](https://github.com/dmarx/nucleation/blob/main/record/cases.d/CASE-151.md), is brave only: a real choice between two lines;
- one, [NUC-CASE-014](https://github.com/dmarx/nucleation/blob/main/record/cases.d/CASE-014.md), has no evidence and is reported as such.

The JSON was byte-identical across four seeds and under four-thread
parallel search.

## Decision

**A second class of program, run by a second command.** `luria propose
NAME` runs a program from `luria/logic/propose/NAME.lp` over the record's
facts. Such a program may use choice rules, integrity constraints and
`#minimize`. It is solved by a new `logic.consequences(mode)` that accepts
only the cautious and brave enumeration modes under `--opt-mode=optN`. That
function exists so the rule is visible: a propose program is read back as a
set of consequences, never as a model. `logic.derive`, every `.lp` file
under `luria/logic/`, lint and the views keep [ADR-127](ADR-127.md)'s rule as it stands.

**What it prints is a proposal, in three parts:**

- **`apply`**: atoms in every optimal answer. Each one is safe to write.
- **`choose`**: atoms in some optimal answer but not every one. These are
  for a person, and nothing writes them unasked.
- **`no_evidence`**: entities the program had nothing to go on for. A
  program must derive this case explicitly, so silence never reads as
  agreement ([DP-015](../principles.d/DP-015.md)).

The proposal is written as a drafts file. `luria propose` never edits a
source.

**Applying a proposal** is the drafts path's job, not this command's.
`luria relate --draft` writes reference fields only, so the drafts file
gains a `values` list: source, field and value, applied through
`field_edit.add_to_field` to a `many` vocabulary field the scheme declares,
and refused for anything else, as relate refuses today. Only `apply`
entries are written into it by default; `--with-choices` adds the `choose`
entries as comments for a person to uncomment.

**The first program, `fill_field`,** takes a scheme and a field as clingo
constants. For each document of the scheme whose field is empty:

- its candidates are the values of its neighbours by any declared
  relation, and, recursively, what an empty neighbour may take;
- it takes at least one candidate where it has any;
- every neighbour with a value must share one with it;
- the number of values is minimised.

That constraint is one reading of what a field like `line` means. It is
the program's, not luria's: another reading is another program.

**Unsatisfiable is a finding, not a crash** ([DP-001](../principles.d/DP-001.md)). The command says which
constraints could not all be met. Where clingo's unsatisfiable core is
available, it names the documents involved.

**Determinism is tested, not assumed** ([DP-006](../principles.d/DP-006.md)). Each shipped propose program
has a test that solves it on a fixture under several seeds and under
parallel mode, and asserts identical output.

## Alternatives considered

- **Keep doing it by hand, with a query beside it.** This is what nucleation
  did. It costs a reading per candidate on every record, every time, and
  the judgement it needs is spent mostly on the cases the constraints
  already settle. Here those were seven of nine.
- **Take the first model clingo finds.** It is what a naive call returns,
  and it is exactly what [ADR-127](ADR-127.md) forbids. The result would depend on search
  order.
- **Pin a seed, or take the lexicographically least optimal model.** Both
  are deterministic on one machine. But the answer then depends on the
  solver's version and heuristics, not on the record, and a choice would
  be presented as if it were settled. Cautious and brave consequences say
  which atoms are settled and which are not.
- **Write the search in Python or SQL.** One grouped count gets candidate
  lists, which is what nucleation's query did. Chaining through empty
  neighbours, the sharing constraint and minimality together are a search,
  and luria would be hand-rolling a solver: the alternative [ADR-127](ADR-127.md)
  rejected.
- **Make proposals lint findings with fixes attached.** Lint must stay one
  answer set and must fail on what is always wrong. A proposal is neither.
- **A separate engine.** The DuckDB experiment in PR 391 found no
  advantage for this. Its value is a query surface, not search.

## Consequences

- **luria has two kinds of logic program.** The directory and the solving
  function keep them apart, and a reviewer can tell which rule a file
  answers to by where it lives.
- **The cost of optimisation is unbounded in principle.** Proving optimality
  and enumerating consequences can be slow on large search spaces, so the
  command takes a time limit. A run that hits it says so and proposes
  nothing, rather than proposing from an unproven optimum. On nucleation
  the first program takes about 6 s, mostly building the facts.
- **The modelling choices are visible and reviewable**, as the
  sharing-constraint reading of `line` is. A record that wants another
  reading writes or asks for another program.
- **Follow-ups this implies:**
  - the `values` list in drafts files;
  - a second program for invariant repairs (`unbound_edge` and
    `unbound_line`), to check that the class generalises beyond one field;
  - possibly a `proposals:` block in `luria.yaml`, once a record has more
    than one standing use.
- **Kill criteria, stated before the work, as in [ADR-127](ADR-127.md):** withdraw the mode
  if any shipped program's output differs across seeds or parallel mode on
  a real record, or if owners reject most `apply` entries on real records.
  A program whose settled answers are mostly wrong is modelling the field
  badly, and luria should not keep offering it.
