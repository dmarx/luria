---
status: Active
title: 'Remote content endorsed by hash, drift compared offline'
version: 1
tags:
- mechanism
date: '2026-08-27'
issue: '#135'
summary: >-
  A remote document has no status this project can read, so the citation
  checks that keep the local record honest stop at the project boundary. What
  is knowable is whether the cited bytes changed: `luria remotes --pin` stores
  a hash of the content a human endorses, `--refresh` records what upstream
  serves now, and the lint compares the two committed hashes offline — the
  `remote-drift` warning class, cleared by re-endorsing after review. A pin
  is registered per source (`pin = true` on a remote or scheme), per URL (a
  `pin:` flag where it is cited), or per code (an explicit `--pin`), and
  removing the registration retires it.
  Rejected: fetching in the lint (a check that fails on a train), mirroring
  upstream status (a projection of somebody else's record), and hashing
  rendered pages (their markup churns under identical content — a remote
  with stable bytes elsewhere declares the location with `pin_url`, and a
  bare URL is pinned by a `pin:` flag where it is cited).
---

# ADR-tmptuwov: Remote content endorsed by hash, drift compared offline

## Context

A local citation is checked against the document's own frontmatter: retire a
decision and every unacknowledged citation of it is reported. A foreign
reference has nothing to check against — the remote may supersede the
document tomorrow, and the reference here would keep presenting it as
justification indefinitely ([#135](https://github.com/dmarx/luria/issues/135)). Status is upstream's to declare and this
project cannot read it; but "the content I endorsed is still the content
there" is a claim about bytes, and bytes can be hashed.

The constraint that shaped the mechanism is the lockfile's own ([ADR-016](ADR-016.md)): CI,
an offline checkout and a laptop must answer the same question the same way,
so `luria lint` never opens a socket.

## Decision

Store two hashes per pinned document in `remotes.lock.json`. `luria remotes
--pin` fetches a cited document's raw bytes and records their hash as
**endorsed** — a human's claim, which only `--pin` may move. `luria remotes
--refresh` re-fetches every pinned document and records what upstream serves
as **seen**, never touching the endorsement. The lint compares the two
committed hashes offline and reports each disagreement under the
`remote-drift` warning class — reported by default, promotable through
`fail_on` like every other class ([ADR-035](ADR-035.md)).

Re-endorsing is the acknowledgement: review the change upstream, run
`luria remotes --pin CODE`, and both hashes agree again. No comment directive
exists for the class, deliberately — the judgement lives in the lockfile, not
in prose at a citation site, so there is no second place for it to go stale.

What gets hashed is a construction's **stable bytes**, never the page a
reader lands on, resolved through an ordered table of sources
(`luria.pins.SOURCES` — adding a source-specific case is one function and
one entry). A declared `pin_url` template wins: only the project can vouch
that a URL is content-stable, so arXiv's immutable e-print archive can stand
behind the abstract page a reader sees. Otherwise a GitHub file construction
qualifies on its own, re-based onto `raw.githubusercontent.com` so the
fetched bytes are the document rather than the page around it.

Every pin has a **registration** — the thing that says it should exist, and
whose removal retires it — and there is one kind per judgement site.
`pin = true` in config, on a remote or one of its schemes, registers a whole
code family: every cited reference is pinned automatically, and the lint
reports any the lockfile has not endorsed yet, because the judgement "this
record is knowledge we lean on" is made per source, not per citation. A
`pin:` comment directive registers one arbitrary URL where it is cited
(`<!-- pin: https://… — why -->`) — a spec, a dataset card, no code family
behind it. An explicit `luria remotes --pin CODE` registers one ad-hoc pin,
whose lockfile entry is its own registration. A bare `--pin` syncs the
lockfile to the registrations, and a pin whose registration is gone — the
config line deleted, the flag removed, the citation dropped — is reported
and then pruned: committed state that governs nothing is the lockfile's
version of a stale directive, and retiring a noisy pin costs one removal.

One rule keeps the sweep honest: a bare `--pin` never moves an `endorsed`
hash that upstream has drifted from. It records the observation (as
`--refresh` would) and names the explicit command — otherwise one scheduled
sweep would quietly launder every drift finding the lint was about to raise,
and the human review the two-hash design exists to force would never happen.

## Alternatives considered

- **Fetch and compare in the lint** — the obvious one. It makes drift visible
  the moment it happens, and it makes the lint a check that fails on a train
  and answers differently in CI than on a laptop, which is the exact failure
  the lockfile exists to prevent ([ADR-016](ADR-016.md)). Every network observation is an
  explicit command whose output is committed; the lint only ever reads.
- **Mirror upstream status** — read the remote document's frontmatter and
  cache its `status:` locally. It answers the real question directly, but the
  cache is a hand-me-down projection of somebody else's record ([DP-3](../../docs/design-principles.md#dp-3)): stale
  the moment upstream edits, wrong for remotes that are not Luria-shaped, and
  unreadable for private ones. A content hash makes the weaker claim that is
  actually verifiable — *something* changed — and hands the judgement to a
  person, which is where every status judgement in this record already lives
  ([ADR-035](ADR-035.md)).
- **Hash whatever URL the reference constructs** — an arXiv abstract or a
  Jira ticket is a rendered page whose markup churns under identical content,
  so the pin would cry wolf on the site's deploy schedule, and a guard that
  cries wolf is a guard nobody reads ([ADR-016](ADR-016.md)). The command refuses by default
  and says why; a remote that *does* have stable bytes somewhere declares
  the location (`pin_url`), which moves the judgement to the party that can
  actually make it — the same bargain as a `url` template, and the config
  line is the project taking responsibility for the claim.
- **Status quo** — foreign references stay reachability-checked only
  (`--check`), and a superseded upstream decision keeps being presented as
  justification until a reader happens to click through and notice.

## Consequences

Endorsement is opt-in per project and per document; nothing changes for a
record with no pins, and the lockfile's shape is unchanged until the first
`--pin` writes a `pins` section. Drift detection is only as fresh as the last
`--refresh` — a scheduled CI job that runs it and opens a PR with the
lockfile diff is the natural companion, and is left to projects. A pin on a
document-scheme code covers the whole document the anchor lands in, so one
upstream edit can flag several pinned anchors at once; that is conservative
in the right direction. The `seen` hash moves only on successful fetches —
an unreachable document keeps its last observation rather than inventing a
change. The migration sweep ([ADR-040](ADR-040.md)) skips the lockfile entirely: its JSON
nests a remote's prefix away from its tails, so the composed-span mask
cannot tell a foreign key from a local code, and machine-derived state is
re-derived after a migration (`luria remotes --pin`), never re-spelled.
