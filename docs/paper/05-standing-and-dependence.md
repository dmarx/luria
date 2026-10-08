<!-- docs/paper/05-standing-and-dependence.md -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; its account of how acknowledgement differs from a truth maintenance system's automatic retraction is cited as evidence -->

# The architecture, part one: standing and dependence

The architecture of a living corpus, as I use the term, is the set of
distinctions it must draw so that L1 to L3 can hold. This section takes the
first two groups, which concern what an entry *is* and what it *rests on*. The
next takes authority, judgment, and self-governance.

## Identity, standing, and history

A conventional document collection runs three questions together. A living
corpus separates them.

| Question | Answer is kept in | Example |
|---|---|---|
| What object is this? | **identity**, a code that persists | `ADR-019` |
| What is its authority now? | **standing**, a status from a declared vocabulary | `Active`, `Superseded` |
| What has happened to it? | **history**, versions and a named successor | `version: 2`, `superseded_by` |

Identity must be stable because it is what other entries cite. In Luria a
document's filename is its code and nothing else, with the title in the
frontmatter, because a title is something that gets corrected and a
correction should cost an edit rather than a rename of the file and every link
to it ([ADR-013](../../record/decisions.d/ADR-013.md)). Identity that changes with the wording is identity that no
dependent can rely on.

### Standing is conferred, not found

Standing is not a property of a text. The same paragraph might be an `Active`
decision in one project and a `Rejected` proposal in another. It is better
understood as what Searle calls a *status function*: something counts as an
authoritative decision in a context, by virtue of collective acceptance, and
carries with it a set of permissions and obligations (Searle 1995). The
deontic content is easy to state for a corpus. An entry in force may be cited
as justification without comment. An entry out of force may be cited only with
a reason.

Two features of the design follow from taking this seriously. First, the
vocabulary of standing is *closed and declared*. A status function can carry
deontic weight only if the community can tell which statuses exist. Luria's
predecessor corpus had an open vocabulary, and an audit found about thirty
distinct forms in use, with "Accepted" and "Active" split almost evenly between
entries that meant the same thing ([ADR-003](../../record/decisions.d/ADR-003.md)). The drift was toward *variety*
rather than toward any wrong value, which is worse, since a reader cannot learn
what the field means. Second, what each word means is the project's to say and
can differ by scheme: `Rejected` on a decision means considered and declined,
and on a reading list it might mean retired from the shelf, with the reason in
the body ([ADR-085](../../record/decisions.d/ADR-085.md)).

### Two histories

A corpus can keep two different histories, and conflating them is the
characteristic confusion of document management.

The **history of belief** is what the corpus held, when, and what replaced it:
*we believed X, and now we hold Y, for these reasons*. The **history of
expression** is how the words changed: which characters differed between one
revision and the next. The first is part of the corpus's content. The second is
bookkeeping about its text, and a version-control system already keeps it
better than prose can.

Luria divides the labour accordingly. The history of belief stays in the corpus,
as the standing and successor of each retired entry. The history of expression
is delegated to the version-control system, and the record is rewritten to stay
true because "the characters are not the deliverable; the claim is" ([DP-017](../../record/principles.d/DP-017.md)).
Where a literal old spelling must survive, as a document's former identity
that other branches may still cite, it is kept as structured data and not as
prose.

Within the history of belief, one further distinction does most of the work.
A decision can be wrong in its *choice* or wrong in its *reason*. If the choice
changes, the entry is superseded: a successor is filed and the old entry keeps
its body. If the choice stands and only a reason was wrong, the entry is
corrected in place, its version is incremented, and the previous claim is
recorded in its history ([ADR-019](../../record/decisions.d/ADR-019.md)). The test the record gives is counterfactual
and pragmatic: *would a reader who acted on the old version have done something
different?* If so, the choice changed.

This is a criterion of identity for a claim, in the pragmatist tradition that
individuates a belief by what it licenses one to do. It matters architecturally
because both alternatives are corrosive. If every change were a supersession,
the status vocabulary would lie, since entries still in force would be
retired and every citation of them repointed at an identical claim. If no change
were a supersession, the corpus would be a palimpsest. The corpus's own first
decision shows the cost of the extreme. Its first version stated the rule
absolutely ("a decision is superseded but never rewritten"), which reads as
"documents are frozen" and leaves no way to fix a wrong argument short of
retiring a decision still in force. It was corrected in place, with a visible
history, within the day ([ADR-001](../../record/decisions.d/ADR-001.md)). The objection, in the record's words, is to
*silent* revision, not to being wrong out loud.

