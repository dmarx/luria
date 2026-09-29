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

## 4. Add conditional requirements when standing makes the edge necessary

Example:

```yaml
superseded_by:
  scheme: DECISION
  required: false
  required_when:
    status:
      - Superseded
```

This says the relation is not universally required; it is required when another declared axis reaches a specific value.

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

A relation is often clearest in the sentence that justifies it. Annotate the
citation with the relation's name and an arrow, and the prose states the edge:

```markdown
Nothing here is new (see [[RFC-2]]{--extends-->here}).
The recovery path is [[RFC-7]]{here--extends-->}'s, generalised.
```

`{--F-->here}` reads left to right: the cited document stands in relation `F`
to this one. `{here--F-->}` is the other direction. `F` is a reference field
declared on the scheme of the document at the arrow's tail. The annotation
follows the link, so `luria link --fix` turning `[[RFC-2]]` into a markdown
link keeps it attached; one in a code span, fence or comment is a specimen and
states nothing ([ADR-tmp3gms4](../../record/decisions.d/ADR-tmp3gms4.md)).

**Pushing up.** An annotated edge missing from frontmatter is
`unrecorded-relations`, and `luria link --fix` writes it: into this
document's field for `{here--F-->}`, and for `{--F-->here}` into this
document's converse field when `F` declares one, otherwise into the cited
document's `F`. The converse completion in the same run writes the far side.

**Pushing down.** A reference declared `explain: true` asks for the reverse —
every code the field holds cited in the body, annotated:

```yaml
references:
  extends:
    scheme: RFC
    required: false
    many: true
    converse: extended_by
    explain: true
```

A plain citation of a code the field holds is `unannotated-relations`, and the
fixer annotates it. A code the body never cites is `unexplained-relations`, a
report rather than a fix: the explanation is prose only you can write. Write
it, or acknowledge the code with `<!-- unexplained-ok: RFC-2 — the title says
it -->`.

An annotation the record cannot hold as written — attached to no citation,
naming a relation the scheme does not declare, pointing into the wrong scheme,
or contradicting a single-valued field that already holds another code — is
`bad-annotations`.

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
