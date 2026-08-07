"""`luria init` — scaffold the record into a project that has none.

    luria init                    # into the current project root
    luria init --into PATH
    luria init --dry-run          # list what would be written

Copies the `template/` tree: the four layers' directories and their templates,
a `luria.toml` with the project's issue URL, a seed set of design principles,
and a `CLAUDE.md` section pointing an agent at all of it.

**Nothing is overwritten.** Existing files are reported as skipped, so running
this on a project that already has half the record adds only the missing half —
and running it twice is a no-op. A scaffolder that clobbers is a scaffolder
nobody dares re-run, which means the one thing it is good at (filling in what a
project grew past) never gets used.

The seed principles are deliberately about *the record itself* — drift, locks,
one authoritative implementation. They are the ones a project needs before it
has learned anything of its own, and they are the ones that earn the machinery
in this package. Delete the ones you disagree with; a principle nobody believes
is worse than an empty file.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .config import CONFIG_NAME, find_root

def _template_dir() -> Path:
    """The scaffold's location, which depends on how Luria arrived.

    Installed from a wheel, the template ships inside the package
    (`luria/template/`, ADR-027); in a checkout it sits at the repository
    top level, where a visitor browses it (ADR-021). Packaged wins when both
    exist, because an installed Luria should scaffold what it shipped."""
    packaged = Path(__file__).resolve().parent / "template"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parent.parent / "template"


TEMPLATE = _template_dir()


def plan(into: Path) -> list[tuple[Path, Path]]:
    """(source, destination) for every template file, in a stable order."""
    if not TEMPLATE.is_dir():                       # installed without data
        return []
    return [(src, into / src.relative_to(TEMPLATE))
            for src in sorted(TEMPLATE.rglob("*")) if src.is_file()]


def write(into: Path, issue_url: str = "",
          dry_run: bool = False) -> tuple[int, int, list[Path]]:
    written = skipped = 0
    kept: list[Path] = []
    for src, dest in plan(into):
        if dest.exists():
            print(f"  skip   {dest.relative_to(into)} (exists)")
            skipped += 1
            kept.append(dest)
            continue
        print(f"  write  {dest.relative_to(into)}")
        written += 1
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text()
        if dest.name == CONFIG_NAME and issue_url:
            text = text.replace(
                'issue_url = ""',
                f'issue_url = "{issue_url.rstrip("/")}/{{n}}"'
                if "{n}" not in issue_url else f'issue_url = "{issue_url}"')
        dest.write_text(text)
        shutil.copystat(src, dest)
    return written, skipped, kept


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--into", type=Path, default=None,
                    help="project root (default: the detected one)")
    ap.add_argument("--issue-url", default="",
                    help="e.g. https://github.com/owner/repo/issues — written "
                         "into luria.toml so issue numbers become links")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    into = (args.into or find_root()).resolve()
    print(f"luria init → {into}")
    written, skipped, kept = write(into, args.issue_url, args.dry_run)
    if not written and not skipped:
        print("  nothing to write — is the template directory installed?")
        return 1
    verb = "would write" if args.dry_run else "wrote"
    print(f"{verb} {written} file(s), skipped {skipped} existing.")
    # A file the project already owns is never touched — but the one an
    # agent reads first deserves more than a silent skip (DP-1): say what
    # the scaffolded shape would have been, and leave the merge to a human
    # or their agent.
    if any(p.name == "CLAUDE.md" for p in kept):
        print("\nYour CLAUDE.md was left alone. The scaffolded shape is a "
              "short map — links to the record's docs plus an invitation to "
              "run `luria --help` (LU-ADR-037). Worth borrowing: ask your "
              "agent to fold that shape into your existing file.")
    if written and not args.dry_run:
        print("\nNext: `luria index` to build the decision index, then "
              "`luria lint`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
