#!/usr/bin/env python3
"""Foreign references: `LU-ADR-013` is that remote's decision number 13.

    luria remotes              # what is configured, and how each resolves
    luria remotes --refresh    # discover code→filename maps, write the lockfile
    luria remotes --check      # HEAD every construction; report what 404s

A project that cites another project's record constantly cannot use an
unprefixed code, because it would mean both "our thirteenth decision" and
"theirs". The prefix makes the namespace explicit at the point of use, and one
config entry teaches Luria how to turn it into a URL (ADR-016):

    [luria.remotes.LU]
    repo = "dmarx/luria"

From there `LU-ADR-013` is a first-class reference — `luria link --fix` writes
the link, and `luria lint` demands it, exactly as it does for a local code.

Constructing the URL
--------------------
Three rungs, strongest first. An explicit `url` template wins. Otherwise a
**discovered filename** from the lockfile, which is the only thing that can
resolve a remote whose files carry title slugs (`adr-013-a-long-title.md`).
Otherwise the code-only convention (ADR-013), which needs no lockfile at all
and is the default because it is Luria's own.

**Discovery reads a public repository over HTTPS**, and reads that repository's
own `luria.toml` when it has one, so `dir` comes from the authority rather than
from a guess. A remote Luria cannot read is told so and left on rung three or
one — the fix is a `url` template, not a workaround.

Why a lockfile
--------------
CI, an offline checkout and a laptop with a network connection have to resolve
the same reference the same way, and a check that reaches the network is a
check that fails on a train. Discovery is an explicit command whose output is
committed; nothing else in Luria opens a socket.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .config import Remote, current

# `LU-ADR-013`: a remote prefix, a delimiter, then a tail in that remote's own
# namespace. Built from config, because an unconfigured prefix must NOT match —
# otherwise a hyphenated word before a code would be read as a namespace. The
# tail defaults to the Luria scheme shape; a `uid` remote supplies its own
# pattern, so a reference need not be a number at all (ADR-024).
DEFAULT_TAIL = r"[A-Z]{2,10}-\d{1,4}"


def tail_re(remote: Remote) -> str:
    return remote.uid or DEFAULT_TAIL


def remote_pattern(remote: Remote) -> re.Pattern:
    # The default tail ends at a word boundary; a uid regex bounds itself —
    # imposing \b on it would truncate uids ending in punctuation.
    end = "" if remote.uid else r"\b"
    return re.compile(rf"\b{re.escape(remote.prefix)}{re.escape(remote.delim)}"
                      rf"(?P<code>{tail_re(remote)}){end}")


@dataclass(frozen=True)
class RemoteRef:
    """One foreign reference found in text, already canonical."""
    remote: Remote
    tail: str
    start: int
    end: int
    text: str

    @property
    def prefix(self) -> str:
        return self.remote.prefix

    @property
    def composed(self) -> str:
        return f"{self.prefix}{self.remote.delim}{self.tail}"


def references(text: str) -> list[RemoteRef]:
    """Every configured remote's references in `text`, in source order.

    Scanned per remote rather than by one combined regex, because each remote
    brings its own delimiter and tail shape. Longer prefixes scan first and
    claim their spans, so `SGX-…` is never read as `SG` plus a strange tail."""
    found: list[RemoteRef] = []
    for remote in sorted(current().remotes.values(),
                         key=lambda r: len(r.prefix), reverse=True):
        for m in remote_pattern(remote).finditer(text):
            if any(r.start < m.end() and m.start() < r.end for r in found):
                continue
            found.append(RemoteRef(remote, remote.canon(m.group("code")),
                                   m.start(), m.end(), m.group(0)))
    return sorted(found, key=lambda r: r.start)


# unresolved-ok-block: DP-018 — the parsed-tail spelling in the example below
def parse_code(text: str) -> tuple[Remote, str] | None:
    """`SG-DP-18` → (the SG remote, "DP-018"); None when no remote matches the
    whole string. The one reader of a composed code's anatomy — annotation
    arguments, link labels and report keys all come through here, so the
    delimiter is spelled in exactly one place (DP-4)."""
    for remote in sorted(current().remotes.values(),
                         key=lambda r: len(r.prefix), reverse=True):
        m = re.fullmatch(
            rf"{re.escape(remote.prefix)}{re.escape(remote.delim)}"
            rf"({tail_re(remote)})", text)
        if m:
            return remote, remote.canon(m.group(1))
    return None


def normalise(code: str) -> str:
    """A scheme code with and without leading zeros is one document — one lock
    key. Only scheme-shaped tails come here; a uid is exact already."""
    prefix, number = code.rsplit("-", 1)
    return f"{prefix.upper()}-{int(number):03d}"


# ── The lockfile ─────────────────────────────────────────────────────────


def lock() -> dict[str, dict[str, str]]:
    path = current().remotes_lock
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text()).get("remotes", {})
    except (OSError, ValueError):
        return {}


def write_lock(found: dict[str, dict[str, str]]) -> Path:
    path = current().remotes_lock
    path.write_text(json.dumps(
        {"_comment": "Generated by `luria remotes --refresh`. Committed so "
                     "CI and offline checkouts resolve foreign references the "
                     "same way (ADR-016).",
         "remotes": {k: dict(sorted(v.items())) for k, v in sorted(found.items())}},
        indent=2) + "\n")
    return path


def link(remote: Remote, code: str) -> str:
    """The URL for one foreign code, using the strongest rung available.

    **Discovery, once done, is authoritative.** If this remote has a lockfile
    entry and the code isn't in it, the answer is "" rather than a guessed
    filename — the map was read from the remote itself, so a code missing from
    it names no document there. Guessing anyway once produced a confident link
    to a file that has never existed (ADR-016).

    The lockfile's authority covers exactly what discovery can see: *files*.
    A scheme configured to construct a document anchor or a URL template
    (ADR-023) never consults it — its documents are sections, which no
    directory listing contains, so an absence there is not evidence."""
    code = remote.canon(code)
    if remote.uid:
        # One rung: the template. The lockfile maps filenames, and a uid
        # remote has none to map (ADR-024).
        return remote.link(code)
    scheme = remote.scheme_for(code)
    if scheme is not None and (scheme.url or scheme.document):
        return remote.link(code)
    if remote.url:
        return remote.link(code)
    known = lock().get(remote.prefix)
    if known is not None:
        return remote.link(code, known[code]) if code in known else ""
    return remote.link(code)


def resolve(remote_prefix: str, code: str) -> str:
    remote = current().remotes.get(remote_prefix.upper())
    return link(remote, code) if remote else ""


# ── Hand-written URLs ────────────────────────────────────────────────────

URL_OK = "url-ok"


def hand_links(files: list[Path] | None = None
               ) -> tuple[list[str], list[str]]:
    """Links whose label is a composed foreign code but whose target is not
    the URL Luria would construct — with the `url-ok:` annotations that
    acknowledge the deliberate ones.

    Construction has real limits: a remote's principles may be sections of one
    document, which no filename convention can address, so a hand-written URL
    is sometimes the only correct citation. It is also a hand-maintained
    projection ([DP-3](../docs/design-principles.md#dp-3)) frozen at writing
    time — if the remote later adopts a convention or the lockfile learns the
    real filename, nothing updates it. So each one is either acknowledged or
    reported (ADR-035): never an error, never silent.

    Returns (flagged, stale): unacknowledged hand links, and `url-ok`
    directives that no longer acknowledge anything."""
    from . import directives, doc_refs, ref_status
    if not current().remotes:
        return [], []
    link_re = re.compile(r"\[([^\]\s]+)\]\(([^)\s]+)\)")
    cfg = current()
    flagged: list[str] = []
    stale: list[str] = []
    for path in files if files is not None else ref_status.scanned_files():
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        quoted = doc_refs.code_spans(text) if path.suffix == ".md" else []
        found = directives.find(path, text, {URL_OK})
        used: set[tuple[int, str]] = set()
        for m in link_re.finditer(text):
            if any(a <= m.start() < b for a, b in quoted):
                continue                      # a quotation, not a citation
            parsed = parse_code(m.group(1))
            if parsed is None:
                continue                      # a link, but not a foreign code
            remote, tail = parsed
            code = f"{remote.prefix}{remote.delim}{tail}"
            target = m.group(2)
            constructed = link(remote, tail)
            if target == constructed:
                continue
            line = text.count("\n", 0, m.start()) + 1
            ack = next(
                (d for d in found if d.covers(line)
                 and any(_same_code(a, code) for a in d.args)), None)
            if ack is not None:
                for a in ack.args:
                    if _same_code(a, code):
                        used.add((ack.line, a))
                continue
            flagged.append(
                f"{cfg.rel(path)}:{line}: {code} links to a hand-written URL "
                f"(construction would say: {constructed or 'nothing — not in the lockfile'})")
        for d in found:
            problem = directives.problems(d)
            for arg in d.args:
                if problem or (d.line, arg) not in used:
                    stale.append(
                        f"{cfg.rel(path)}:{d.line}: `url-ok` names {arg}, "
                        "which acknowledges no hand-written link here")
    return flagged, stale


def _same_code(arg: str, code: str) -> bool:
    a, b = parse_code(arg), parse_code(code)
    return (a is not None and b is not None
            and (a[0].prefix, a[1]) == (b[0].prefix, b[1]))


# ── Discovery ────────────────────────────────────────────────────────────

FILENAME_RE = re.compile(r"^([A-Za-z]{2,10})-0*(\d{1,4})(?:-[^/]*)?\.md$")


def _from_names(names: list[str]) -> dict[str, str]:
    """Filenames → {code: filename}. The same permissive rule
    `Scheme.number_of` uses, so a remote on either naming convention reads."""
    out: dict[str, str] = {}
    for name in sorted(names):
        m = FILENAME_RE.match(name)
        if m:
            out.setdefault(normalise(f"{m.group(1)}-{m.group(2)}"), name)
    return out


def _upstream_dir(text: str, fallback: str) -> str:
    """The remote's own `luria.toml` is the authority on where its documents
    live. Reading it rather than guessing is the whole point of a config file
    existing — and when there isn't one, the configured value stands."""
    try:
        import tomllib
        raw = tomllib.loads(text)
    except ValueError:
        return fallback
    luria = raw.get("luria", raw)
    schemes = luria.get("schemes") or {}
    for spec in schemes.values():
        if isinstance(spec, dict) and spec.get("dir"):
            return spec["dir"]
    return (luria.get("paths") or {}).get("decisions", fallback)


def _fetch(url: str) -> tuple[str, str]:
    """(body, why-not). Public HTTPS only — there is no credential path here,
    deliberately: a discovery that needs a secret is a discovery CI can't
    reproduce, and the answer for an unreadable remote is a `url` template."""
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return response.read().decode(), ""
    except urllib.error.HTTPError as exc:
        return "", ("not readable anonymously"
                    if exc.code in (401, 403, 404) else f"HTTP {exc.code}")
    except (urllib.error.URLError, OSError, UnicodeDecodeError) as exc:
        return "", f"unreachable ({exc.__class__.__name__})"


def discover(remote: Remote) -> tuple[dict[str, str], str]:
    """({code: filename}, how) for one remote. `how` names the source, or the
    reason there wasn't one — a discovery that silently finds nothing is
    indistinguishable from a remote with no documents (DP-1)."""
    if not remote.repo:
        return {}, "no `repo` configured"
    raw = f"https://raw.githubusercontent.com/{remote.repo}/{remote.ref}"
    config, _ = _fetch(f"{raw}/luria.toml")
    directory = _upstream_dir(config, remote.dir) if config else remote.dir
    body, why = _fetch(f"https://api.github.com/repos/{remote.repo}/contents/"
                       f"{directory}?ref={remote.ref}")
    if why:
        return {}, f"GitHub API: {why}"
    try:
        entries = json.loads(body)
    except ValueError:
        return {}, "GitHub API returned something that isn't JSON"
    how = f"GitHub API, {directory}/" + (" (from its luria.toml)" if config else "")
    return _from_names([e["name"] for e in entries
                        if e.get("type") == "file"]), how


# ── Reachability ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Probe:
    remote: str
    code: str
    url: str
    status: str          # "ok" | "404" | "unchecked: <why>"

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def cited() -> dict[str, set[str]]:
    """Every foreign code this project actually cites, by remote prefix."""
    from . import ref_status
    found: dict[str, set[str]] = {}
    if not current().remotes:
        return found
    for path in ref_status.scanned_files():
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for ref in references(text):
            found.setdefault(ref.prefix, set()).add(ref.tail)
    return found


def _head(url: str) -> tuple[bool, str]:
    """(reached, why-not). A HEAD, because the body is never wanted."""
    try:
        with urllib.request.urlopen(
                urllib.request.Request(url, method="HEAD"), timeout=15) as r:
            return (True, "") if r.status == 200 else (False, str(r.status))
    except urllib.error.HTTPError as exc:
        return False, str(exc.code)
    except (urllib.error.URLError, OSError) as exc:
        return False, exc.__class__.__name__


def readable(remote: Remote) -> tuple[bool, str]:
    """Whether this remote can be read at all, anonymously.

    Probed once per remote, and it is what keeps the check honest. A private
    repository answers 404 to every anonymous request, so probing documents
    without asking this first reports a shelf of perfectly good links as
    broken — a guard that cries wolf, which is a guard nobody reads
    (ADR-016)."""
    if remote.uid and remote.url:
        # The template is the whole story — no repository stands behind the
        # construction, so there is nothing to gate on; each URL is probed on
        # its own (ADR-024).
        return True, ""
    if not remote.repo:
        return False, "no `repo` configured"
    ok, why = _head(f"https://github.com/{remote.repo}")
    if ok:
        return True, ""
    return False, ("private or missing — every document will 404 anonymously"
                   if why in ("403", "404") else why)


def probe(remote: Remote, code: str, visible: bool = True) -> Probe:
    """One document. `visible` is `readable()`'s verdict for the remote, so a
    private repo yields "unverifiable" rather than a false "404"."""
    url = link(remote, code)
    if not url:
        # Not "unchecked": the lockfile was read from the remote itself, so its
        # silence about this code is a finding, not a gap.
        return Probe(remote.prefix, code, "", "absent from the remote")
    if not visible:
        return Probe(remote.prefix, code, url, "unverifiable: repo not public")
    ok, why = _head(url)
    return Probe(remote.prefix, code, url, "ok" if ok else
                 ("404" if why in ("403", "404") else f"unchecked: {why}"))


# ── CLI ──────────────────────────────────────────────────────────────────


def run(refresh: bool = False, check: bool = False) -> None:
    """How each configured remote's cited references resolve. --refresh
    discovers code→filename maps into the lockfile; --check HEADs every
    construction (needs network — a report, never a failure)."""
    cfg = current()
    if not cfg.remotes:
        # No silent refusal: say what would make this command do something.
        print("luria remotes: none configured. Add one to luria.toml:\n\n"
              "  [luria.remotes.LU]\n  repo = \"owner/name\"\n\n"
              "then cite it as `LU-ADR-013`.", file=sys.stderr)
        return

    if refresh:
        found: dict[str, dict[str, str]] = {}
        for remote in cfg.remotes.values():
            if remote.uid:
                # No directory of files to list — the uid template is the
                # whole construction, so there is nothing to discover, and
                # saying so beats a silent skip (DP-1).
                print(f"{remote.prefix} ({remote.label}): a uid remote — "
                      "nothing to discover")
                continue
            entries, how = discover(remote)
            found[remote.prefix] = entries
            print(f"{remote.prefix} ({remote.label}): {len(entries)} document(s) "
                  f"via {how}")
        path = write_lock(found)
        print(f"wrote {cfg.rel(path)}")

    references = cited()
    locked = lock()
    for remote in cfg.remotes.values():
        codes = sorted(references.get(remote.prefix, ()))
        known = locked.get(remote.prefix, {})
        rung = ("a url template over the uid" if remote.uid
                else "an explicit url template" if remote.url
                else f"{len(known)} discovered filename(s)" if known
                else "the code-only filename convention")
        print(f"\n{remote.prefix} → {remote.label}: {len(codes)} reference(s), "
              f"resolved by {rung}")
        for code in codes:
            target = link(remote, code)
            scheme = remote.scheme_for(code)
            # Not "assumed": the code-only convention (ADR-013) is exact for
            # any remote that follows it, and `--check` says whether it does.
            # A per-scheme construction says which shape it used (ADR-023).
            if remote.uid:
                note = ""
            elif scheme is not None and (scheme.url or scheme.document):
                note = ("  (by the scheme's url template)" if scheme.url
                        else "  (a document anchor, per the scheme)")
            elif code in known or remote.url:
                note = ""
            else:
                note = "  (by the code-only convention)"
            print(f"  {code}  {target or 'NO SUCH DOCUMENT'}{note if target else ''}")

    if check:
        broken, unverifiable, absent = [], [], []
        for remote in cfg.remotes.values():
            codes = sorted(references.get(remote.prefix, ()))
            if not codes:
                continue
            visible, why = readable(remote)
            print(f"\nchecking {remote.prefix} ({remote.label})"
                  + ("" if visible else f" — {why}"))
            # Probed wide (ADR-026): each URL is an independent HEAD, and the
            # wall-clock of a serial sweep is the sum of every round-trip.
            from .parallel import pmap
            for result in pmap(lambda c: probe(remote, c, visible), codes):
                if result.ok:
                    continue
                bucket = (unverifiable if result.status.startswith("unverifiable")
                          else absent if result.status == "absent from the remote"
                          else broken)
                bucket.append(result)
                print(f"  {result.remote}-{result.code}: {result.status}"
                      + (f" — {result.url}" if result.url else ""))
        print()
        if unverifiable:
            # Say which it is. "Unverified because we have a map we can't
            # confirm" and "unverified because nothing here knows" are
            # different claims, and a reader acts on them differently.
            backed = sum(1 for p in unverifiable
                         if p.code in lock().get(p.remote, {}))
            evidence = (f"{backed} of them rest on a discovered filename; the "
                        f"rest on the code-only convention alone"
                        if backed else
                        "their URLs rest on the code-only convention alone, "
                        "which is a prediction about the remote, not a fact "
                        "about it")
            print(f"remotes: {len(unverifiable)} could not be checked — the "
                  f"repository is not readable anonymously, so {evidence}")
        if absent:
            # Not a network result: the lockfile was read from the remote, so
            # its silence is a finding. `luria reports` lists these too, and
            # `unresolved-ok:` is where a deliberate one is acknowledged.
            print(f"remotes: {len(absent)} name no document in their remote "
                  "(see `luria reports`)")
        print(f"remotes: {len(broken)} reference(s) did not answer 200"
              if broken else "remotes: nothing verifiable is broken",
              file=sys.stderr if broken else sys.stdout)
    # A report, never a failure (ADR-035) — no exit code either way.


if __name__ == "__main__":
    import fire
    fire.Fire(run)
