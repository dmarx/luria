#!/usr/bin/env python3
"""Does a document's identifier name the document's subject? (#166)

`unresolved-codes` asks whether a reference points *somewhere*. Nothing asked
whether it points *where it says*, and the gap is not theoretical: 53 of 139
`arxiv:` identifiers in one record resolved to real papers on unrelated
subjects — quantum secret sharing filed as the PaLM 2 technical report,
electron losses in hypersonic flows filed as checkpointing advice. Every one
was syntactically valid, in the right year range, and green for two years.
That is what a plausible wrong identifier looks like, and it is why review
does not catch them: `2111.09432` reads as a late-2021 systems paper unless
you fetch it.

The check is a title comparison, and the reason it can exist at all is that
the remote already knows how to reach the thing.

Offline, like everything else
-----------------------------
`luria lint` does not open sockets (ADR-016), so this follows `pins`: an
explicit command reaches the network and writes what it found into
`remotes.lock.json`; the lint reads the committed file and compares. CI, a
train and a laptop then answer the question identically, and the answer is
reviewable in a diff.

Where a title comes from
------------------------
`uris.title` names a URL that serves metadata for one identifier, and
`title_re` reads the title out of it — first capture group, `re.DOTALL`. Both
are declared per remote rather than guessed per host, for the reason `pin_url`
is: only the project can vouch that a URL serves what it looks like, and a
guess that silently stops matching when a provider changes its response is
worse than no check. The two recipes anyone needs:

    [luria.remotes.ARXIV]
    uris.title = "https://export.arxiv.org/api/query?id_list={1}.{2}"
    title_re   = "<entry>.*?<title>(.*?)</title>"

    [luria.remotes.DOI]
    uris.title = "https://api.crossref.org/works/{uid}"
    title_re   = '"title":\\s*\\[\\s*"(.*?)"'

Which fields hold identifiers
-----------------------------
A frontmatter key equal to a remote's prefix, lowercased: `arxiv:` belongs to
`[luria.remotes.ARXIV]`. No new configuration — a project that has declared
the remote has already said what the identifier is.

Why the comparison is dumb on purpose
-------------------------------------
Normalized equality, then a `source-ok:` directive. A similarity threshold
turns a mechanical check into a judgement call, and a check joins the lint
only when the violation is always wrong and mechanically fixable. The
legitimate divergences are real and common — a nickname the project prefers
(`AdamW: Decoupled Weight Decay Regularization`), a v1 title that changed
between versions, a subtitle deliberately trimmed — and they are what the
directive is for. In the record that motivated this, 22 of the 53 were that
class, which is more than enough noise to get a check switched off.
"""

from __future__ import annotations

import html
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .config import current

SOURCE_OK = "source-ok"

# A title survives rewrapping, case and punctuation; it does not survive being
# a different paper. Comparing on words alone is what lets a recorded title
# keep its own capitalisation and line breaks.
def normalize(title: str) -> str:
    return " ".join(re.sub(r"[^0-9a-z]+", " ", title.lower()).split())


@dataclass(frozen=True)
class Identifier:
    path: Path
    code: str
    remote: str          # the remote's prefix, e.g. "ARXIV"
    uid: str             # the identifier itself, e.g. "2502.11089"
    recorded: str        # the document's own `title:`
    line: int            # where the identifier field sits, for the report

    @property
    def key(self) -> str:
        return f"{self.remote}/{self.uid}"


def _field_line(text: str, field: str) -> int:
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith(f"{field}:"):
            return n
    return 1


def identifiers() -> list[Identifier]:
    """Every document field that holds a remote identifier, with the title the
    document claims for it."""
    from . import adr_index
    cfg = current()
    by_field = {prefix.lower(): prefix for prefix in cfg.remotes}
    found: list[Identifier] = []
    for scheme in cfg.schemes.values():
        for code, path in [*scheme.documents().items(),
                           *scheme.temp_documents().items()]:
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            meta, _ = adr_index.parse_frontmatter(text)
            title = str(meta.get("title") or "").strip()
            if not title:
                continue
            for field, prefix in by_field.items():
                value = meta.get(field)
                if not value or not isinstance(value, str):
                    continue
                found.append(Identifier(path, code, prefix, value.strip(),
                                        title, _field_line(text, field)))
    return found


# ── The network half: an explicit command, never the lint ────────────────


