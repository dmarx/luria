"""`luria <command>` — one entry point for the whole record.

    luria lint          check the record; the only command that can fail
    luria link [--fix]  rewrite bare references as hyperlinks
    luria index         regenerate the decision index and tag pages
    luria ref-status    references to retired documents, with their sites
    luria pending       undecided decisions by age and citation count
    luria reports       write both reports as markdown, for a CI artifact
    luria collect       assemble fragment directories into their views
    luria remotes       other projects' records cited from this one
    luria badges        the README's needs-decision / cited-but-retired counts
    luria init          scaffold the record into a project that has none

Subcommands delegate to modules that each keep their own `main()`, so any of
them still runs standalone — useful when a project vendors one file instead of
installing the package.
"""

from __future__ import annotations

import sys

COMMANDS = {
    "lint": ("luria.lint", "the docs lint — the only command that fails"),
    "link": ("luria.link_refs", "rewrite bare references as hyperlinks"),
    "index": ("luria.adr_index", "regenerate the decision index"),
    "ref-status": ("luria.ref_status", "references to retired documents"),
    "pending": ("luria.adr_pending", "undecided decisions, by age"),
    "reports": ("luria.reports", "write both reports as markdown"),
    "collect": ("luria.collect", "assemble fragments into their views"),
    "remotes": ("luria.remotes", "other projects' records, and how they resolve"),
    "badges": ("luria.badges", "the README's two counts, derived from the record"),
    "init": ("luria.init", "scaffold the record into a project"),
}


def usage() -> str:
    width = max(len(name) for name in COMMANDS)
    lines = ["usage: luria <command> [options]", "", "commands:"]
    lines += [f"  {name:<{width}}  {blurb}" for name, (_, blurb) in COMMANDS.items()]
    lines += ["", "Every command takes --help."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(usage())
        return 0
    name = argv[0]
    if name not in COMMANDS:
        # No silent refusal: say what was asked for and what exists (DP-1).
        print(f"luria: unknown command {name!r}\n", file=sys.stderr)
        print(usage(), file=sys.stderr)
        return 2

    module_name, _ = COMMANDS[name]
    from importlib import import_module
    module = import_module(module_name)
    sys.argv = [f"luria {name}", *argv[1:]]
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
