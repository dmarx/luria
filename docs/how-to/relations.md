# How to model and add relations

Use a typed reference when a relationship matters semantically.

## 1. Declare the reference

Example (a fragment: the `IMPLEMENTATION` table also needs its `dir` and the rest of a scheme's keys, and `DECISION` must be a declared scheme):

```yaml
schemes:
  IMPLEMENTATION:
    references:
      decision:
        scheme: DECISION
        required: true
        many: true
        label: Implements decision
```

Now `decision` is not an arbitrary string field. It is a declared relation to `DECISION` ([ADR-060](../../record/decisions.d/ADR-060.md)): the lint checks that every value is a code of that scheme that resolves.

A reference field is required unless it says `required: false`, so spell that out for an optional edge — `required: true` above only restates the default.

## 2. Decide cardinality

Use:

```yaml
many: false
```

for a scalar relation, or:

```yaml
many: true
```

for a list. `many: false` is the default. A field that takes part in a converse pair (below) must be `many: true` on both sides, because several documents can stand in one relation to the same target.

## 3. Add a converse when the reverse edge is semantic

A converse is the same relation read backwards: if A `extends` B, then B is `extended_by` A. Declare it as a pair — the reverse field is declared on the scheme whose codes the first field holds, and each side names the other ([ADR-084](../../record/decisions.d/ADR-084.md), [ADR-097](../../record/decisions.d/ADR-097.md)):

```yaml
schemes:
  RFC:
    references:
      extends:
        scheme: RFC
        required: false
        many: true
        converse: extended_by
      extended_by:
        scheme: RFC
        required: false
        many: true
        converse: extends
```

For a relation that crosses schemes, the converse field lives on the other scheme and points back: `SOTA.introduced_by` holding `LIT` codes pairs with `LIT.introduces` holding `SOTA` codes.

Only declare a converse when the reverse relation is actually known. Without one, Luria does not guess, and nothing writes a reverse edge.

A symmetric relation is its own converse:

```yaml
compared_against:
  scheme: RFC
  required: false
  many: true
  converse: compared_against
```

A half-declared pair — a converse that is not a declared field of the target scheme, does not name the original back, or is not `many: true` — is refused when `luria.yaml` loads.

## 4. Use conditional requirements for state-dependent fields

Every scheme already has a successor relation: its `successor` field defaults
to `superseded_by`, and an entry carrying the scheme's `retires_on` status
(default `Superseded`) must fill it ([ADR-071](../../record/decisions.d/ADR-071.md)). Do **not** redeclare
`superseded_by` merely to make that rule conditional.

For your own field or relation, `required_when` expresses the same general
shape. For example, a proposed or deferred recommendation can be required to
say what would settle it:

```yaml
fields:
  promote_when:
    required_when:
      status:
        - Proposed
        - Deferred
```

The field is required only in the named states: an entry at `status: Proposed`
with no `promote_when:` fails the lint, and an `Active` one does not.

## 5. Add an invariant when the edge implies shared structure

Example:

```yaml
extends:
  scheme: RFC
  invariant: tags
```

Now the edge claims the endpoints share some declared subject vocabulary. The invariant belongs to the relation, so it holds whether or not a chain walks the field, and it may cross schemes ([ADR-106](../../record/decisions.d/ADR-106.md)).

## 6. Write the relation

`luria relate SOURCE FIELD TARGET` writes a declared relation into an existing document's frontmatter. SOURCE and TARGET are codes, not paths; the target must resolve.

```console
$ luria relate RFC-003 compared_against RFC-002
record/rfcs.d/RFC-003.md: compared_against += RFC-002
```

It writes the one side you named. Until the other side exists, `luria lint` reports the pair under `one-sided-relations`; `luria link --fix` writes the converse:

```console
$ luria link --fix
linked 0 reference(s) in 19 file(s)
wrote 1 back-reference(s) in 1 file(s)
```

`luria relate --draft FILE` reads relations instead of taking them as arguments: FILE is a JSON drafts file whose `relations` list holds `{"source", "field", "target"}` entries, each written as above.

## 7. State the relation where you explain it

A relation is often clearest in the sentence that justifies it. State it
there, with the same comment-directive grammar every acknowledgement uses:
the `ref::` namespace, then the field that holds the relation.

```markdown
The recovery path is RFC-007's, generalised. <!-- ref::extends: RFC-007 -->

<!-- ref::extended_by-block: RFC-012, RFC-015 — both carry the retry loop on -->
Two later designs picked this up...
```

The name after `ref::` is a reference field of *this* document, either one
your scheme declares or the built-in `superseded_by`. There is no direction to
choose, because a relation read the other way has its own name, its converse.
The namespace keeps these names apart from the fixed directive vocabulary, so
a field may be called anything but a name ending in `-block` or `-file`, which
would read as a scope. It also means a misspelt field is reported rather
than ignored.

Everything a [directive](../directives.md) has comes with it: line, `-block` and
`-file` scope, a `— reason`, and `until <date>`. An example in a code span
or fence states nothing, and a statement in frontmatter comments is ignored
([ADR-122](../../record/decisions.d/ADR-122.md)).

`[[extends::RFC-7]]` is shorthand for a citation plus its statement.
`luria link --fix` expands it to `[RFC-7](RFC-007.md)<!-- ref::extends: RFC-007 -->`.
A shorthand naming a field this document doesn't have is left unexpanded and
fails the lint, and a `ref::` statement naming one is `bad-annotations`.

**Pushing up.** A stated relation missing from frontmatter is
`unrecorded-relations`, and `luria link --fix` writes it into this document's
field. The converse completion in the same run writes the far side.

**Pushing down.** A reference declared `explain:` asks for the reverse: every
code the field holds accounted for in the body. There are two strengths.

```yaml
references:
  extends:
    scheme: RFC
    required: false
    many: true
    converse: extended_by
    explain: true      # or: cited (the same), stated (stricter)
```

- **`explain: true` (or `cited`)** asks that the body cite each code
  somewhere, and takes the citation as serving the relation. A code the body
  never cites is `unexplained-relations`, a report rather than a fix, since
  the explanation is prose only you can write. This is the useful default: it
  finds the relation nothing in the prose mentions, and leaves alone the
  citations whose sentence already says what the relation is.
- **`explain: stated`** also asks that each citation carry a statement of the
  relation, a `ref::` statement governing it. A citation with no statement is
  `unannotated-relations`, and the fixer writes the statement after it. Use
  it when the relation's name adds something the prose would not.

At either strength, a statement's `— reason` counts as the explanation, so a
`-file` statement with a reason is how you say the relation needs no more
prose than that.

A statement the record can't hold as written is `bad-annotations`. That
covers an argument that isn't a code, a code naming no document here, a code
in a scheme the field doesn't hold, and a single-valued field that already
holds another code.

## 8. Lint the result

```console
$ luria lint
```

Check for:

- unresolved targets,
- wrong target scheme,
- converse inconsistencies,
- invariant failures,
- relations stated in prose and missing from frontmatter, or the reverse,
- standing-related findings.

## 9. If the relation forms a longitudinal sequence

Do not maintain a prose lineage by hand.

Define a [chain](chains.md) ([ADR-083](../../record/decisions.d/ADR-083.md)).
