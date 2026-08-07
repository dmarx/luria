#!/usr/bin/env python3
"""Two numbers about the record, rendered as badges in the README.

This is a library: `luria index` rewrites the region with everything else and
`luria lint` checks it. The `luria badges` command was retired (ADR-030) —
its normal use had become printing a warning that `luria index` is what you
meant (ADR-029). The module still runs standalone:

    python -m luria.badges            # print the markdown
    python -m luria.badges --write    # rewrite the region in README.md
    python -m luria.badges --check    # exit 1 if that region is stale

Both counts are questions a reader of the repository front page should be able
to answer without cloning it:

  **needs decision**  — documents that are `Proposed` or `Deferred`, across
                        every configured scheme. An open question stated is
                        fine; an open question nobody can see is how a decision
                        gets made in code and never written down.
  **cited but retired** — documents no longer in force that current docs or
                        code still cite *without an acknowledgement*. Citing a
                        `Rejected` decision is often right, which is why this
                        counts only the unconsidered ones (ADR-007).

Derived, not hand-written (ADR-018). The numbers are computed from frontmatter
and baked into static shields.io URLs, which `luria index` rewrites and
`luria lint` checks — so a badge cannot quietly disagree with the record it
describes, and reading it costs a reader no network round-trip to a service
that would need this repository's data anyway.

Only local schemes are counted. A remote's *status* is not knowable from a URL,
and fetching every foreign document to find out would make a documentation
badge depend on someone else's uptime — the same argument that keeps
`luria remotes --check` out of the lint.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import adr_pending, ci, ref_status
from .config import current

OPEN = "<!-- luria:badges -->"
CLOSE = "<!-- /luria:badges -->"
REGION_RE = re.compile(rf"{re.escape(OPEN)}.*?{re.escape(CLOSE)}", re.DOTALL)

# Neither number is a failure, so neither goes red. Green when nothing is
# outstanding, amber when something is — "look at this", not "you broke it".
GOOD, ATTENTION = "brightgreen", "orange"


def counts() -> tuple[int, int]:
    """(needs decision, cited but retired). Both across every local scheme."""
    docs = ref_status.load_docs()
    scan = ref_status.scan(docs=docs)
    return len(adr_pending.pending()), len(ref_status.flagged(scan, docs))


def badge(label: str, value: int, target: str) -> str:
    colour = GOOD if value == 0 else ATTENTION
    text = f"{label.replace(' ', '%20')}-{value}-{colour}"
    return f"[![{label}: {value}](https://img.shields.io/badge/{text})]({target})"


def index_link() -> str:
    """Where a badge points, read from config rather than restated.

    A default that spells out a configured path is a projection, and
    projections drift ([DP-3](../docs/design-principles.md#dp-3)) — this one
    did, the moment the index moved."""
    return current().rel(current().index)


def region(link: str | None = None) -> str:
    link = link or index_link()
    undecided, retired = counts()
    return "\n".join([
        OPEN,
        badge("needs decision", undecided, link),
        badge("cited but retired", retired, link),
        CLOSE,
    ])


def rewrite(text: str, link: str | None = None) -> str:
    """The README with its badge region refreshed.

    Returns the text unchanged when there is no region — a project that hasn\'t
    opted in isn\'t nagged, and `--write` says so rather than silently doing
    nothing (DP-1)."""
    return REGION_RE.sub(lambda _: region(link), text, count=1)


def readme() -> Path:
    return current().root / "README.md"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="rewrite README.md")
    ap.add_argument("--check", action="store_true", help="exit 1 if stale")
    args = ap.parse_args()

    path = readme()
    if not args.write and not args.check:
        print(region())
        # Printing is the whole job here, but as a CI `- run:` step it is
        # indistinguishable from a write that landed — which is how an
        # adopter came to have a badges step in a workflow doing nothing
        # (ADR-029). Said on stderr so a `> file` redirect stays clean.
        print("luria badges: printed only — `--write` rewrites the region in "
              f"{current().rel(readme())}, `--check` fails when it is stale. "
              "In normal use `luria index` writes it with everything else.",
              file=sys.stderr)
        return 0

    if not path.exists() or OPEN not in path.read_text():
        print(f"luria badges: no {OPEN} region in "
              f"{current().rel(path)} — add one where the badges belong:\n\n"
              f"  {OPEN}\n  {CLOSE}\n", file=sys.stderr)
        return 0

    text = path.read_text()
    fresh = rewrite(text)
    if args.check:
        if fresh != text:
            print(f"{current().rel(path)}: badge counts are stale — "
                  f"{ci.regenerate_remedy()}", file=sys.stderr)
            return 1
        print("luria badges: current")
        return 0
    path.write_text(fresh)
    undecided, retired = counts()
    print(f"badges: needs decision {undecided}, cited but retired {retired}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
