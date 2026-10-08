<!-- docs/paper/04-secondary-rules.md -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; its account of what a truth maintenance system does not do is cited as evidence -->

# Secondary rules for knowledge

## Hart's diagnosis

H. L. A. Hart argued that a legal system is best understood as the union of
two kinds of rule (Hart 1961, chapter V). *Primary* rules require or forbid
conduct. A society that has only primary rules is not without order, but its
order has three characteristic defects.

- It is **uncertain**: nothing identifies which rules count, or settles what
  to do when they conflict.
- It is **static**: nothing provides for deliberately adding, changing, or
  dropping a rule, so change is slow and accidental.
- It is **inefficient**: there is no authoritative way to settle whether a rule
  has been broken, so enforcement is diffuse and episodic.

Each defect is remedied by a *secondary* rule, a rule about rules. A **rule of
recognition** says what counts as a valid rule. **Rules of change** say how
rules may be introduced and withdrawn. **Rules of adjudication** say who settles
disputes and how. Hart's claim is that the step from the first condition to
the second is the step from a pre-legal to a legal order.

## The transfer

A directory of notes is a society of primary assertions. Each note says
something, such as a decision, a claim, or a recommendation, and nothing says
which notes currently count. The three defects reappear without alteration.

- **Uncertainty.** Two notes disagree and neither is marked as the one in
  force. A reader cannot tell the live decision from the abandoned
  proposal that sits in the same folder with a later modification date.
- **Static character.** Changing a note is either an edit that erases the
  prior position, or, because that is uncomfortable, not done. A corpus that
  has no sanctioned way to change its mind will do it unsanctioned.
- **Inefficiency.** Nobody is responsible for noticing that a premise has
  moved. The remedy in practice is diffuse pressure: someone, eventually, will
  remember that a page depends on a decision that changed. Hart's
  description of the legal case fits: enforcement by diffuse social pressure
  works about as well here as it does there.

The remedies are the secondary rules, and the three conditions of the
previous section are their results.

| Hart's defect | Secondary rule | What the corpus needs | In Luria |
|---|---|---|---|
| Uncertainty | Recognition | A way to say what counts as an entry and whether it is in force | A scheme declares a code; a closed status vocabulary says what is in force ([ADR-003](../../record/decisions.d/ADR-003.md), [ADR-085](../../record/decisions.d/ADR-085.md), [ADR-013](../../record/decisions.d/ADR-013.md)) |
| Static character | Change | A sanctioned way to retire an entry and to correct one | Supersession with a named successor; in-place correction with a version and a history; migrations ([ADR-019](../../record/decisions.d/ADR-019.md), [ADR-040](../../record/decisions.d/ADR-040.md)) |
| Inefficiency | Adjudication | A designated place where a question about dependents is raised, and a designated way of answering it | A finding raised at the citing site; an acknowledgement answered there with a reason ([ADR-035](../../record/decisions.d/ADR-035.md), [ADR-008](../../record/decisions.d/ADR-008.md)) |

Under this reading, L1 is the output of recognition, L2 is what makes the
rule of change *consequential* (a change of standing has effects), and L3 is
adjudication. The framework's stated operating loop, in which lint discovers,
repair fixes the mechanical, and acknowledgement records human judgment, is the
secondary-rule structure in miniature.

## Where the analogy strains

Three disanalogies are worth stating, because each of them shapes the design.

**The rules are partly compiled.** Hart's rule of recognition is a social
practice that officials accept from an internal point of view; it is a fact
about what they do, and is not itself written down in a statute. The
participants in a corpus are often unable to take that point of view: some
are stateless, arriving without context and leaving without leaving any, and
it would be a mistake to suppose that a norm written in prose will be
followed reliably by them. The record's answer is a principle it calls
*culture must be compiled* ([DP-005](../../record/principles.d/DP-005.md)): norms that matter are walked up a ladder
from prose to convention to mechanism to guarantee, and "when you find yourself
repeating a correction, that is the signal to walk the norm up a rung." Secondary
rules in a corpus are therefore not only practised, they are partly executed.

That has a cost, and it is the first of the objections taken up later. A
rule of recognition that a machine applies recognizes only what the machine
can see. Everything that the compiled rules cannot express is outside the
corpus's secondary rules, and it will be treated as if it were not there.

**The adjudicator does not decide.** A court settles a dispute. The lint
surfaces a question and halts. What it does not do is resolve it, because
resolving it is a judgment about meaning that the tool cannot make ([ADR-058](../../record/decisions.d/ADR-058.md)).
The Hartian *court* is the review process around a contribution: the person
who decides that the sentence should be rewritten, or that it should stand with
a recorded reason. The section on authority and judgment takes this up.

**The rules govern themselves.** In Hart's account the ultimate rule of
recognition is not itself valid or invalid; it is simply practised. In a
corpus the configuration that declares the schemes and statuses is itself a
file, and the governing documents (decisions, principles) are entries of the
same kind as the ones they govern. This is both an advantage and a hazard, and
it is discussed with the distinction between subject and governing knowledge.
