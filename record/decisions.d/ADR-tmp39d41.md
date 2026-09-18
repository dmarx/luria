---
status: Active
title: 'A 406 from a metadata remote is a throttle, not an outage'
version: 1
tags:
- record
date: '2026-09-18'
issue: '#292'
summary: >-
  arXiv returns 406 and 429 interchangeably for the same identifier seconds
  apart when it is shedding load. `_once` classified 406 as `unreachable`,
  which skips the retry and — the part that cost something — never trips the
  circuit breaker, so a sustained refusal bought one socket per unverified
  identifier every run. 406 now classifies as `throttled`. Rejected: a
  fourth status, and leaving the RFC reading in place.
---

# ADR-tmp39d41: A 406 from a metadata remote is a throttle, not an outage

## Context

Eight identifiers in a downstream record sat unverified for hours, reported as:

```
record/literature.d/LIT-394.md:12: `arxiv: 1207.0580` could not be checked — unreachable — HTTP 406
```

arXiv was up throughout. `curl` to the identical URL returned 200 during the
same window. The wording sent the first reader chasing a request-construction
bug — user-agent, then `Accept`, then `Accept-Encoding` — and none of it was
the cause: `urllib` with an explicit UA, an empty UA, `Accept: */*` and
`Accept: application/atom+xml` all returned 406 while the condition held and
200 after it lifted.

What settled it was catching the condition live on the endpoint
`uris.title` configures, three attempts two seconds apart:

```
1207.0580  try0: HTTP 406   try1: HTTP 406   try2: HTTP 406
2409.19256 try0: HTTP 406   try1: HTTP 429   try2: HTTP 429
```

**The same identifier returns 406 and 429 seconds apart.** The host is using
the two interchangeably to shed load. `Retry-After` is absent on both.

`_once` classified `404`/`410` as `absent`, `429`/`503` as `throttled`, and
everything else as `unreachable`. Two behaviours hang off that split, and
both were designed deliberately:

- `_fetch` returns immediately on `unreachable`, so no `Retry-After` is
  honoured. Moot here, since arXiv sends none.
- `ask` populates `_REFUSING` only on `throttled`. **This is the one that
  cost something.** Under a sustained refusal luria opened one socket per
  unverified identifier, against a host already rationing — precisely what
  that breaker's own docstring says it exists to prevent, sitting out the
  case it was built for.

## Decision

**406 joins 429 and 503 in the `throttled` branch.**

This is a classification on evidence rather than on the RFC, which reads 406
as content negotiation, and the trade is worth stating rather than burying.
It is defensible because of what luria's own request construction guarantees:
every request is built from a remote's declared `uris.title` template and
sends no `Accept` header to argue about. There is nothing here for a server
to negotiate away, so a 406 from this code path is not a negotiation failure
of ours.

The invariant a future change must not break: **a status that means "the host
answered and declined" must trip the breaker.** The retry is incidental; the
breaker is the point.

## Alternatives considered

- **Leave 406 as `unreachable`, per the RFC.** Correct by specification and
  wrong in practice. It also keeps the misleading report — "unreachable"
  describes a host that did not answer, and this host answered.
- **A fourth status for "refused, reason unclear"**, retrying once and
  tripping the breaker. Same behaviour, more code, and a fourth word to
  explain in a vocabulary whose value is that it has three.
- **Sniff the response body** to tell a throttle from a negotiation failure.
  Requires reading a body luria has no schema for, from a remote it does not
  control, and would be one more thing to maintain per remote.
- **Status quo.** Costs a wrong diagnosis every time the condition recurs —
  measured once at roughly an hour of a reader's time — plus a round trip per
  identifier against a host that is asking for fewer.

## Consequences

**A remote that really does mean 406 the orthodox way now reports a throttle
that never clears.** That is louder than the `unreachable` it used to get, so
the reclassification does not hide the case it trades away.

**The report wording fixes itself.** The lint composes its reason as
`f"{got.status} — {got.detail}"`, so the line above becomes `could not be
checked — throttled — HTTP 406` with no separate change. A reader now sees a
host that is rationing rather than one that is down.

**The breaker does the work.** With `Retry-After` absent, reclassifying
changes nothing about waiting and everything about stopping: the first
identifier asks, and every later one in the run reads the cached
`"…; not asked again this run"`.

**Not verified:** whether other remotes in the wild use 406 this way. The
argument above rests on what luria's request construction guarantees, so it
does not depend on the answer, but it is an assumption rather than a finding.