def _title_url(remote, uid: str) -> str:
    """The metadata URL for one identifier, or "" when the remote has not
    declared one. `uris.title` renders over the same vocabulary as `read`,
    with the uid's capture groups by position."""
    template = remote.uris.get("title", "")
    if not template:
        return ""
    values = {"uid": uid, "0": uid}
    if remote.uid:
        if m := re.fullmatch(remote.uid, uid):
            for i, group in enumerate(m.groups(), 1):
                values[str(i)] = group or ""
    return re.sub(r"\{([0-9a-z_]+)\}",
                  lambda m: values.get(m.group(1), m.group(0)), template)


# Metadata APIs are a courtesy, and the ones worth asking say so: arXiv's
# terms ask for a pause between requests. The pause is only half the job —
# the other half is telling a throttle apart from an answer, which HTTP
# already does and the first version of this did not.
COURTESY = 3.0
ATTEMPTS = 3

# What came back, as a fact rather than as an absence. The distinction this
# type exists for: "upstream has no such identifier" and "upstream would not
# talk to me" are opposite findings, and collapsing them into `None` makes a
# rate limit indistinguishable from the wrong-paper answer the check hunts.
#   ok         — a title
#   absent     — upstream says this identifier names nothing (404/410)
#   throttled  — rate-limited or unavailable (429/503), after the retries
#   unreachable— DNS, TLS, timeout, refused
#   unparsed   — a 200 whose body the `title_re` did not match
@dataclass(frozen=True)
class Fetched:
    status: str
    title: str = ""
    detail: str = ""

    @property
    def known(self) -> bool:
        return self.status in ("ok", "absent")


def _retry_after(error) -> float | None:
    """Seconds a 429/503 asked us to wait, when it said."""
    value = (getattr(error, "headers", None) or {}).get("Retry-After")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _once(url: str, pattern: str) -> Fetched:
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            body = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        if error.code in (404, 410):
            return Fetched("absent", detail=f"HTTP {error.code}")
        if error.code in (429, 503):
            wait = _retry_after(error)
            return Fetched("throttled",
                           detail=f"HTTP {error.code}"
                                  + (f", retry after {wait:g}s" if wait else ""))
        return Fetched("unreachable", detail=f"HTTP {error.code}")
    except (urllib.error.URLError, OSError, ValueError) as error:
        return Fetched("unreachable", detail=str(error)[:80])
    if m := re.search(pattern, body, re.S):
        # Metadata APIs serve XML and JSON, so a title arrives escaped: arXiv's
        # Atom feed returns "Better &amp; Faster". Comparing that against a
        # title a person typed reports a mismatch on the escaping, which is a
        # false positive — and a check that cries wolf is a check nobody reads.
        return Fetched("ok", title=" ".join(html.unescape(m.group(1)).split()))
    return Fetched("unparsed", detail="200, but `title_re` matched nothing")


def _fetch(url: str, pattern: str) -> Fetched:
    """Ask, backing off only for the answers that mean "ask again later".

    A 404 is an answer and is not retried; a 429 is not an answer and is. The
    first version retried everything blindly and reported every failure the
    same way, which is how a throttled batch of fifteen wrote nothing to the
    lockfile and read afterwards as fifteen documents in agreement.
    """
    delay = COURTESY
    for attempt in range(ATTEMPTS):
        got = _once(url, pattern)
        if got.known or got.status == "unparsed":
            return got
        if attempt < ATTEMPTS - 1:
            time.sleep(delay)
            delay *= 2
    return got


def ask(ident: "Identifier") -> Fetched | None:
    """Ask upstream what one identifier is, or None when the remote has not
    declared how to ask. The single place a socket is opened."""
    remote = current().remotes.get(ident.remote)
    if remote is None or not remote.title_re:
        return None
    url = _title_url(remote, ident.uid)
    if not url:
        return None
    return _fetch(url, remote.title_re)


