#!/usr/bin/env python3
"""Content pins: remote knowledge endorsed by hash (#135).

A remote document has no status this project can read — upstream may retire
it tomorrow and nothing here would know. What CAN be known is whether its
bytes changed: `luria remotes --pin` stores a hash of the content being
endorsed, `--refresh` records what upstream serves now, and `luria lint`
compares the two committed hashes — offline, like every other check —
reporting each pinned document that moved on since a human last vouched for
it (the `remote-drift` warning class). Re-endorsing after review
(`luria remotes --pin LU-ADR-013`) is the acknowledgement.

The pins live in `remotes.lock.json` beside the discovered filenames, for the
same reason those do (ADR-016): CI, an offline checkout and a laptop have to
answer "did this change?" the same way, so the network work happens in
explicit commands whose output is committed, and the lint only ever reads.

Where stable bytes live
-----------------------
Hashing the URL a *reader* lands on is wrong whenever that page is a
rendering — an arXiv abstract, a Jira ticket — whose markup churns under
identical content: the pin would cry wolf on the site's deploy schedule, and
a guard that cries wolf is a guard nobody reads (ADR-016). So a pin hashes a
different URL, resolved by `stable_url()` through `SOURCES`: an ordered table
of rungs, each answering "where do this construction's stable bytes live?"
or "" when it has nothing to say. The first answer wins.

`SOURCES` is the extension point. A new source-specific case — a forge with
its own raw scheme, a service with a canonical bytes endpoint — is one
function and one table entry; everything downstream (endorsing, refreshing,
drift reporting) consumes only the returned URL and never asks where it came
from. Today's rungs, strongest first:

1. **A declared `pin_url` template** (`Remote.pin_link`) — only the project
   can vouch that a URL is content-stable, so the declaration beats any
   construction.
2. **The GitHub rebase** — a `github.com/.../blob/...` construction re-based
   onto raw.githubusercontent.com, so the bytes are the document rather than
   GitHub's page around it.
"""

from __future__ import annotations

import hashlib
import re
import sys

from . import remotes
from .config import Remote, current

# ── Where stable bytes live ──────────────────────────────────────────────

BLOB_URL_RE = re.compile(r"https://github\.com/([^/]+/[^/]+)/blob/([^/#]+)/(.+)")


def _declared(remote: Remote, code: str) -> str:
    """Rung 1: the project's own `pin_url` declaration (#135)."""
    return remote.pin_link(code)


def _github_raw(remote: Remote, code: str) -> str:
    """Rung 2: a GitHub file construction, re-based onto raw bytes.

    The anchor a document scheme appends is dropped: a fragment selects
    nothing server-side, and the endorsement covers the document the anchor
    lands in."""
    m = BLOB_URL_RE.fullmatch(remotes.link(remote, code).split("#")[0])
    if not m:
        return ""
    owner_repo, ref, path = m.groups()
    return f"https://raw.githubusercontent.com/{owner_repo}/{ref}/{path}"


SOURCES = (_declared, _github_raw)


def stable_url(remote: Remote, code: str) -> str:
    """The URL whose bytes ARE the document, or "" when no source knows one."""
    for source in SOURCES:
        if url := source(remote, code):
            return url
    return ""


def content_hash(body: bytes) -> str:
    """`sha256:<hex>` — prefixed so a future algorithm change is visible in
    the lockfile rather than silently comparing across algorithms."""
    return "sha256:" + hashlib.sha256(body).hexdigest()


# ── The committed state ──────────────────────────────────────────────────


def state() -> dict[str, dict[str, dict[str, str]]]:
    """The committed content pins: {prefix: {code: {endorsed, seen}}} (#135).

    `endorsed` is the hash of the content a human vouched for; `seen` is what
    upstream served at the last `--refresh`. The two disagreeing is the whole
    signal, and it lives in the lockfile so `luria lint` can read it offline."""
    return remotes._read_lockfile().get("pins", {})


def _copy(pinned: dict) -> dict:
    return {p: {c: dict(e) for c, e in entries.items()}
            for p, entries in pinned.items()}


# ── The operations ───────────────────────────────────────────────────────


