<!-- docs/paper/07-forgetting.md -->

# Forgetting without deletion

Funes's tragedy was not memory but the absence of abstraction. A corpus that
keeps every entry at equal weight is in his position, and the third
architectural question, after what an entry is and what it rests on, is how the
corpus is to forget.

## Retirement is a way of forgetting

The first thing to say is that forgetting here is not deletion. An entry that
is wrong, replaced, or no longer wanted is *demoted*: its standing changes, and
its body and reasoning remain. The practice is stated as a rule in a downstream record that uses the
framework for a reading list, "retire by status, never by deletion", and the
vocabulary of standing builds it in. Of the five words Luria ships,
two (`Superseded`, `Rejected`) are ways of leaving force while remaining
citable, and the second is defined as "kept because a rejection is worth being
able to point at".

The reason is practical, and has the shape of Chesterton's Fence turned
around. The record keeps retired entries so that whoever proposes the
retired idea again can find out why it was retired. Demotion makes the
corpus cheaper to read, since the current answer is separate from the
history, without making it poorer, since the history remains on request.

## Four metabolic rates

Different parts of a corpus forget at different speeds, and a single policy
applied to all of them is wrong for most. Luria's four layers, each with a
one-line test for what belongs in it, are four answers ([ADR-001](../../record/decisions.d/ADR-001.md)).

| Layer | How it forgets | Rate |
|---|---|---|
| Changelog fragment | Collected into a shared file, then deleted | Consumed on assembly |
| Journal entry | Never revised, never expected to stay current; rendered into books by period | Frozen at its date |
| Decision | Superseded by a successor, or corrected in place with a version | Retired when the choice changes |
| Principle | Revised, with a version and an account of why | Slowly generalized |

The fragment is consumed because its job is to be assembled and a file
that every contribution appends to is a lock. The journal is preserved because
what it records is *how it went*, including the wrong theories, which are
the part that is expensive to rediscover ([ADR-001](../../record/decisions.d/ADR-001.md), [ADR-020](../../record/decisions.d/ADR-020.md)). The decision
is retired and not rewritten because it is a choice at a point in time. The
principle is revised because it is a value that decisions cite, and it
improves by being applied.

### An unreconciled tension

The record does not fully reconcile two of these. Journals are described as
true about the day they were written and never revised ([ADR-020](../../record/decisions.d/ADR-020.md)), and the
reference documentation repeats this. A later principle argues that a record
document is "not a ledger entry", that its job is to be true and resolvable
today, and that the journals are rewritten to stay so when a code is
renumbered, because version control keeps the history of expression
([DP-017](../../record/principles.d/DP-017.md)). The two can be read compatibly, since the first concerns the *claim* a
journal entry makes about its day and the second concerns the *spelling* of
codes within it, but the documentation has not been brought into line and I
would not call the matter settled.

## Abstraction is the other half

Forgetting without abstraction is only loss, and the architecture provides for
the positive half. The record's rule for when a principle is added is
deliberately late: on the *second* re-derivation of the same reasoning,
because "one instance is a decision, a pattern is a principle". A principle is
what a corpus produces when it notices it has been arguing the same case
twice, and it preserves the evidence, since every principle names the
incident that earned it ([ADR-009](../../record/decisions.d/ADR-009.md)).

The corpus's own principles show how hard it is to abstract at the right level.
The principle that shared artifacts should be generated and not hand-edited
([DP-002](../../record/principles.d/DP-002.md)) is at its third version. The first was written about one file, so
when the same conflicts appeared on a second shared document months later nobody
recognized them. The second generalized to the artifact and stopped at
generation, and the question of *where the generator runs* was then decided
three separate times in three decisions, none of which cited the principle.
The record's own summary of the lesson is that "a value stated about one
artifact is a value nobody applies to the next one".

The framework supports a mechanical check for this, in one narrow place. A
scheme can ask that its titles generalize, and a lint reports a title that
names one of the project's own concrete nouns. The vocabulary is the project's,
because a shipped default would be "someone else's vocabulary with the
authority of a default". The check reads titles only, because scanning bodies
was measured at five of six caught against eight false alarms in fifteen, and
"a check wrong more often than right gets switched off" ([ADR-050](../../record/decisions.d/ADR-050.md)). A principle titled after a toolbar is a principle that will not
be applied to the next widget. This is Funes in miniature, an abstraction
stuck at the level of the instance.
