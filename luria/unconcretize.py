#!/usr/bin/env python3
# luria/unconcretize.py
"""`luria unconcretize CODE...` — give a document's number back.

    luria unconcretize ADR-068            # ADR-068.md → a fresh ADR-tmp… file
    luria unconcretize ADR-005 ADR-006    # several at once

The inverse of `luria concretize`. Each named document is renamed to a
fresh temporary code (ADR-049), loses its `number:`, and every occurrence of
its code is rewritten to the temporary one, in the files `concretize`
rewrites (`concretize.rewritable_files`). The next `concretize`, where
merges serialize, numbers it again, in commit order.

It does not ask why. Two uses asked for it:

- **A collision.** A filing-allocated scheme takes the next free number on a
  branch. When the trunk takes the same number first, the two documents
  collide at merge: an add/add conflict on the file, and every citation the
  branch wrote now names the trunk's document (nucleation#387, ADR-068).
  Run this on the branch before merging the trunk, while every occurrence
  in the tree still means the branch's document.
- **Renumbering.** Giving back a run of numbers and concretizing assigns
  them in commit order.

No `formerly:` is recorded. The number is being given back, and an alias
would claim a code that another document holds, or soon will.

Codes are matched whole. `LIT-156` does not match inside `LIT-1563`, and
`ADR-068` does not match inside a composed remote code such as `LU-ADR-068`. Its lower-case spelling
is rewritten too, since an anchor spells a code that way (`#adr-068`).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from . import concretize
from . import new as new_mod
from .config import current
from . import writes


def _resolve(code: str):
    """(scheme, number, path) for a numbered document code, or a refusal
    that names the code (DP-1)."""
    cfg = current()
    for prefix, scheme in cfg.schemes.items():
        m = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", code.strip())
        if m:
            number = int(m.group(1))
            path = scheme.documents().get(number)
            if path is None:
                raise SystemExit(f"luria unconcretize: {code} names no "
                                 f"document in {cfg.rel(scheme.dir)}")
            return scheme, number, path
    raise SystemExit(f"luria unconcretize: {code} is not a numbered code of "
                     f"any scheme here ({', '.join(cfg.schemes)})")


def _whole(code: str) -> re.Pattern[str]:
    """`code` as a whole token: not preceded by a letter, digit, `_` or `-`
    (so not the tail of a composed remote code), not followed by a letter,
    digit or `_` (so not the head of a longer number)."""
    return re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(code)}(?![A-Za-z0-9_])")


def rewrite(renames: list[tuple[str, str]]) -> list[Path]:
    """Every whole occurrence of each old code, in either case, rewritten to
    its new code. Returns the files changed."""
    patterns = []
    for old, new in renames:
        patterns.append((_whole(old), new))
        if old.lower() != old:
            patterns.append((_whole(old.lower()), new.lower()))
    changed = []
    for path in concretize.rewritable_files():
        text = path.read_text(encoding="utf-8")
        out = text
        for pattern, new in patterns:
            out = pattern.sub(new, out)
        if out != text:
            writes.write_text(path, out)
            changed.append(path)
    return changed


def run(*codes: str) -> None:
    """Rename each named document to a fresh temporary code, drop its
    `number:`, and rewrite its code everywhere `concretize` would. Prints
    each rename and how many files changed."""
    if not codes:
        raise SystemExit("luria unconcretize: name at least one code, "
                         "e.g. `luria unconcretize ADR-068`")
    plan = []
    minted: set[str] = set()
    for code in codes:
        scheme, number, path = _resolve(code)
        while (tail := new_mod._mint_tail(scheme)) in minted:
            pass
        minted.add(tail)
        plan.append((scheme.code(number), f"{scheme.prefix}-{tail}", path,
                     scheme.dir / f"{scheme.prefix}-{tail}.md"))
    if len({old for old, *_ in plan}) != len(plan):
        raise SystemExit("luria unconcretize: a code is named twice")
    changed = rewrite([(old, new) for old, new, _, _ in plan])
    for old, new, src, dest in plan:
        # The rewrite already reached the document's own heading and
        # citations; what is left is its identity, the filename and the
        # `number:` a temporary document must not carry (#355).
        text = new_mod.drop_number(src.read_text(encoding="utf-8"))
        writes.write_text(dest, text)
        writes.unlink(src)
        print(f"{old} → {new}")
    print(f"rewrote the codes in {len(changed)} file(s); "
          "`luria concretize` numbers them where merges serialize",
          file=sys.stdout)
    if not changed:
        print("luria unconcretize: no file cited them", file=sys.stderr)


if __name__ == "__main__":
    import fire
    fire.Fire(run)