def pin_codes(requested: tuple[str, ...]) -> None:
    """Endorse remote content: fetch each document, store its hash (#135).

    With codes, endorse exactly those — which is also how a reviewed change
    is endorsed again. With none, endorse every cited code that has stable
    bytes to fetch, and drop pins whose code is no longer cited, so the
    committed state keeps describing the record that exists."""
    cfg = current()
    pinned = _copy(state())
    targets: list[tuple[Remote, str]] = []
    if requested:
        for text in requested:
            parsed = remotes.parse_code(text)
            if parsed is None:
                # No silent refusal (DP-1): an unparseable code pins nothing,
                # and saying so beats a lockfile that quietly didn't change.
                print(f"{text}: no configured remote matches — nothing to pin",
                      file=sys.stderr)
                continue
            targets.append(parsed)
    else:
        refs = remotes.cited()
        targets = [(cfg.remotes[prefix], code) for prefix in sorted(refs)
                   for code in sorted(refs[prefix])]
        for prefix in list(pinned):
            remote = cfg.remotes.get(prefix)
            delim = remote.delim if remote else "-"
            for code in list(pinned[prefix]):
                if code not in refs.get(prefix, set()):
                    del pinned[prefix][code]
                    print(f"{prefix}{delim}{code}: no longer cited — "
                          "pin dropped")
    for remote, code in targets:
        composed = f"{remote.prefix}{remote.delim}{code}"
        url = stable_url(remote, code)
        if not url:
            reason = ("the construction is not a GitHub file, so nothing "
                      "here knows where its stable bytes live — a `pin_url` "
                      "template on the remote declares it"
                      if remotes.link(remote, code)
                      else "it names no document there")
            print(f"{composed}: not pinned — {reason}", file=sys.stderr)
            continue
        body, why = remotes._fetch_bytes(url)
        if why:
            print(f"{composed}: not pinned — {why} ({url})", file=sys.stderr)
            continue
        digest = content_hash(body)
        entry = pinned.get(remote.prefix, {}).get(code)
        told = ("unchanged" if entry and entry.get("endorsed") == digest
                else "endorsed again" if entry else "pinned")
        pinned.setdefault(remote.prefix, {})[code] = {
            "endorsed": digest, "seen": digest}
        print(f"{composed}: {told} at {digest[:19]}…")
    path = remotes.write_lock(pinned=pinned)
    print(f"wrote {cfg.rel(path)}")


def refresh_seen() -> list[str]:
    """Re-fetch every pinned document and record what upstream serves now in
    `seen` — never touching `endorsed`, which only `--pin` moves. Returns the
    codes that drifted; the committed diff is what lets `luria lint` warn
    offline (#135)."""
    cfg = current()
    pinned = _copy(state())
    if not pinned:
        return []
    drifted: list[str] = []
    for prefix, entries in sorted(pinned.items()):
        remote = cfg.remotes.get(prefix)
        if remote is None:
            continue                  # `drift_lines` reports the orphan pin
        for code, entry in sorted(entries.items()):
            url = stable_url(remote, code)
            if not url:
                continue              # no stable construction; nothing to observe
            body, why = remotes._fetch_bytes(url)
            if why:
                # An unreachable document is not a changed one — keep the
                # last observation rather than inventing a new claim.
                print(f"{prefix}{remote.delim}{code}: seen hash kept — {why}")
                continue
            entry["seen"] = content_hash(body)
            if entry["seen"] != entry.get("endorsed"):
                drifted.append(f"{prefix}{remote.delim}{code}")
    remotes.write_lock(pinned=pinned)
    return drifted


def drift_lines() -> list[str]:
    """Every pin out of step with the record — from the committed lockfile
    alone, so the lint that reads this stays a check that passes on a train.
    The network work happened earlier: `--pin` recorded the endorsement,
    `--refresh` recorded what upstream serves, and this compares."""
    cfg = current()
    pinned = state()
    if not pinned:
        return []
    refs = remotes.cited()
    lines: list[str] = []
    for prefix, entries in sorted(pinned.items()):
        remote = cfg.remotes.get(prefix)
        delim = remote.delim if remote else "-"
        for code, entry in sorted(entries.items()):
            composed = f"{prefix}{delim}{code}"
            if remote is None:
                lines.append(f"{composed}: pinned, but no remote {prefix!r} "
                             "is configured — `luria remotes --pin` prunes it")
            elif code not in refs.get(prefix, set()):
                lines.append(f"{composed}: pinned, but nothing cites it any "
                             "more — `luria remotes --pin` prunes it")
            elif entry.get("seen") != entry.get("endorsed"):
                lines.append(
                    f"{composed}: upstream content changed since it was "
                    f"endorsed — review {remotes.link(remote, code)}, then "
                    f"`luria remotes --pin {composed}` to endorse it again")
    return lines
