# Concept: External knowledge and remotes

Not every identity a record depends on is locally owned.

Luria remotes let foreign identities participate in the local reference model without pretending the local repository is their authority.

## Another Luria record

A remote prefix can identify a foreign record whose schemes are cited from this one.

Conceptually:

```text
local claim
   ↓
LU-ADR-013
   ↓
foreign record
```

The composed code preserves ownership.

## Arbitrary identifier namespaces

A remote can also describe a non-Luria namespace using recognition and URL rules.

Examples:

- arXiv IDs,
- issue keys,
- standards identifiers,
- DOI-like identifiers.

The record can then treat those references structurally rather than as handwritten URLs.

## Network policy

Remote checking has a different failure surface from local checking.

A project may choose whether lint:

- uses the network when needed,
- remains hermetic and trusts a lock/cache,
- requires successful remote verification.

The policy should make clear what a green lint actually guarantees.

## Pinning

Some external dependencies need a stronger statement than:

> this identifier still resolves.

A pin says:

> the external content I depended on had this content identity.

If upstream content changes, the local record can surface drift.

That extends truth maintenance across repository boundaries:

```text
local claim
    ↓ depends on
external content
    ↓ changes
local review needed
```

## Authority remains external

A remote reference is not imported ownership.

The local record can cite, check, and pin what it depends on while preserving the fact that the source of authority lives elsewhere.
