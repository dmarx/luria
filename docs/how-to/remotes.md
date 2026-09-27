# How to reference remote knowledge

Use a remote when the local record depends on identities owned elsewhere.

## Another Luria record

Declare a remote prefix for the foreign record.

Local citations can then compose the remote prefix with the foreign scheme/code rather than pretending the object is local.

## Arbitrary identifier namespace

For identifiers such as arXiv IDs or issue keys, define the recognition rule and URL template in the remote configuration.

This turns handwritten URLs into structured identifiers.

## Refresh/check remote knowledge

Use:

```console
$ luria remotes --help
```

for the current remote discovery/checking workflow.

The record may maintain resolved remote information in a lock/cache so hermetic checks and network-aware checks have explicit semantics.

## Choose a network policy

The lint configuration can distinguish:

- opportunistic network checking,
- no network,
- required network verification.

Document the policy in CI so a green build has a clear meaning.

## Pin content when identity alone is not enough

When your claim depends on the actual content of a foreign source rather than merely its continued existence, use the pinning mechanism/directive.

A later upstream content change should then become a local finding.

That extends truth maintenance beyond repository boundaries.
