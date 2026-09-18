---
status: Active
title: 'Every request carries a configured user agent, defaulting to a browser string'
version: 1
tags:
- record
date: '2026-09-18'
summary: >-
  Luria sent `Python-urllib/3.11` — the language and nothing else — from
  three call sites that had already drifted apart. All three now go through
  `fetch.request()`, which carries the project's `user_agent`. The default
  is a generic Firefox string: pragmatic rather than honest, and
  configurable precisely because the honest version is a per-record fact.
  Rejected: a hardcoded `luria/<version>` identity.
---

# ADR-tmpdmtfc: Every request carries a configured user agent, defaulting to a browser string

## Context

Luria opened sockets from three places and announced itself at none of them:

| site | what it did |
|---|---|
| `sources._once` | `urlopen(url)` — the lint's identifier check |
| `remotes._fetch_bytes` | `urlopen(url)` — remote discovery |
| `remotes._head` | `urlopen(Request(url, method="HEAD"))` — the reachability probe |

All three sent `Python-urllib/3.11`, the stdlib default, which names the
language and nothing else: not the tool, not the project, not a way to be
reached.

Two facts shaped the decision. First, **the sites had already drifted**: two
passed a bare URL and one built a `Request` for its `method`, so a header
added to the obvious place would have covered part of luria's traffic and
left the rest anonymous. A tool that identifies itself on two endpoints out
of three has not identified itself.

Second, and worth recording because it was checked rather than assumed: **a
user agent is not what caused the 406s in `#292`.** Under that condition an
explicit UA, an empty UA, `Accept: */*` and `Accept: application/atom+xml`
all returned 406, and all returned 200 once it lifted. This decision and
that one are independent, and neither is evidence for the other.

## Decision

**One builder, `fetch.request()`, and every `urlopen` goes through it.** The
headers luria sends are now a single fact rather than a habit repeated three
times (`DP-004`), and the module exists so that the next call site has an
obvious thing to call.

**The default is a generic Firefox string.** This is a pragmatic choice, not
an honest one, and it is recorded as such: a browser string is what gets
served, and it is also what a rate-limiter is trying to see through.

**What makes that defensible is the `user_agent` setting**, which is the
substance of this decision rather than a convenience on top of it. The honest
identity belongs to the project, not to luria: a contact address is a
per-record fact, and the form some hosts actually ask for — CrossRef's polite
pool wants a real mailbox — cannot be supplied by a default at all. So the
tool ships the string that works and gives every project one line to say who
it really is.

## Alternatives considered

- **A hardcoded `luria/<version> (+https://github.com/dmarx/luria)`.** The
  polite option, and it was the first proposal. It loses because it is the
  wrong thing to hardcode: it identifies the *tool* when what a host wants is
  the *operator*, so every project would announce the same contact for
  traffic none of them shares. Making it configurable keeps this available —
  a project that wants it writes it — while not imposing luria's identity on
  a record's traffic.
- **Keep the stdlib default.** Free, and it is the traffic a metadata host
  rations first. It also leaves nothing for a project to change.
- **A UA as the fix for `#292`.** Tested and rejected on evidence; see
  Context. Shipping it as a throttling fix would have left a future reader
  believing the wrong cause.
- **Per-remote user agents**, so one host could get a contact address and
  another a browser string. Real hosts differ in what they want, so this is
  not absurd — but nothing here needs it yet, and a per-remote key is easy to
  add later and hard to remove.

## Consequences

**Luria's traffic is now identifiable at one place and changeable in one
line.** `luria.user_agent` in `luria.yaml`, documented in the generated
config reference — luria's own `test_every_scalar_key_is_described` failed
until that prose existed, which is the check doing its job.

**The default misrepresents what luria is**, and a project that cares should
override it. That is a real cost and is the reason this ADR says so in the
title rather than in a footnote: someone reading a server log will see a
browser, and the record should not be the only place that fact is written
down.

**A fourth call site is now a one-liner** — `request(url)` rather than a
header dict copied from somewhere. That was the point of extracting the
module rather than adding a header three times.
