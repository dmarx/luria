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

A remote can also describe a non-Luria namespace: a `uid` pattern says what one of its identifiers looks like, and a `url` template says where it lives ([ADR-024](../../record/decisions.d/ADR-024.md)).

Examples:

- arXiv IDs,
- issue keys,
- standards identifiers,
- DOI-like identifiers.

The record can then treat those references structurally rather than as handwritten URLs.

## Hermeticity

Remote checking has a different failure surface from local checking: the network may be down, and upstream may change underneath a record that did not.

A remote can declare how to ask what one of its identifiers *is* — the title upstream gives a paper, say — so a citation whose identifier names a different document than the one filed can be reported ([ADR-080](../../record/decisions.d/ADR-080.md)). What upstream answered is recorded in a committed lockfile, so a check can be answered from the record instead of the network. A project chooses how far the lint may reach: from "never, answer from the record alone" to "always, and fail if you cannot".

The lint asks; it does not record. The answers are written in one place, where merges serialize, so concurrent branches do not collide on one shared file and a branch's result does not depend on one contributor's network ([ADR-112](../../record/decisions.d/ADR-112.md)).

## Pinning

Some external dependencies need a stronger statement than:

> this identifier still resolves.

A pin says:

> the external content I depended on had this content identity.

A pin keeps two facts apart: the content the record **endorsed**, and the content upstream was last **seen** serving. Drift is the difference between them, compared offline from what the record has committed rather than by fetching during the lint ([ADR-066](../../record/decisions.d/ADR-066.md)). Re-endorsing after review is the acknowledgement. The commands are in [Reference remote knowledge](../how-to/remotes.md).

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
