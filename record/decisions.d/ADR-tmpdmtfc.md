---
status: Active
title: 'Every request names the software and no contact, and the project adds the rest'
version: 1
tags:
- record
date: '2026-09-18'
summary: >-
  Luria sent `Python-urllib/3.11` — the language and nothing else — from
  three call sites that had already drifted apart. All three now go through
  `fetch.request()`, which carries the project's `user_agent`. The default
  is `luria/<version>`: honest about the software, and carrying no contact,
  because a shipped contact routes every user's traffic to whoever
  maintains luria. Rejected: a browser string, and a hardcoded project URL.
---

# ADR-tmpdmtfc: Every request names the software and no contact, and the project adds the rest

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

**The default is `luria/<version>` and deliberately nothing more.** Two
constraints meet here and the string satisfies both. It is honest about the
software — the shape `curl/8.0` and `Wget/1.21` have used for decades — so a
host reading a log sees what is actually calling it. And it carries **no
contact**, because a URL or a mailbox in a shipped default routes every
user's traffic to whoever happens to maintain luria: a person who did not
agree to that, and who is not the operator a host wants to reach anyway.

**The contact is the project's to add**, which is what the `user_agent`
setting is for and the substance of this decision rather than a convenience
on top of it. The form some hosts ask for — CrossRef's polite pool wants a
real mailbox — is a per-record fact that no default can supply.

The version is read from installed distribution metadata rather than from
`luria.__version__`, which was a hand-written `"0.1.0"` that had been wrong
for twenty-seven releases (`#295`). A header being honest about the software
should not misreport its version in the same breath; that line is now derived
too.

## Alternatives considered

- **`luria/<version> (+https://github.com/dmarx/luria)`.** The polite
  option, and the first proposal. It loses on the same ground the browser
  string does, from the other direction: it identifies the *tool* when a host
  wants the *operator*, so every project using luria would point complaints
  at one maintainer for traffic none of them sent. A contact nobody consented
  to publish is not politeness. A project that wants that URL can write it.
- **A generic browser string** (`Mozilla/5.0 … Firefox/128.0`). Gets served,
  and was the shipped default in the first draft of this change. It loses
  because it is a lie told to the party least able to check it, and it is
  what a rate-limiter is specifically trying to see through — so it buys
  goodwill now at the cost of being the traffic a host blocks by pattern
  later. It also forfeits the one benefit that motivated setting an agent at
  all.
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

**No project gets the polite-pool treatment without opting in.** A default
that named a contact would earn it for everyone at once; this one earns it
for nobody until a record writes its own address. That is the cost of not
publishing a maintainer's inbox on other people's behalf, and it is the right
side to err on — the setting is one line, and a project that cares will find
it in the config reference.

**A fourth call site is now a one-liner** — `request(url)` rather than a
header dict copied from somewhere. That was the point of extracting the
module rather than adding a header three times.
