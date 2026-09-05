---
status: Active
title: A remote declares how to ask what an identifier is, and the lint compares offline
version: 1
tags:
- mechanism
date: '2026-09-05'
issue: '#166'
summary: >-
  53 of 139 arXiv identifiers in one record resolved to real papers on
  unrelated subjects and stayed green for two years, because every check
  asked whether a reference points somewhere and none asked whether it points
  where it says. `uris.title` plus `title_re` say how to ask; `--resolve`
  records the answer in the lockfile; the lint compares offline. Rejected:
  fetching in the lint, guessing the metadata API per host, and fuzzy title
  matching.
---

# ADR-tmpjg0jj: A remote declares how to ask what an identifier is, and the lint compares offline

## Context

The lint's reference vocabulary — `unresolved-codes`, `broken-targets`,
`retired-citations` — asks one question in three shapes: does this pointer
resolve? `remote-drift` asks a fourth: have the bytes behind an endorsed pin
changed since a human vouched for them?

None of them asks whether an identifier and the document carrying it were
ever about the same thing. In `anthology-of-the-sota`, **53 of 139 `arxiv:`
identifiers did not resolve to the paper the note named**: quantum secret
sharing filed as the PaLM 2 technical report, electron losses in hypersonic
flows filed as checkpointing advice, chromatic number and Hamiltonicity filed
as compiler optimization.

None of these was a typo. Every one was syntactically valid, in a plausible
year range, and in the right format — `2111.09432` reads as a late-2021
systems paper unless you fetch it. That is why two years of review missed
them, and why the failure is worth a check rather than a convention.

The gap also falsifies a claim that record makes about itself, in the
principle this whole mechanism serves: that the remotes "turn those ids into
resolvable references rather than strings, so 'cite the paper' and 'the
citation resolves' are the same check rather than two". They were two.
Resolution was available and never performed.

## Decision

A remote declares how to ask what one of its identifiers is:

    [luria.remotes.ARXIV]
    uris.title = "https://export.arxiv.org/api/query?id_list={1}.{2}"
    title_re   = "<entry>.*?<title>(.*?)</title>"

`uris.title` is one more name in the URI table `read` and `bytes` already
live in — the table's docstring anticipated this: "a relation Luria does not
ship yet is one more name". `title_re`'s first capture group is the title.

`luria remotes --resolve` fetches each one and records what came back in
`remotes.lock.json`. `luria lint` reads the committed file and compares,
offline, against the document's own `title:`. Disagreement is
`source-mismatch`; `source-ok:` acknowledges a deliberate one.

Which fields hold identifiers needs no new configuration: a frontmatter key
equal to a remote's prefix, lowercased. A project that declared `ARXIV` has
already said what `arxiv:` means.

## Alternatives considered

**Fetch in the lint.** The obvious shape and the one the architecture
forbids: "a check that reaches the network is a check that fails on a train"
([ADR-016](ADR-016.md)). It would also make the finding unreviewable — a mismatch would
appear and vanish with connectivity, and no diff would ever show it. The
pins pattern already solved this, and copying it cost nothing.

**Guess the metadata API from the host.** `arxiv.org` → the Atom API,
`doi.org` → Crossref, and a project would configure nothing. Rejected for the
reason `pin_url` is declared rather than derived: only the project can vouch
that a URL serves what it appears to, and a guess that silently stops
matching when a provider changes its response shape fails *closed* — the
lockfile gains no entry, and no entry reads exactly like agreement. A check
that quietly stops checking is worse than one that was never installed.

**Fuzzy matching on similarity.** Would forgive the 22 cosmetic cases in that
record automatically — a dropped subtitle, a nickname the project prefers.
Rejected because it converts a mechanical check into a judgement call, and
the standing rule is that a check joins the lint only when the violation is
always wrong and mechanically fixable. "The recorded title is not the
resolved title" is mechanical; "the recorded title is 0.82 similar" is a
threshold argument in every future review. The directive puts the judgement
on a person, once, with a reason, where the disagreement is.

**Report unresolved identifiers too.** Rejected: a project that has never run
`--resolve` would see every document become a finding at once, which teaches
people to run the command to silence the lint rather than to read what it
says. Absence from the lockfile means the check has no opinion.

## Consequences

No project's output changes until it declares `uris.title` on a remote and
runs `--resolve`. The lockfile grows a `titles` section, which `write_lock`
preserves like the others.

The check is deliberately shallow: it compares titles, not authors or years,
because the title is the field a record already carries for its own reasons
and therefore the one that cannot drift out of maintenance. A record that
wants author and date checked can add them later against the same lockfile
entries; the fetch already has them in hand.
