<!-- docs/paper/08-the-record-on-itself.md -->
<!-- inactive-ok-file: ADR-007 — superseded by ADR-035; cited as one of the three retirements the record contains -->
<!-- inactive-ok-file: ADR-010 — superseded by ADR-011; cited as one of the three retirements the record contains -->
<!-- inactive-ok-file: ADR-015 — superseded by ADR-016; cited as one of the three retirements the record contains -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; cited as the record's one rejected decision and for its prior-art account -->

# The record on itself

Luria's repository is its own first user. Its decisions and principles are
scheme documents, its changelog and development log are fragment and journal
families, and the lint and generators run on them in the project's own
continuous integration. This is the sense in which the record is a case study,
and the section below says what it can and cannot support.

## What the record contains

At the commit this manuscript was written against (`5b74248`, 8 October 2026),
the decision scheme holds 126 documents: 121 in force, three superseded,
one rejected, one proposed. The principle scheme holds 18: 17 in force and one
proposed. Seventeen decisions and four principles have been corrected in place
at least once, which is to say they carry a version above 1 and a history
saying what the earlier version claimed. The reference-status report, before
this manuscript was added to the repository, listed no unacknowledged citation
of a document out of force, and 62 citations that someone had acknowledged
with a reason.

The earliest entries are dated August 2026. Many of them were extracted from an
ancestor project's record and rewritten as decisions about Luria, each naming
its ancestor as provenance and not importing the original number, because the
evidence that earned a rule is what makes it persuasive ([ADR-009](../../record/decisions.d/ADR-009.md)). The dates
are therefore nominal as a measure of the corpus's age.

## Three retirements

The three superseded decisions are small and instructive.

**The name.** The project was called *chester* for a day. The successor
records why the first name failed, in terms that are about the project's
purpose, not about taste ([ADR-010](../../record/decisions.d/ADR-010.md), [ADR-011](../../record/decisions.d/ADR-011.md)). The corpus's worked example of
supersession is therefore a naming decision, and the successor's body
preserves the argument it replaced.

**The enforcement stance.** The policy that status findings are reported and
never enforced ([ADR-007](../../record/decisions.d/ADR-007.md)) was replaced by one that keeps the reporting default
and adds a dial ([ADR-035](../../record/decisions.d/ADR-035.md)). The change was prompted by review of a different
piece of work and stated a cost the original had not counted: that a
prohibition on promotion obstructed projects that wanted the last rung of the
ladder from prose to guarantee. Some two dozen files still cite the retired decision,
and the reference-status report lists none of them as unacknowledged, which is
to say each carries a reason.

**The remote-discovery mechanism.** A decision that let a remote's filenames be
discovered from a local clone ([ADR-015](../../record/decisions.d/ADR-015.md)) was replaced by one that reads public
URLs only, on the ground that a resolution that depends on what happens to be
on somebody's disk is not reproducible ([ADR-016](../../record/decisions.d/ADR-016.md)).

## One rejection

A decision to describe the project as a truth maintenance system ([ADR-058](../../record/decisions.d/ADR-058.md)) is
the record's only rejected decision, and it is rejected in an unusual way. The
*claim* was accepted, and the documentation now leads with the mechanism and
names the prior art as its second sentence. What was rejected was the
proposal to make the category the README's headline. The decision's status note
says so. Its body, which this paper draws on, remains the record's most
careful statement of what is new in the framework (nodes that are human prose,
propagation that halts at a finding, acknowledgement as a first-class move) and
what is not.

## A principle that failed to generalize, twice

The record's principle on shared artifacts ([DP-002](../../record/principles.d/DP-002.md)) is the clearest case of
the corpus correcting itself in public, and is described in the section on
forgetting. It is worth restating here for its evidential character. Its
three versions are the visible trace of two failures to generalize, each found
when a later instance did not recognize the earlier statement. A corpus without
version history would have shown only the final, general principle and
concealed that it was reached by being wrong twice.

## A guard fired once

The project's working agreements say that a new guard must be fired once on a
real case before it is trusted. For this manuscript the guard is the dependence
rule applied to the paper itself, and the first lint run supplied the case. I
had acknowledged three retired decisions with directives that cover only their
own line and the line below, which is the default scope ([ADR-008](../../record/decisions.d/ADR-008.md)), and cited
them further down the page. The lint reported all three as unacknowledged, and
reported each directive as no longer applying, which is the two-sided behaviour
the design intends. It also reported the paper's mention of a principle that
the record has proposed and not accepted. The fix was to widen the directives
to the whole file, with a reason, and to say in the text that the principle is
a proposal. This is a weak test, since the manuscript has no history of its own,
but it does establish that the paper's references to the record are live edges.
If any decision it relies on is superseded, the sentence that relied on it will
be named.

## What this evidence supports

The record supports four modest claims.

1. The distinctions can be implemented in plain files and a lint, and the
   result runs on a non-trivial corpus.
2. The corpus has used them to change its own mind, visibly and repeatedly, in
   a way a conventional document set would have shown only as rewrites.
3. At least two guards (inert status, narrow titles) exist because the
   corpus or a downstream adopter found the failure they catch.
4. The authors' own descriptions of what is distinctive were corrected
   against prior art ([ADR-058](../../record/decisions.d/ADR-058.md)) and not defended.

It does not support the claims that matter most for a general thesis. Three
supersessions in a corpus of 126 is a low rate, and I cannot tell from this
record alone whether it reflects a stable body of decisions or a record that
is too seldom revisited, though the 62 acknowledged citations and the
corrections in place suggest the machinery is exercised. The authors of the
guards are also the subjects of the record, so the corpus is unlikely to
contain the failure modes that its authors do not anticipate. And a record
used by its maker is the weakest kind of validation. The downstream figures
cited above come from adopters, but they are reported by the same authors in
the same record.
