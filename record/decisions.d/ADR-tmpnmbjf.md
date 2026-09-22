---
status: Proposed
title: 'luria ack: the code comes from the scan, the reason from a person'
version: 1
tags:
- record
- ci
date: '2026-09-22'
issue: '#308'
summary: >-
  `luria ack` writes an acknowledgement directive at every unacknowledged
  citing site the scan reports, with the code, the directive name and the
  location read from `Scan` and only the reason supplied by a person. It
  refuses over a document in force, a code nothing cites, and a citation
  already covered. Rejected: a `--fix` that writes them in bulk, since a
  generated reason vouches for nothing; putting it in `luria repair`, whose
  contract a judgement cannot satisfy; and an interactive prompt, which no
  CI or agent caller can answer.
---

# ADR-tmpnmbjf: luria ack: the code comes from the scan, the reason from a person

## Context

The acknowledgement directives — `inactive-ok:`, `unresolved-ok:` and their
`-block`/`-file` variants — are the escape hatch under `lint.fail_on`. That
makes them the one place in the record where a mistake is *silent*: a
directive naming a code that does not exist suppresses nothing and reports
nothing, because an unresolvable code inside an HTML comment is not the
finding an unresolvable code in prose is.

They were written by hand, at the citing site, from memory of what the lint
said. Downstream guidance already tried to close this by instruction — *"write
it from the lint's own report, after running it, never from memory of a
document's status"* — which is the right rule and did not hold. Four failures
in one day of filing work on `anthology-of-the-sota`:

1. A stale directive **shipped**, caught a contribution later: the code it
   vouched for was no longer retired.
2. A directive naming **a code that does not exist** — a `LIT` tail crossed
   with a `THEORY` prefix. It passed silently.
3. A directive **stale on arrival**, over a document that was `Active`.
4. A configuration comment citing a **number before it was allocated**.

Every one is a transcription error between a report that already held the
right answer and a file edited by hand.

## Decision

**`luria ack` writes the directive, reading everything but the reason from the
scan.**

    luria ack                                  # what could be acknowledged
    luria ack [ADR-012](ADR-012.md) --reason "..."           # one per citing site
    luria ack [ADR-012](ADR-012.md) --reason "..." --scope file
    luria ack [ADR-012](ADR-012.md) --reason "..." --until 2026-12-01

The code, the directive name, the comment syntax and the line all come from
`ref_status.Scan` and the file itself. Failures 2 and 4 become structurally
impossible: the command cannot name a code the scan has never seen.

**The three refusals are the feature, not the guard rail.** Each of the three
states with no acknowledgement to write fails differently if one is written
anyway, and each now produces a sentence rather than a silent no-op:

- a document **in force** — the directive would be a `stale-directives`
  finding the moment it landed (failures 1 and 3);
- a code **nothing cites** — it would govern nothing (failures 2 and 4);
- a citation **already covered** — a second directive is noise the stale
  check then reports.

**`--reason` is required, and there is no bulk mode.** The reason is the
content: a directive whose justification was generated vouches for nothing,
which is the failure the directives exist to prevent. One code per invocation,
every site of that code, one reason.

**Line scope is the default** because an acknowledgement is a claim about
*that* sentence. `--scope file` is offered rather than guessed: the scan knows
a code is cited three times and cannot know whether that makes the file the
unit. A `-file` directive lands below frontmatter, since a comment above the
opening `---` is not a comment — it is the document's first line, and the
frontmatter every view reads is gone.

## Alternatives considered

- **Better instructions.** Tried, downstream, in these exact words. It
  survived until the fourth error of the same day. `ADR-054` reached the same
  conclusion about a different discipline in the same session: a rule that
  depends on remembering is a rule with a failure rate.
- **A `--fix` on the lint that writes them automatically.** The reason is the
  content. A directive with a generated reason is a suppression nobody
  authored, and the record would be worse off than with the finding.
- **Put it in `luria repair`.** `repair` writes *mechanical* fixes — ones with
  a single correct answer — and its contract is that a second run changes
  nothing. An acknowledgement needs a judgement and a sentence, and a command
  that asks for one cannot satisfy that contract.
- **Interactive by default, prompting for each reason.** The issue leaned this
  way and it is wrong for the callers that exist: a prompt cannot be answered
  by CI or by an agent, which is who writes most of these. A survey that
  prints and writes nothing, plus one explicit invocation per code, gets the
  same one-reason-per-row discipline with no terminal required.
- **A `--reason` that applies to every row at once.** Recreates the
  blanket-silence problem the `-file` variants already risk, with none of
  their visibility — `-file` at least shows up in the report as a file-wide
  exemption.
- **Status quo.** Keep writing them by hand and keep catching the mistakes a
  contribution later, when the fix is an edit to a merged file.

## Consequences

**The command can still write a wrong reason**, and nothing here checks one.
That is the correct residue: what was mechanical is now mechanical, and what
was a judgement is still a judgement, made in one place with the facts in
front of it.

**The comment syntax is a two-way guess** — `<!-- -->` for markdown and HTML,
`#` for everything else. A record whose `code.globs` name a `.js` or `.rs`
file gets `#`, which is wrong, and wrong *visibly*: the directive does not
parse and the finding stays. Widening it is a config question, not a default.

**A second directive over an acknowledged site is refused, so the command
cannot broaden an existing acknowledgement.** Editing the directive that is
already there is a hand edit, which is right — changing what a suppression
vouches for is the judgement, not the mechanics.

Run on luria's own record the survey listed five unacknowledged codes, all
fixture and illustrative numbers, and writing one of them produced exactly
the directive a person would have written, at the right indent, in the right
comment syntax, clearing the row.
