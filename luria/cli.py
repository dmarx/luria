"""`luria <command>` — one entry point for the whole record.

    luria lint          check the record; the only command that can fail
    luria link [--fix]  rewrite bare references as hyperlinks
    luria index         regenerate every generated view, badges included
    luria journal new   file a dated entry in a journal (the devlog)
    luria remotes       other projects' records cited from this one
    luria init          scaffold the record into a project that has none

Two more exist for CI, which is their only regular caller:

    luria reports       write the status reports as markdown, for an artifact
    luria collect       assemble fragment directories into their views

The surface used to be wider — one command per module, eleven in all — which
mirrored the package layout rather than anyone's workflow (ADR-030). A retired
command answers with where its job went, not "unknown command".

Subcommands delegate to modules that each keep their own `main()`, so any of
them still runs standalone (`python -m luria.ref_status`) — useful when a
project vendors one file instead of installing the package, and how the
retired reports stay reachable in full detail.
"""

from __future__ import annotations

import sys

COMMANDS = {
    "lint": ("luria.lint", "the docs lint — the only command that fails"),
    "link": ("luria.link_refs", "rewrite bare references as hyperlinks"),
    "index": ("luria.adr_index", "regenerate every generated view"),
    "journal": ("luria.journal", "dated entries that persist, rendered into books"),
    "remotes": ("luria.remotes", "other projects' records, and how they resolve"),
    "init": ("luria.init", "scaffold the record into a project"),
}

# Run by CI on every push; runnable by hand, but nothing in the contributor
# workflow needs them — `collect` even mildly misfires locally, consuming
# fragments a reviewer was meant to see on the branch.
CI_COMMANDS = {
    "reports": ("luria.reports", "write the status reports as markdown"),
    "collect": ("luria.collect", "assemble fragments into their views"),
}

# Each of these was subsumed before it was retired (ADR-030); the refusal
# names the successor rather than pleading ignorance (DP-1).
RETIRED = {
    "badges": "`luria index` writes the README's badges and `luria lint` "
              "checks them; the markdown itself is `python -m luria.badges`",
    "ref-status": "`luria lint` prints the summary and `luria reports` writes "
                  "every site; interactively, `python -m luria.ref_status --all`",
    "pending": "`luria lint` prints the headline and `luria reports` writes "
               "the table; interactively, `python -m luria.adr_pending`",
}


def usage() -> str:
    names = {**COMMANDS, **CI_COMMANDS}
    width = max(len(name) for name in names)
    lines = ["usage: luria <command> [options]", "", "commands:"]
    lines += [f"  {name:<{width}}  {blurb}" for name, (_, blurb) in COMMANDS.items()]
    lines += ["", "run by CI, rarely by hand:"]
    lines += [f"  {name:<{width}}  {blurb}" for name, (_, blurb) in CI_COMMANDS.items()]
    lines += ["", "Every command takes --help."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(usage())
        return 0
    name = argv[0]
    if name in RETIRED:
        print(f"luria: {name!r} was retired — {RETIRED[name]}", file=sys.stderr)
        return 2
    commands = {**COMMANDS, **CI_COMMANDS}
    if name not in commands:
        # No silent refusal: say what was asked for and what exists (DP-1).
        print(f"luria: unknown command {name!r}\n", file=sys.stderr)
        print(usage(), file=sys.stderr)
        return 2

    module_name, _ = commands[name]
    from importlib import import_module
    module = import_module(module_name)
    sys.argv = [f"luria {name}", *argv[1:]]
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