def resolve(only: tuple[str, ...] = ()) -> list[str]:
    """Fetch every identifier's title and record it in the lockfile.

    Returns one line per identifier that could not be settled. A `throttled`
    or `unreachable` answer is NOT written: an entry that says nothing is
    read later as agreement, so the absence has to stay an absence and be
    reported here instead.
    """
    from . import remotes
    state_now = dict(remotes._read_lockfile().get("titles", {}))
    problems: list[str] = []
    seen: set[str] = set()
    for ident in identifiers():
        if only and ident.remote not in only and ident.key not in only:
            continue
        if ident.key in seen:
            continue
        seen.add(ident.key)
        got = ask(ident)
        if got is None:
            continue                      # remote has not declared how to ask
        if got.status == "ok":
            state_now[ident.key] = {"title": got.title}
        elif got.status == "absent":
            state_now[ident.key] = {"status": "absent", "detail": got.detail}
        else:
            problems.append(f"{ident.key}: {got.status} — {got.detail}")
        if got.status != "absent":
            time.sleep(COURTESY)
    remotes.write_lock(titles=state_now)
    return problems


def state() -> dict[str, dict[str, str]]:
    """What the committed lockfile says each identifier resolves to."""
    from . import remotes
    return remotes._read_lockfile().get("titles", {})


# ── The offline half: what the lint reads ────────────────────────────────


def mismatch_lines() -> tuple[list[str], list[str], list[str]]:
    """Identifiers that disagree with upstream, identifiers nothing has
    checked, and `source-ok:` directives that no longer acknowledge anything.

    The lockfile is a **cache with an endorsement in it**, not the boundary of
    what may be known. An identifier it has no answer for is the interesting
    case, not the exempt one: a citation is never more likely to be wrong than
    in the minutes after it is typed, and the first version of this check
    passed exactly then, because nothing had resolved it yet.

    So under `[luria.lint] network = "auto"` the lint asks about what it does
    not already know — normally the one citation a contribution added — and
    falls back to reporting it unchecked when it cannot. "never" answers only
    from the lockfile, for a hermetic build. "require" makes not being able to
    ask a finding, so a green CI run means the references were verified rather
    than remembered.
    """
    from . import directives, remotes
    cfg = current()
    known = dict(state())
    policy = cfg.network
    flagged: list[str] = []
    unchecked: list[str] = []
    stale: list[str] = []
    learned: dict[str, dict[str, str]] = {}

    by_path: dict = {}
    for ident in identifiers():
        by_path.setdefault(ident.path, []).append(ident)

    for path, idents in sorted(by_path.items(), key=lambda kv: str(kv[0])):
        text = path.read_text(encoding="utf-8")
        found = directives.find(path, text, {SOURCE_OK})
        used: set[tuple[int, str]] = set()
        for ident in idents:
            entry = known.get(ident.key)
            if entry is None and policy != "never":
                got = ask(ident)
                if got is None:
                    continue              # remote declares no way to ask
                if got.status == "ok":
                    entry = {"title": got.title}
                elif got.status == "absent":
                    entry = {"status": "absent", "detail": got.detail}
                else:
                    entry = None
                    reason = f"{got.status} — {got.detail}"
                if entry is not None:
                    known[ident.key] = entry
                    learned[ident.key] = entry
            ack = next((d for d in found
                        if d.covers(ident.line)
                        and (ident.uid in d.args or ident.key in d.args)), None)

            if entry is None:
                if policy == "never":
                    continue              # answering only from the lockfile
                if ack is not None:
                    used.add((ack.line, ident.uid))
                    continue
                site = (f"{cfg.rel(path)}:{ident.line}: `{ident.remote.lower()}: "
                        f"{ident.uid}`")
                unchecked.append(f"{site} could not be checked — {reason}")
                continue

            if entry.get("status") == "absent":
                problem = (f"names nothing upstream ({entry.get('detail', '')})")
            elif normalize(entry.get("title", "")) == normalize(ident.recorded):
                continue
            else:
                problem = (f"resolves to \u201c{entry['title']}\u201d, not "
                           f"\u201c{ident.recorded}\u201d")
            if ack is not None:
                used.add((ack.line, ident.uid))
                continue
            flagged.append(f"{cfg.rel(path)}:{ident.line}: "
                           f"`{ident.remote.lower()}: {ident.uid}` {problem}")

        for d in found:
            problem = directives.problems(d)
            for arg in d.args:
                if (d.line, arg) not in used:
                    problem = problem or (f"`{SOURCE_OK}: {arg}` matches no "
                                          "identifier that disagrees")
                    stale.append(f"{cfg.rel(path)}:{d.line}: {problem}")
                    break

    # What the lint learned is worth keeping: the next run answers from the
    # lockfile, and the diff shows a reviewer what upstream said and when.
    if learned:
        remotes.write_lock(titles=known)
    return flagged, unchecked, stale
