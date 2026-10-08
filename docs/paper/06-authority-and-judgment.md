<!-- docs/paper/06-authority-and-judgment.md -->
<!-- inactive-ok-file: ADR-007 — the decision ADR-035 supersedes; the paper cites the replacement as an instance of the corpus changing its mind -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; its figures on how many findings were deliberate are cited as evidence -->

# The architecture, part two: authority, judgment, and self-governance

## Authority and display

Whatever a corpus says, some of it was written by someone and some of it was
assembled from that writing. The distinction matters because the second kind
cannot be trusted on its own account. A *source* is an assertion by an author.
A *projection* (an index, a rendered book of principles, a status report, a
badge count) is a rearrangement of sources, and its trustworthiness is exactly
the trustworthiness of the derivation.

The architecture draws the line as a rule about direction. Authority runs from
source to projection and never the reverse, and the corpus enforces it: a
directory of views contains only generated files, a hand-written file in one is
a violation, and a stale view fails the build. A view is *display* and not
*voice*. It speaks for no one, so a reader can read it without asking who wrote
it, and nobody can edit it to make a point.

The reason given in the record is empirical. A hand-maintained copy of what an
authoritative source already knows drifts, and this is "not a risk but a rate":
when one project converted five such lists, five had already drifted ([DP-003](../../record/principles.d/DP-003.md)).
The decision index was the first case. In the predecessor corpus 45 of 155 rows
disagreed with their own decision's status ([ADR-004](../../record/decisions.d/ADR-004.md)).

### Authority and concurrency

A second condition on authority is less obvious. If every contribution must
edit one shared file, that file is a lock, and the conflicts it generates carry
no information. Luria's answer is structural: each contribution writes a file
nobody else writes, and the shared artifact is generated. The principle has
three versions in the record, and the third is the instructive one. It adds
that the generator must run *where merges serialize*, because a generator that
runs on every branch and commits its output has made every branch a writer of
the same file ([DP-002](../../record/principles.d/DP-002.md)). Views are therefore committed on the default branch and
a contribution writes none ([ADR-068](../../record/decisions.d/ADR-068.md)).

There is an old observation in the theory of archives that the authority of an
archive lies in the place and the power by which things are consigned to it
and interpreted (Derrida 1995; Foucault 1969). In this architecture that place
is concrete and small: it is the point at which merges are serialized, and the
only writer of the shared view is whatever runs there. I make no claim that
Luria's designers had the philosophy in mind. The point is that the question
*who is the archon?* has a mechanical answer once one is forced to ask it.

## Finding and judgment

A living corpus must do two things with a surfaced question that pull in
opposite directions: make it impossible to ignore, and refrain from answering it.

### Reported by default, enforced by dial

The record's first position on status was that it should be *reported, never
enforced*: citing a rejected decision is often exactly right, and a guard that
is wrong most of the time gets suppressed, after which the cases where it is
right go unread ([ADR-007](../../record/decisions.d/ADR-007.md)). That decision was later superseded by one that keeps
the default and removes the "never". Findings stay warnings unless a project
promotes named classes to failures, and the accounting is unchanged under
enforcement, since an acknowledged citation stays acknowledged ([ADR-035](../../record/decisions.d/ADR-035.md)). The
stated reason for the change was that a prohibition on promotion was a "soft
gate" against projects that wanted exactly the last rung of the ladder from
prose to guarantee. The corpus corrected its own constitution because a default
would do where a prohibition had been written.

### Why the tool cannot resolve the question

Two facts from the record explain why the question cannot be answered by
machine. The first is logical. Withdrawing a premise does not in general
refute an argument that used it: a bad argument for P is not a defeater for P.
The second is empirical. In the first wave of findings in a downstream
adoption, forty-two of seventy were deliberate and legitimate citations
([ADR-058](../../record/decisions.d/ADR-058.md)). A tool that had rewritten or
invalidated them automatically would have been wrong on a majority.

So the tool halts. It differs from a classical truth maintenance system in
exactly this, and in the corresponding move: where a TMS has nodes that are IN
or OUT, a Luria entry cited from a retired premise is neither. It is in
question, and the answer is a person's.

### The acknowledgement

The person's answer has a form, and the form matters more than the verdict. An
acknowledgement is a comment at the citing site naming the retired entry and
stating a reason. The reason is mandatory. It is placed where the finding
would have appeared, it lapses automatically if the entry returns to force, and
it is counted in the reports and not hidden ([ADR-035](../../record/decisions.d/ADR-035.md)). The record states the
corollary as a standing value: a suppression must not become a silence
([DP-001](../../record/principles.d/DP-001.md)).

One useful gloss comes from the philosophy of language. Lewis described a
conversation as having a score that evolves under the participants' moves
(Lewis 1979), and Brandom described discursive practice as the keeping of
accounts of commitment and entitlement, in which a speaker who undertakes a
commitment may be asked to vindicate their entitlement to it by giving reasons
(Brandom 1994). Citing a retired premise is a commitment whose entitlement is
open to challenge, and an acknowledgement is the vindication. I offer this as
interpretation. Luria does not implement either theory, and I do not claim it
derives from them. What the gloss shows is that the design is not arbitrary:
the demand for a reason, at the site of the challenge, is the demand that a
practice of giving and asking for reasons makes anyway.

### The failure of silence

The corpus has a characteristic way of dying, and it is the canon of the
introduction appearing inside a system built to prevent it. If every entry in
a scheme has the same status, the mechanism that reads status cannot fire, and
the build is green *because nothing is being judged* and not because nothing is
wrong. The record found this downstream: thirteen green builds over a scheme of
fifty-one entries at one status, twenty-three of which the corpus's own bodies
refuted ([ADR-057](../../record/decisions.d/ADR-057.md)). The remedy is a report that measures the distribution of
statuses and leaves the threshold to the project, with an acknowledgement for
the case where uniformity is intended ([ADR-081](../../record/decisions.d/ADR-081.md)). The principle underneath is
generic: nothing happening and everything working produce the same observation,
so the silent case needs a signal of its own ([DP-015](../../record/principles.d/DP-015.md)).

## Subject and governing knowledge

Some entries in a corpus are about its subject. Others are about how entries
are represented, checked, and changed. Luria's documentation distinguishes
the governing knowledge M from the subject-level knowledge R, and the question
a record keeps asking can be written *M; R ⊢ x*: under the current rules and the
current subject record, does this object or relation remain admissible? The
notation is a mnemonic, not a logic, and the documentation treats it as a rough
judgment. It is not computed.

What is structurally notable is that M is made of the same stuff as R. The
design principles and decisions are entries with codes, statuses, versions, and
citations, so the identity, standing, and propagation machinery that serves the
subject serves the governance too. A rule about how to supersede a decision can
itself be superseded, and was: the corpus's first rule about supersession was
corrected in place within a day ([ADR-001](../../record/decisions.d/ADR-001.md), [ADR-019](../../record/decisions.d/ADR-019.md)).

This is Neurath's boat with a logbook. The corpus cannot step outside itself to
check its rules against a fixed standard; it can only rebuild a plank at a
time while afloat. What the logbook adds is that each plank replaced is
recorded with its replacement and the reason. The hazard is that the sailors can
also change the rules to make the checks pass. The architecture offers no
defence against that except that rule changes go through the same review as
everything else, and the objections section is candid that this is a social
protection and not a technical one.