## Dependence

### A citation is a claim

In a living corpus a code written in a sentence is not a bibliographic
courtesy. It is a claim that the cited entry is part of why the sentence is
true, and the tool treats it that way ([ADR-005](../../record/decisions.d/ADR-005.md)). The record's own
documentation states the distinction I want. A bibliography tells a reader
where an idea came from, while a dependency tells the corpus which other claim,
changing, would make this one questionable. The test for whether a citation is
a dependency is: *if this premise were superseded, could this claim become
false or misleading?*

The manuscript you are reading is subject to its own rule. Each decision or
principle it relies on is cited by code, so that if one is retired the
relevant paragraph surfaces for review without anyone having edited it. It also
means the paper is a dependent of the record it describes, which is a
modest form of the self-application discussed below.

### Why a corpus must keep justifications

There are two broad pictures of how a rational agent should revise beliefs.
On a *foundations* theory, beliefs are held on the strength of reasons, and
withdrawing a reason is cause to withdraw what rested on it; Doyle's truth
maintenance system is the canonical implementation (Doyle 1979; de Kleer 1986).
On a *coherence* theory, a belief is retained unless it conflicts with others,
and nothing is lost by forgetting why it was adopted (Gärdenfors 1990).
Harman argues that human reasoners are in fact coherentists: they do not and
could not keep track of the justifications of all they believe, and rational
change in view is conservative about what is already held (Harman 1986).

I think the contrast explains something about corpora. A human mind can afford
to be coherentist because it is a single continuous process whose dispositions
carry its history implicitly. Where reasons are forgotten, the beliefs persist
and the agent behaves as if they were justified. A corpus consulted by
rotating participants has no such continuity. If the project does not write
down what rests on what, then *no one* knows, and the loss is not a clutter
saved but a capacity destroyed. The externalization of memory forces a
foundations-style bookkeeping on a community that, as individuals, reasons in
the other way.

The qualifier is policy. Bookkeeping is what the corpus must be able to say;
what it does with the answer is a separate matter. A classical truth
maintenance system acts on the bookkeeping by marking a node out when its
justification is withdrawn. Luria records the same loss of justification and
then *stops*, because whether a withdrawn premise defeats an argument is a
judgment ([ADR-058](../../record/decisions.d/ADR-058.md)). The acknowledgement that follows, in which a person says
*I know, and this citation stands, for this reason*, is Harman's conservatism
made explicit and accountable: retention of a belief whose original support has
gone, which is rational in the human case, is here permitted at the price of
a stated reason. The combination is foundationalist in what it records and
coherentist in what it permits, which seems to me the right posture for a
corpus, though I offer it as a proposal and not as a result.

### The web must be legible to be revised

Neurath compared our situation to that of sailors who must rebuild their ship
at sea, plank by plank, with no dry dock in which to take it apart (Neurath
1932). Quine's holism makes the same point about revision: any statement can be
held true, come what may, by making adjustments elsewhere in the web (Quine
1951; Quine and Ullian 1970). Both accounts assume a revision can find the
"elsewhere".

For a person this is a matter of understanding. For a corpus it is a matter of
representation. A web that is not explicit is revisable only from the memory of
its maintainers, and replacing that memory is the purpose of the corpus. So the
precondition of revisability is *legibility of dependence*: the edges have to be
written in a form the corpus can read. The dependence also need not be a single
kind. Luria lets a scheme declare typed relations (`extends`, `rests_on`,
`compared_against`), each with a declared converse, so that an edge written on
one side exists on the other, and an invariant that both ends must agree on
([ADR-083](../../record/decisions.d/ADR-083.md), [ADR-106](../../record/decisions.d/ADR-106.md)). A line of work can then be *derived* from the edges authors
state, rather than maintained as a second, hand-written lineage that can
drift.

### Dependence on what others hold

Some of what a corpus rests on is held elsewhere. A decision can cite another
project's decision, and a reading list can cite a paper whose standing is
decided by a literature the corpus does not control. The epistemology is that of
testimony: the corpus cannot verify the source's standing, which can change
tomorrow without notice.

What it can do is record what *it* endorsed and detect a change since. Luria
stores a hash of each pinned foreign document as the content a human vouched
for, compares it offline to the content upstream now serves, and reports each
document that has changed since it was endorsed. Re-endorsing after review is
the acknowledgement ([ADR-066](../../record/decisions.d/ADR-066.md)). The foreign standing is never known. What is
known is that the thing endorsed has moved, which is the Cambridge change
again, detected at the boundary.
