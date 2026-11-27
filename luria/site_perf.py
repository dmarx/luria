# luria/site_perf.py
"""Where a site build spends its time and its bytes, on request.

    npx quartz build -v … 2>&1 | python -m luria.site_perf stamp > quartz.log
    python -m luria.site_perf report --log quartz.log --public public \\
        --staged content --steps steps.tsv --out perf

`actions/site` runs these when its `timings` input is on — luria's own Pages
workflow turns it on once a week — and uploads `perf/` as the `site-perf`
artifact, with `site-perf.md` also written to the job summary. The record
grows continuously, so a build that was fast in the spring says nothing
about the build now. A weekly sample gives every later decision about the
publisher a series to read rather than one anecdote.

Three readings, one per thing the run leaves behind:

**The Quartz log.** Quartz always prints its phase totals ("Parsed 419
Markdown files in 9s"), but rounded by `pretty-time` to one unit, so a
minute-long phase reads "1m". `stamp` prefixes every line with the seconds
since the pipe opened, which makes the verbose `[emit:<Emitter>] <file>`
lines a per-emitter timeline. Emitters after the first two run concurrently
under one `Promise.all`, so an emitter's span is *when its files appeared*,
not CPU it alone spent; the emitter whose last file appears last is the one
holding the build.

**The built output.** Bytes and files by kind, with per-page social cards
(`*-og-image.webp`) counted apart from images the record ships, plus the
size of `contentIndex.json` — the search and graph index every page fetches —
and the heaviest files. Deploy size and page weight are requirements in
their own right, not side effects of build time.

**The step durations** the action measured around each of its own steps, as
`<label>\t<seconds>` lines, so setup (pip, npm) is not mistaken for build.

`luria: timing:` lines from `LURIA_TIMINGS=1` (luria/timing.py) land in the
same job log; they are not re-parsed here because they are already one line
per phase.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TextIO

from . import writes

ANSI = re.compile(r"\x1b\[[0-9;]*m")
STAMP = re.compile(r"^\[\+(?P<t>\d+(?:\.\d+)?)\] (?P<line>.*)$")
UNITS = {"ns": 1e-9, "μs": 1e-6, "us": 1e-6, "ms": 1e-3, "s": 1.0,
         "m": 60.0, "h": 3600.0}
DURATION_PART = re.compile(r"(\d+(?:\.\d+)?)(ns|μs|us|ms|s|m|h)")

PHASES = {
    "found": re.compile(r"Found (\d+) input files from .* in (.+)$"),
    "parsed": re.compile(r"Parsed (\d+) Markdown files in (.+)$"),
    "emitted": re.compile(r"Emitted (\d+) files to .* in (.+)$"),
    "done": re.compile(r"Done processing (\d+) files in (.+)$"),
}
EMIT = re.compile(r"^\[emit:(?P<name>[^\]]+)\] ")
MARKDOWN = re.compile(r"^\[markdown\] (?P<file>\S+) -> \S+ \((?P<took>[^)]+)\)$")


def stamp(source: TextIO = sys.stdin, sink: TextIO = sys.stdout,
          clock: Callable[[], float] = time.monotonic) -> None:
    """Copy `source` to `sink`, each line prefixed `[+seconds] `."""
    start = clock()
    for raw in source:
        line = ANSI.sub("", raw.rstrip("\n"))
        sink.write(f"[+{clock() - start:.3f}] {line}\n")
        sink.flush()


def duration(text: str) -> float | None:
    """Seconds from a `pretty-time` string: `744μs`, `9s`, `1m 3s`."""
    parts = DURATION_PART.findall(ANSI.sub("", text).strip())
    if not parts:
        return None
    return round(sum(float(n) * UNITS[u] for n, u in parts), 9)


def parse_log(lines: Iterable[str], slowest: int = 10) -> dict:
    """Phase totals, per-emitter spans and the slowest markdown files."""
    phases: dict[str, dict] = {}
    emitters: dict[str, dict] = {}
    markdown: list[dict] = []
    for raw in lines:
        text = ANSI.sub("", raw.rstrip("\n"))
        at = None
        if m := STAMP.match(text):
            at, text = float(m["t"]), m["line"]
        for phase, pattern in PHASES.items():
            if m := pattern.search(text):
                phases[phase] = {"count": int(m[1]), "seconds": duration(m[2])}
        if (m := EMIT.match(text)) and at is not None:
            span = emitters.setdefault(m["name"], {"files": 0, "first": at, "last": at})
            span["files"] += 1
            span["first"], span["last"] = min(span["first"], at), max(span["last"], at)
        if (m := MARKDOWN.match(text)) and (took := duration(m["took"])) is not None:
            markdown.append({"file": m["file"], "seconds": took})
    ordered = dict(sorted(emitters.items(), key=lambda kv: -kv[1]["last"]))
    markdown.sort(key=lambda r: -r["seconds"])
    return {"phases": phases, "emitters": ordered, "slowest_markdown": markdown[:slowest]}


def _kind(path: Path) -> str:
    if path.name.endswith("-og-image.webp"):
        return "og-image"
    return path.suffix.lstrip(".").lower() or "(none)"


def inventory(root: Path, top: int = 10) -> dict:
    """Files and bytes under `root`, by kind, with the heaviest named."""
    root = Path(root)
    files = [p for p in root.rglob("*") if p.is_file()] if root.is_dir() else []
    by_kind: dict[str, dict] = {}
    sized = []
    for p in files:
        size = p.stat().st_size
        bucket = by_kind.setdefault(_kind(p), {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += size
        sized.append((size, p.relative_to(root).as_posix()))
    sized.sort(key=lambda s: (-s[0], s[1]))
    index = root / "static" / "contentIndex.json"
    return {
        "files": len(files),
        "bytes": sum(s for s, _ in sized),
        "by_kind": dict(sorted(by_kind.items(), key=lambda kv: -kv[1]["bytes"])),
        "content_index_bytes": index.stat().st_size if index.is_file() else None,
        "largest": [{"path": p, "bytes": s} for s, p in sized[:top]],
    }


def _steps(path: Path) -> dict[str, float]:
    if not path.is_file():
        return {}
    rows = (line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if "\t" in line)
    return {label: float(seconds) for label, seconds in rows}


def _mb(n: int | None) -> str:
    return "—" if n is None else f"{n / 1e6:.2f}"


def markdown(data: dict) -> str:
    """The job-summary table: the numbers to glance at, not the whole JSON."""
    out = ["## Site build performance", "", "| step | seconds |", "|---|---|"]
    out += [f"| {k} | {v:.1f} |" for k, v in data["steps"].items()]
    phases = data["quartz"]["phases"]
    if phases:
        out += ["", "| Quartz phase | files | seconds (Quartz-rounded) |", "|---|---|---|"]
        out += [f"| {k} | {v['count']} | {v['seconds']} |" for k, v in phases.items()]
    if emitters := data["quartz"]["emitters"]:
        out += ["", "Emitters by when their last file appeared (concurrent, so "
                "spans overlap):", "", "| emitter | files | first s | last s |",
                "|---|---|---|---|"]
        out += [f"| {k} | {v['files']} | {v['first']:.1f} | {v['last']:.1f} |"
                for k, v in emitters.items()]
    for label in ("staged", "output"):
        inv = data[label]
        out += ["", f"**{label}**: {inv['files']} files, {_mb(inv['bytes'])} MB"
                + (f"; contentIndex.json {_mb(inv['content_index_bytes'])} MB"
                   if inv["content_index_bytes"] else ""), "",
                "| kind | files | MB |", "|---|---|---|"]
        out += [f"| {k} | {v['files']} | {_mb(v['bytes'])} |"
                for k, v in list(inv["by_kind"].items())[:8]]
    return "\n".join(out) + "\n"


def report(log: str, public: str, staged: str, steps: str, out: str) -> str:
    """Write `site-perf.json` and `site-perf.md` into `out`; return `out`."""
    log_path = Path(log)
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines() if log_path.is_file() else []
    data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": _steps(Path(steps)),
        "quartz": parse_log(lines),
        "staged": inventory(Path(staged)),
        "output": inventory(Path(public)),
    }
    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    writes.write_text(dest / "site-perf.json", json.dumps(data, indent=2) + "\n")
    writes.write_text(dest / "site-perf.md", markdown(data))
    return str(dest)


if __name__ == "__main__":
    import fire

    fire.Fire({"stamp": stamp, "report": report})
