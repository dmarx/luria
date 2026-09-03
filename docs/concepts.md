# Concepts

Entries, citations, and the status field the rest of it hangs off.

The [quickstart](quickstart.md) has you filing entries and seeing a finding.
This page is what was underneath that. It is the shortest complete account;
[designing a record](modeling.md) is how to choose between the options it
describes, and [project memory](project-memory.md) is the reference.

## The engine

Luria maintains a graph. The nodes are **referable documents** — one file
each, prose with a little structured frontmatter, and a code something else
can name. The edges are **citations**: one document naming another by its
code, in ordinary sentences.

Every referable document carries a `status`. One value per scheme is *in
force*; the rest mean the document is retired in some way.

A record holds other material too — journals, fragments, remotes, and ordinary
prose — and none of it is status-bearing. Only referable documents are nodes
in this graph, which is why they are the only ones that can go out of force
and take citations with them. [What the record is made of](#the-four-families)
sorts the rest.

That is the model. Everything else is machinery around one operation:

> **Change an entry's status, and every citation of it becomes a finding.**

Nothing else in the system produces that effect, and it is the part that
quietly fails to happen. A project whose statuses never move has a graph that
never propagates: no citation is ever reconsidered, and the build stays green
because nothing is being judged. `luria lint` reports that state as
`inert-status`.

## Status

The vocabulary is closed to five words:

`Active` · `Proposed` · `Deferred` · `Superseded` · `Rejected`

a superseded document naming its successor in `superseded_by:`, and any
of them optionally qualified by a `status_note:`, a prose field in its
own right.

Closed because an audit of 121 entries found an open vocabulary had drifted
into roughly thirty forms — not toward one wrong value but toward *variety*,
which is worse, because a reader cannot learn what the field means.

**What each word means is yours, and differs by scheme.** `Rejected` on a
decision means considered and declined. On a reading list it can mean *retired
from the shelf, and here is why*. On a scheme of terms it can mean *this word
picks nothing out*. Say which in a `statuses.yaml` beside the entries, and the
meanings render above the index table they explain:

```yaml
Active:
  label: In force
  blurb: safe to cite as justification
Rejected:
  label: Retired
  blurb: no longer believed, and the body says why
```

Declaring is also narrowing: an entry whose status the scheme does not declare
fails the lint.

## Citations

A citation is a code written in prose. Write it bare and let the fixer link it:

```console
$ luria link --fix
docs/scaling.md: 3 reference(s)
```

**Never hand-write a link target.** Entry prose is rendered into views in other
directories, so a target has to resolve from where the text *lands*, not where
it lives. A journal entry five directories deep renders into `docs/journal/`,
and the depth that looks right beside the source points at nothing in the view.
Only the fixer knows that frame, and a check catches targets it did not write.

Prose as the label is still the fixer's job:
`[[ADR-012|the caching decision]]`.

## Findings and acknowledgements

A finding is what propagation produces. Five matter most:

| | |
|---|---|
| `retired-citations` | an entry cites something not in force. The core finding. |
| `unresolved-codes` | `ADR-047` names no document — a reference nobody can follow. |
| `broken-targets` | a relative link resolves to nothing from where the prose renders. |
| `inert-status` | a whole scheme at one status, so the field says nothing. |
| `narrow-titles` | a title that claims to generalise while naming one subsystem. |

Reported by default. Naming one in `[luria.lint] fail_on` promotes it to a
build failure, per class, so a project can enforce what it cares about while
it works through the rest.

**Every finding can be answered where it is raised.** A citation of a retired
entry that is deliberate — history, or a rejection worth pointing at — takes an
`inactive-ok:` comment at the citing site, carrying the reason:

```markdown
<!-- inactive-ok: ADR-012 — the decision this one replaced -->
```

The reason is mandatory, it lives where the finding would have appeared, and it
lapses when the condition does. That bargain is the whole
[directive vocabulary](directives.md), and it is what keeps the checks worth
reading: a guard nobody can answer is one people learn to skip.

## The four families

Four kinds of table in `luria.toml`, and none of their names is in the code:

- **Schemes** — families of entries with codes (`ADR-012`, `RFC-7`). Either
  browsed one at a time through a generated index, or concatenated into a
  single page when the set is short enough to read whole — that is the
  `render` key, and [which one you want](modeling.md#index-or-document) is a
  question about how the set is read rather than about the output.
- **Journals** — dated entries that persist and are never revised, rendered
  into books.
- **Fragment directories** — pieces written now and assembled later, which is
  how a changelog stops being a file every branch has to touch.
- **Remotes** — another namespace, cited by prefix. `LU-ADR-013` is another
  project's decision; a `uid` remote makes arXiv identifiers or ticket keys
  first-class citations without their being records at all.

A scheme can also constrain what its entries may be: required fields, exactly
one primary category, which statuses it uses. Those are what stop a convention
from being a comment. [Designing a record](modeling.md) is how to pick.

## Sources and views

Two directories, and the split is a rule rather than a preference. `record/`
holds what people **file**; `docs/` holds what people **read**, and everything
in it that is a view is generated by `luria index`. The lint refuses hand edits
to a generated page, which is what lets the views be trusted as projections
rather than maintained as copies.

That guarantee covers generated views and nothing else. Hand-written prose in
`docs/` drifts like hand-written prose anywhere; what the record can tell you
is when it cites something that has stopped being in force.

## Three things it is not

**Not a documentation generator.** It generates documentation, but so does
everything; the generation is a means. Without a status that moves, luria
degenerates into exactly that, and `inert-status` is the check that says so.

**Not a linter**, in the usual sense. A linter checks a file against rules that
do not change. Here nothing about the prose changes when a status does: one
field moves, and consequences appear in files nobody opened.

**Not a wiki.** A wiki's links break silently.

## The prior art

The mechanism is old and has a name. A **truth maintenance system** — Doyle,
1979; de Kleer's assumption-based variant, 1986 — maintains a set of beliefs
together with the justifications linking them, where each node is IN or OUT and
retracting a belief propagates to everything whose justification depended on
it. That is the operation at the top of this page.

Three things here are not in that literature, and they are the interesting
part: the nodes are human prose rather than propositions, propagation halts at
a finding instead of resolving itself, and acknowledgement is a first-class
move — a person can say *yes, and that is fine* and have the system record the
reason.

The neighbouring vocabularies are worth knowing by name if you want to read
further: belief revision for the formal account of retraction, requirements
traceability for the industrial cousin, and abstract argumentation for what
the schemes are.

- Doyle, [*A Truth Maintenance System*](https://doi.org/10.1016/0004-3702(79)90008-0) (1979).
- de Kleer, [*An Assumption-based TMS*](https://doi.org/10.1016/0004-3702(86)90080-9) (1986).
- Alchourrón, Gärdenfors & Makinson, [*On the Logic of Theory Change*](https://doi.org/10.2307/2274239) (1985).
- Dung, [*On the Acceptability of Arguments*](https://doi.org/10.1016/0004-3702(94)00041-X) (1995).

## Next

- [Designing a record](modeling.md) — which family fits your material, when
  two kinds of entry are two schemes, and what the schema can refuse.
- [Project memory](project-memory.md) — the reference for each family.
- [Comment directives](directives.md) — the acknowledgement vocabulary in full.
- [CLI reference](cli.md) — every command, flag by flag.
