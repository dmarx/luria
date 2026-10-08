<!-- docs/paper/10-related-work.md -->
<!-- inactive-ok-file: ADR-058 — Rejected as a README headline; its table of neighbouring literatures is the source for this section's first paragraph -->

# Related work

**Truth maintenance and belief revision.** The mechanism of retracting a
premise and propagating to its dependents is Doyle's truth maintenance system
(Doyle 1979), with de Kleer's assumption-based variant maintaining multiple
contexts (de Kleer 1986). The formal account of retraction is the AGM theory of
contraction and revision (Alchourrón, Gärdenfors and Makinson 1985), and
the foundations-versus-coherence debate is surveyed by Gärdenfors (1990) and
motivated by Harman (1986). Luria's record is explicit about its debt and about
what differs: its nodes are prose, propagation halts at a finding, and
acknowledgement has no counterpart in a TMS ([ADR-058](../../record/decisions.d/ADR-058.md)). Abstract argumentation
(Dung 1995) is the nearest formal account of what a scheme of claims and
relations is, though this paper does not use it.

**Design rationale.** The tradition of capturing why a design is as it is runs
from issue-based information systems (Kunz and Rittel 1970) through gIBIS
(Conklin and Begeman 1988) and the QOC notation (MacLean et al. 1991) to the
critical literature already cited. The architecture decision record, a short
document per significant decision, was popularized by Nygard (2011) and is the
form Luria's default scheme takes. The contribution here is not a better
capture notation. It is the observation that a decision record becomes a
different kind of object when it has a status that moves and citations that
follow the status.

**Traceability and impact analysis.** Requirements traceability and
change-impact analysis in safety-critical engineering trace dependence among
artifacts so that a change to one can be assessed against the others. The
industrial practice is the closest cousin of the mechanism and is typically
built on tools whose objects are not prose written for readers.

**Philosophy of institutions and norms.** The analysis of standing as a status
function draws on Searle (1995); the account of rules as the union of primary
and secondary draws on Hart (1961); the gloss on acknowledgement draws on
Lewis (1979) and Brandom (1994). I have used these as lenses and not as
foundations, and a reader who rejects any of them loses a particular argument,
not the criterion of the third section.

**Memory and the archive.** The extended-mind thesis (Clark and Chalmers 1998)
supports the claim that a corpus in use is part of a community's cognitive
system and so must be held to the standards of one. The treatment of the
archive as an instrument of authority and not a neutral store (Derrida 1995;
Foucault 1969) is the background for the section on who writes the view.
Bowker and Star's study of classification systems as infrastructure, and of the
consequences that follow when their categories become invisible to those who use
them (Bowker and Star 1999), bears directly on closed vocabularies. Bush's
imagined memex, which kept associative trails among documents (Bush 1945), is
the ancestor of the idea that the *connections* in a corpus are as much its
content as the documents.

**Software evolution and living systems.** Lehman's laws (Lehman 1980) supply the
observation that a system in use must change. Maturana and Varela's autopoiesis
(Maturana and Varela 1980) is the strong sense of "living" that this paper
disclaims.
