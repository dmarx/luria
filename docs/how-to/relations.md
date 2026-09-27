# How to model and add relations

Use a typed reference when a relationship matters semantically.

## 1. Declare the reference

Example:

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

Now `decision` is not an arbitrary string field. It is a declared relation to `DECISION`.

## 2. Decide cardinality

Use:

```yaml
many: false
```

for a scalar relation, or:

```yaml
many: true
```

for a list.

## 3. Add a converse when the reverse edge is semantic

Example:

```yaml
extends:
  scheme: RFC
  converse: extended_by
```

Only declare a converse when the reverse relation is actually known. Without one, Luria should not guess.

A symmetric relation may name itself:

```yaml
compared_against:
  scheme: RFC
  converse: compared_against
```

## 4. Add conditional requirements when standing makes the edge necessary

Example conceptually:

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

Now the edge claims the endpoints share some declared subject vocabulary.

## 6. Write the relation

Use the current `luria relate` interface:

```console
$ luria relate --help
```

The command writes a declared relation into an existing document's frontmatter (or the appropriate drafts path for its workflow).

## 7. Lint the result

```console
$ luria lint
```

Check for:

- unresolved targets,
- wrong target scheme,
- converse inconsistencies,
- invariant failures,
- standing-related findings.

## 8. If the relation forms a longitudinal sequence

Do not maintain a prose lineage by hand.

Define a [chain](chains.md).
