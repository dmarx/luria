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

Every pin has a REGISTRATION — the thing that says it should exist, and whose
removal retires it. Three kinds, one per judgement site: `pin = true` in
config (on a remote or one of its schemes) registers a whole code family, so
each cited reference is pinned automatically and the lint reports any the
lockfile has not endorsed yet; a `pin:` comment directive registers one
arbitrary URL where it is cited (`<!-- pin: https://… — why it matters -->`,
see `flagged_urls`) — a spec, a dataset card, a post the design leans on; and
an explicit `luria remotes --pin CODE` registers one ad-hoc pin, for which
the lockfile entry itself is the registration. A bare `--pin` syncs the
lockfile to the registrations; deleting one — the config line, the comment,
the entry — retires its pins, so one that fires too often costs one removal.

Where stable bytes live
-----------------------
Hashing the URL a *reader* lands on is wrong whenever that page is a
rendering — an arXiv abstract, a Jira ticket — whose markup churns under
identical content: the pin would cry wolf on the site's deploy schedule, and
a guard that cries wolf is a guard nobody reads (ADR-016). So a pin hashes a
different URI under the same code: the `bytes` name in the remote's URI
table, rendered by the same machinery as the reader's `read` link. A
declared `uris.bytes` (or its `pin_url` sugar) wins at either level; where
`read` resolves by construction, `bytes` defaults to the forge's raw
counterpart of the same shape; where a template governs `read`, no bytes are
guessed — declaring them is the project vouching that the URL is
content-stable.
"""

from __future__ import annotations

import hashlib
import sys

from . import remotes
from .config import Remote, current

# ── Where stable bytes live ──────────────────────────────────────────────


def stable_url(remote: Remote, code: str) -> str:
    """The URL whose bytes ARE the document — the code's `bytes` URI.

    One rendering call: `remotes.construct` supplies the lockfile's word on
    {filename}, `Remote.uri` applies the precedence (a declared template at
    either level, then the default derived from the same shape `read`
    constructs by — GitHub's raw scheme as a shipped template, not a regex
    over a rendered URL). "" means no source vouches for stable bytes: a
    rendered page's markup churns under identical content, so a hash of it
    would drift on its own schedule and the pin would cry wolf (ADR-016).
    A source-specific case — another forge, a service's canonical bytes
    endpoint — is a `uris.bytes` template in config, or one more entry in
    `config._DEFAULT_URIS`; everything downstream consumes only the URL."""
    return remotes.construct(remote, code, "bytes")


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


def url_state() -> dict[str, dict[str, str]]:
    """The committed URL pins: {url: {endorsed, seen}} — the same two-hash
    bargain for content that is not a foreign code at all."""
    return remotes._read_lockfile().get("urls", {})


def _copy(pinned: dict) -> dict:
    return {p: {c: dict(e) for c, e in entries.items()}
            for p, entries in pinned.items()}


# ── URL flags ────────────────────────────────────────────────────────────

PIN = "pin"


def flagged_urls(files=None) -> tuple[set[str], list[str]]:
    """URLs a `pin:` directive marks for endorsement, and the directives that
    mark nothing.

        <!-- pin: https://spec.test/v1.html — the spec this implements -->
        We follow [the spec](https://spec.test/v1.html).

    Not every load-bearing citation is a foreign code: a spec, a blog post,
    a dataset card. The flag lives where the URL is cited — same scopes as
    every directive — and it IS the pin's registration: `luria remotes
    --pin` endorses what is flagged, and removing the flag is how a pin is
    retired (the next bare `--pin` prunes it). A pin that fires too often
    costs one deleted comment, and the URL goes back to being an ordinary,
    unwatched link.

    The directive's own comment is blanked before checking what it governs —
    otherwise every flag would satisfy itself with the URL in its own text,
    and a flag whose citation was deleted could never report itself stale."""
    from . import directives, ref_status
    cfg = current()
    flagged: set[str] = set()
    problems: list[str] = []
    for path in files if files is not None else ref_status.scanned_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = directives.find(path, text, {PIN})
        if not found:
            continue
        chars = list(text)
        for d in found:
            for i in range(max(0, d.span[0]), min(len(chars), d.span[1])):
                if chars[i] != "\n":
                    chars[i] = " "
        lines = "".join(chars).splitlines()
        for d in found:
            problem = directives.problems(d)
            if problem:
                problems.append(f"{cfg.rel(path)}:{d.line}: {problem}")
                continue
            for arg in d.args:
                if not arg.startswith(("http://", "https://")):
                    problems.append(
                        f"{cfg.rel(path)}:{d.line}: `pin` names {arg}, which "
                        "is not a URL — a foreign code is pinned with "
                        f"`luria remotes --pin {arg}`, no flag needed")
                elif any(arg in line for n, line in enumerate(lines, 1)
                         if d.covers(n)):
                    flagged.add(arg)
                else:
                    problems.append(
                        f"{cfg.rel(path)}:{d.line}: `pin` names {arg}, which "
                        "appears nowhere the directive governs")
    return flagged, problems


def flag_problems() -> list[str]:
    """`pin:` directives that register nothing — the lint's stale-directives
    section reads these, same bargain as every other directive (DP-1)."""
    return flagged_urls()[1]


# ── The operations ───────────────────────────────────────────────────────


def endorse(requested: tuple[str, ...]) -> None:
    """Endorse remote content: fetch each document, store its hash (#135).

    With arguments — codes or flagged URLs — endorse exactly those, which is
    also the ONLY way a drifted pin is endorsed again. With none, sync the
    lockfile to what is registered: every cited code the config declares
    pinned (`pin = true` on a remote or one of its schemes), every existing
    pin that is still cited, and every `pin:`-flagged URL — and drop pins
    nothing cites or flags any more, so the committed state keeps describing
    the record that exists. A bare run never moves an `endorsed` hash that
    upstream has drifted from: it records the observation and names the
    explicit command, because a scheduled sweep must not quietly launder the
    findings the lint was about to raise."""
    cfg = current()
    pinned = _copy(state())
    url_pinned = {u: dict(e) for u, e in url_state().items()}
    flagged, _ = flagged_urls()
    targets: list[tuple[Remote, str]] = []
    url_targets: list[str] = []
    if requested:
        for text in requested:
            if text.startswith(("http://", "https://")):
                if text in flagged:
                    url_targets.append(text)
                else:
                    # The flag is the registration — a pin the prose doesn't
                    # carry would be invisible exactly where it governs.
                    print(f"{text}: not pinned — no `pin:` directive flags "
                          "it; add one where the URL is cited",
                          file=sys.stderr)
                continue
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
        for prefix in sorted(refs):
            remote = cfg.remotes[prefix]
            for code in sorted(refs[prefix]):
                # Registered by config, or already pinned (an explicit `--pin
                # CODE` once made the lockfile entry its own registration).
                if remote.auto_pin(code) or code in pinned.get(prefix, {}):
                    targets.append((remote, code))
        for prefix in list(pinned):
            remote = cfg.remotes.get(prefix)
            delim = remote.delim if remote else "-"
            for code in list(pinned[prefix]):
                if code not in refs.get(prefix, set()):
                    del pinned[prefix][code]
                    print(f"{prefix}{delim}{code}: no longer cited — "
                          "pin dropped")
        url_targets = sorted(flagged)
        for url in list(url_pinned):
            if url not in flagged:
                del url_pinned[url]
                print(f"{url}: no `pin:` directive flags it — pin dropped")
    explicit = bool(requested)
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
        _endorse_one(composed, url, pinned.setdefault(remote.prefix, {}),
                     code, explicit)
    for url in url_targets:
        _endorse_one(url, url, url_pinned, url, explicit)
    path = remotes.write_lock(pinned=pinned, urls=url_pinned)
    print(f"wrote {cfg.rel(path)}")


def _endorse_one(label: str, url: str, into: dict, key: str,
                 explicit: bool) -> None:
    """Fetch one document's stable bytes and record the endorsement.

    A change since the last endorsement is endorsed only by an explicit act:
    a bulk run records it as `seen` — the same observation `--refresh` makes
    — and says which command endorses it, so drift always crosses a human's
    desk before the record vouches for it again."""
    body, why = remotes._fetch_bytes(url)
    if why:
        tail = "" if url == label else f" ({url})"
        print(f"{label}: not pinned — {why}{tail}", file=sys.stderr)
        return
    digest = content_hash(body)
    entry = into.get(key)
    if entry and entry.get("endorsed") != digest and not explicit:
        into[key] = {"endorsed": entry["endorsed"], "seen": digest}
        print(f"{label}: changed since endorsed — kept for review; "
              f"`luria remotes --pin {label}` endorses the change")
        return
    told = ("unchanged" if entry and entry.get("endorsed") == digest
            else "endorsed again" if entry else "pinned")
    into[key] = {"endorsed": digest, "seen": digest}
    print(f"{label}: {told} at {digest[:19]}…")


def refresh_seen() -> list[str]:
    """Re-fetch every pinned document and record what upstream serves now in
    `seen` — never touching `endorsed`, which only `--pin` moves. Returns the
    codes that drifted; the committed diff is what lets `luria lint` warn
    offline (#135)."""
    cfg = current()
    pinned = _copy(state())
    url_pinned = {u: dict(e) for u, e in url_state().items()}
    if not pinned and not url_pinned:
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
            _observe(f"{prefix}{remote.delim}{code}", url, entry, drifted)
    for url, entry in sorted(url_pinned.items()):
        _observe(url, url, entry, drifted)
    remotes.write_lock(pinned=pinned, urls=url_pinned)
    return drifted


def _observe(label: str, url: str, entry: dict, drifted: list[str]) -> None:
    """One fetch into one pin's `seen` hash."""
    body, why = remotes._fetch_bytes(url)
    if why:
        # An unreachable document is not a changed one — keep the last
        # observation rather than inventing a new claim.
        print(f"{label}: seen hash kept — {why}")
        return
    entry["seen"] = content_hash(body)
    if entry["seen"] != entry.get("endorsed"):
        drifted.append(label)


def migrate_endorsements(moves: list[tuple[str, str, str]],
                         claimed: list[str]) -> tuple[int, list[str]]:
    """Carry pinned endorsements through a migration (ADR-040, #135).

    A rename moves a document's ADDRESS and leaves its content standing, and
    the endorsement is of the content — so for each claimed mirrored remote,
    a pin is re-keyed from the old tail to the new one with both hashes
    intact, rather than dropped and re-fetched. The distinction is not
    cosmetic: prune-and-re-endorse would silently vouch for whatever is
    upstream at that moment, laundering any drift a human had not reviewed.

    The claimed remote's discovered filename map is dropped instead of
    re-keyed: its keys AND its values spell the old world, an authoritative
    map with the wrong keys turns every new-spelled reference into "absent
    from the remote", and discovery (`luria remotes --refresh`) is the only
    authority that can rebuild it — absence honestly means "code-only
    convention until then". When upstream's own rename lands, the pinned
    documents' bytes will have changed too (their citations were swept), and
    that surfaces as ordinary drift for review — exactly the crossing of a
    human's desk the two-hash design exists to force.

    Returns (pins re-keyed, remote prefixes whose filename maps dropped)."""
    pinned = _copy(state())
    rekeyed = 0
    for prefix, old_tail, new_tail in moves:
        entries = pinned.get(prefix, {})
        if old_tail in entries:
            entries[new_tail] = entries.pop(old_tail)
            rekeyed += 1
    found = remotes.lock()
    dropped = sorted(p for p in set(claimed) if p in found)
    if dropped:
        found = {p: m for p, m in found.items() if p not in dropped}
    if rekeyed or dropped:
        remotes.write_lock(found=found, pinned=pinned)
    return rekeyed, dropped


def drift_lines() -> list[str]:
    """Every pin out of step with the record — from the committed lockfile
    alone, so the lint that reads this stays a check that passes on a train.
    The network work happened earlier: `--pin` recorded the endorsement,
    `--refresh` recorded what upstream serves, and this compares."""
    cfg = current()
    pinned = state()
    url_pinned = url_state()
    flagged, _ = flagged_urls()
    declaring = any(r.pin or any(s.pin for s in r.schemes.values())
                    for r in cfg.remotes.values())
    if not pinned and not url_pinned and not flagged and not declaring:
        return []
    refs = remotes.cited()
    lines: list[str] = []
    # Cited references the config declares pinned but the lockfile has not
    # endorsed — the scheme-level counterpart of a flagged, unendorsed URL.
    for prefix in sorted(refs):
        remote = cfg.remotes.get(prefix)
        if remote is None:
            continue
        for code in sorted(refs[prefix]):
            if not remote.auto_pin(code) or code in pinned.get(prefix, {}):
                continue
            composed = f"{prefix}{remote.delim}{code}"
            if stable_url(remote, code):
                lines.append(
                    f"{composed}: cited in a source configured to pin "
                    "(`pin = true`), but never endorsed — "
                    "`luria remotes --pin` fetches and endorses it")
            else:
                lines.append(
                    f"{composed}: configured to pin, but nothing knows "
                    "where its stable bytes live — a `pin_url` template "
                    "on the remote declares it")
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
    for url, entry in sorted(url_pinned.items()):
        if url not in flagged:
            lines.append(f"{url}: pinned, but no `pin:` directive flags it "
                         "any more — `luria remotes --pin` prunes it")
        elif entry.get("seen") != entry.get("endorsed"):
            lines.append(
                f"{url}: content changed since it was endorsed — review it, "
                f"then `luria remotes --pin {url}` to endorse it again")
    # A flag that registered a pin nobody fetched: armed-looking, doing
    # nothing — the exact quiet failure the directives report exists for.
    for url in sorted(flagged - set(url_pinned)):
        lines.append(f"{url}: flagged by `pin:` but never endorsed — "
                     "`luria remotes --pin` fetches and endorses it")
    return lines
