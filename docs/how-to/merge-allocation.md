# How to use merge-time identity allocation

Sequential numbers are globally ordered. Distributed branches are not.

If several branches can create records concurrently, allocating permanent numbers at filing time can produce collisions.

Luria can represent provisional identity explicitly.

## Configure merge allocation

For a scheme:

```yaml
schemes:
  ADR:
    allocate: merge
```

## Create records normally

```console
$ luria new ADR --title "..."
```

The new entry receives a visibly temporary code rather than pretending its global sequence number is already known.

The temporary identity is first-class on the branch: it can be linted, indexed, and cited.

This behavior is governed by [ADR-049](../../record/decisions.d/ADR-049.md) ([ADR-049](../../record/decisions.d/ADR-049.md)).

## Concretize where merges serialize

At the merge queue / merge-to-main serialization point:

```console
$ luria concretize
```

Luria assigns permanent numbers, renames source files, rewrites references, and preserves the temporary spelling as a former identity/alias so old citations do not become dead names.

## Guard the trunk

```console
$ luria concretize --check
```

Use this where a temporary code on the serialized branch should be considered mechanically fixable and therefore inadmissible.

## Why this is a product feature

The point is not merely avoiding filename collisions.

The record distinguishes:

```text
provisional identity
```

from:

```text
serialized permanent identity
```

instead of encoding a distributed guess as if it were globally authoritative.
