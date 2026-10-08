<!-- docs/paper/09-objections.md -->
<!-- inactive-ok-file: DP-018 — Proposed and not accepted; the paper says so where it mentions it -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; cited for the figures and the limits it records -->

# Objections and limits

## A citation is a proxy for dependence

The whole propagation mechanism rests on one assumption: that a code written
in a sentence marks a real reliance. The assumption fails in both directions.
A retrospective may cite a retired decision because it is the subject, which is
a false positive, and the figure of forty-two deliberate citations in seventy
findings suggests the rate is not small ([ADR-058](../../record/decisions.d/ADR-058.md)). More seriously, a sentence
may depend on a premise it does not cite. The tool sees only what is written.
It cannot report the dependence nobody represented, and the corpus will look
fully consistent exactly where its maintainers did not think to write the edge.

This is the same shape as a general hazard the record names: nothing happening
and everything working produce the same observation ([DP-015](../../record/principles.d/DP-015.md)). A clean report
shows that no *represented* dependence is in question. The record proposes,
but has not accepted, a principle that mutable premises be made explicit
dependencies at the point of reliance (`DP-018`). The proposal is a norm for
authors and not a mechanism, which is the right place for it, because the
tool cannot supply what the author did not know was a reliance.

## Green can launder authority

A passing check has the grammar of a verdict. A corpus that says "lint clean"
invites the inference that it is correct, when what the lint establishes is
that its own rules, as currently written and currently configured, found
nothing to report. The rules can be narrowed, a class of findings can be
left as a warning forever, and an acknowledgement can be written carelessly
with a reason that is not one. The inert-status case is the corpus finding a
sample of this in its adopters, a green build produced by an absence of
judgment. Nothing in the architecture guards against the same absence in the
reasons attached to acknowledgements, beyond the requirement that a reason be
present and the possibility that a reviewer reads it.

Relatedly, who may change standing is a question about power, and the
machinery records conferral without assessing its legitimacy. The mechanical
answer (whoever's contribution is merged) is a useful one and not a complete
one.

## The cost of capture

The design-rationale literature of the 1970s onward is largely a literature of
why systems for recording the reasoning behind decisions went unused. Kunz and
Rittel's issue-based information systems and their hypertext descendants
(Kunz and Rittel 1970; Conklin and Begeman 1988) asked people to capture
structured argument as they worked, and the common finding was that the
people bearing the cost of capture were not the people who benefited from it
(Grudin 1988), that premature formalization suppressed the contributions it was
meant to preserve (Shipman and Marshall 1999), and that the benefits of the
structure were too diffuse to motivate its upkeep (MacLean et al. 1991). The
counter-case in the literature is a field trial in which capture was sustained
with a lightweight notation and little disruption (Conklin and Yakemovic 1991).

Luria is a design-rationale system, among other things, and the objection
applies. Its answers are design choices and not results. Contributions are
single small files with no shared document to edit. The scaffolding is
generated. The working agreement is that an entry is filed in the same
contribution as the work, while the context is loaded, since a fact "filed while its
context is loaded costs a paragraph; re-derived cold, it costs a session" ([DP-008](../../record/principles.d/DP-008.md)). The costs of
the lint fall on the person who introduced the change, and the benefits to
the person reading the page later. That asymmetry is Grudin's, unremoved.
Whether the design mitigates it enough is an empirical question this paper
does not answer.

## The word does too much

"Living" is a metaphor, and I have specified what I mean by it as L1 to L3
and declined the stronger biological sense. A critic can still say that the
three conditions are those of any maintained database with referential
integrity, and that the label adds a flattering analogy. There is something in
that. What is distinctive is not any one of the conditions but their
combination at the level of *prose written by people*, where integrity cannot
be checked by schema, where the outcome of a violation is a question and not a
rollback, and where the answer to the question must itself be recorded. The
claim is about that combination. Whether the word helps is a matter of taste.

## Closure has a price

The vocabularies are closed, the schemes are declared, and an entry that does
not fit fails the lint. Closure is what lets standing carry weight, but it is
also what makes a corpus brittle to a subject that outgrows its categories. The
record's partial answer is that a closed vocabulary's violation message should
say that the value is *not yet declared* and that declaring it is the move
(the `alert` field on a vocabulary), and that a vocabulary which needs to say
more is promoted to a scheme and not enriched ([ADR-124](../../record/decisions.d/ADR-124.md)). That keeps closure
revisable. It does not remove the cost, which is borne by whoever has to write
the declaration before they can write the entry.

## Scope

The argument applies to corpora of discrete, citable, interdependent entries
with human authors. It says nothing about the revision of continuous prose, about
corpora whose entries are not individually meaningful, or about settings where
there is no review process that could play the part of the court. In a corpus
with no reviewer, the acknowledgement is a note to nobody.
