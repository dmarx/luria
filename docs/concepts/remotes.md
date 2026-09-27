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

A remote can also describe a non-Luria namespace: a `uid` pattern says what one of its identifiers looks like, and a `url` template says where it lives (ADR-024).

Examples:

- arXiv IDs,
- issue keys,
- standards identifiers,
- DOI-like identifiers.

The record can then treat those references structurally rather than as handwritten URLs.

## Network policy

Remote checking has a different failure surface from local checking.

A remote can also declare how to ask what one of its identifiers *is* — for example, the title upstream gives a paper — so the lint can report a citation whose identifier names a different document than the one filed (ADR-080). What upstream said is recorded in `remotes.lock.json`.

`lint.network` in `luria.yaml` says how far the lint may reach to check that:

- `auto` (the default) asks only about identifiers the lockfile has no answer for, and reports them unchecked when the network is not there,
- `never` answers from the lockfile alone — the hermetic build,
- `require` makes an unreachable remote a failure, so a green run means the references were verified rather than remembered.

Whatever the setting, the lint never writes the lockfile. `luria remotes --resolve` does, and it runs where merges serialize — the default-branch generation job — so concurrent branches do not collide on one shared file and a branch's result does not depend on one contributor's network (ADR-112).

## Pinning

Some external dependencies need a stronger statement than:

> this identifier still resolves.

A pin says:

> the external content I depended on had this content identity.

`luria remotes --pin` fetches the document and records the hash of its bytes as **endorsed**. `luria remotes --refresh` re-fetches and records what upstream serves now as **seen**. The lint never fetches for pins: it compares the two committed hashes, offline, and reports each pinned document whose content moved on as `remote-drift` (ADR-066). So drift shows up once a `--refresh` has recorded the new hash and it is committed, not the moment upstream changes.

Reviewing the change and running `luria remotes --pin CODE` again is the acknowledgement: it endorses the new content, and the two hashes agree.

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
