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
# terms ask for a pause between requests, and a corpus resolve is a few
# hundred of them in a row. Backing off is also the only way to tell a rate
# limit from a wrong identifier — without it a throttled batch writes
# nothing and reads as "upstream has no title for this", which is the same
# shape as the answer the check exists to find.
COURTESY = 3.0
ATTEMPTS = 3


def _fetch(url: str, pattern: str) -> str | None:
    for attempt in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                body = response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError, ValueError):
            body = ""
        if body:
            if m := re.search(pattern, body, re.S):
                return " ".join(m.group(1).split())
        if attempt < ATTEMPTS - 1:
            time.sleep(COURTESY * (attempt + 1))
    return None


def resolve(only: tuple[str, ...] = ()) -> list[str]:
    """Fetch the title behind every identifier and record it in the lockfile.

    The one command here that opens a socket. Returns one line per identifier
    it could not resolve, so a network failure is reported rather than written
    into the lockfile as an absence that later reads as agreement.
    """
    from . import remotes
    cfg = current()
    state = dict(remotes._read_lockfile().get("titles", {}))
    problems: list[str] = []
    seen: set[str] = set()
    for ident in identifiers():
        if only and ident.remote not in only and ident.key not in only:
            continue
        if ident.key in seen:
            continue
        seen.add(ident.key)
        remote = cfg.remotes.get(ident.remote)
        url = _title_url(remote, ident.uid) if remote else ""
        if not url or not remote.title_re:
            continue                      # remote has not declared how to ask
        title = _fetch(url, remote.title_re)
        if title is None:
            problems.append(f"{ident.key}: no title from {url}")
            continue
        state[ident.key] = {"title": title}
        time.sleep(COURTESY)
    remotes.write_lock(titles=state)
    return problems


def state() -> dict[str, dict[str, str]]:
    """What the committed lockfile says each identifier resolves to."""
    from . import remotes
    return remotes._read_lockfile().get("titles", {})


# ── The offline half: what the lint reads ────────────────────────────────


def mismatch_lines() -> tuple[list[str], list[str]]:
    """Identifiers whose resolved title is not the one recorded, and the
    `source-ok:` directives that no longer acknowledge anything.

    Unresolved identifiers are not reported here. A lockfile that has never
    been populated would otherwise turn every document into a finding, which
    teaches people to run the command to silence it rather than to read it.
    """
    from . import directives
    cfg = current()
    known = state()
    flagged: list[str] = []
    stale: list[str] = []
    for path in {i.path for i in identifiers()}:
        text = path.read_text(encoding="utf-8")
        found = directives.find(path, text, {SOURCE_OK})
        used: set[tuple[int, str]] = set()
        for ident in [i for i in identifiers() if i.path == path]:
            entry = known.get(ident.key)
            if not entry or not entry.get("title"):
                continue
            upstream = entry["title"]
            if normalize(upstream) == normalize(ident.recorded):
                continue
            ack = next((d for d in found
                        if d.covers(ident.line)
                        and (ident.uid in d.args or ident.key in d.args)), None)
            if ack is not None:
                used.add((ack.line, ident.uid))
                continue
            flagged.append(
                f"{cfg.rel(path)}:{ident.line}: `{ident.remote.lower()}: "
                f"{ident.uid}` resolves to “{upstream}”, not "
                f"“{ident.recorded}”")
        for d in found:
            problem = directives.problems(d)
            for arg in d.args:
                if (d.line, arg) not in used:
                    problem = problem or (f"`{SOURCE_OK}: {arg}` matches no "
                                          "identifier that disagrees")
                    stale.append(f"{cfg.rel(path)}:{d.line}: {problem}")
                    break
    return flagged, stale
