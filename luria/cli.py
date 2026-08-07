"""`luria <command>` — one entry point for the whole record.

    luria lint          check the record; the only command that can fail
    luria link [--fix]  rewrite bare references as hyperlinks
    luria index         regenerate every generated view, badges included
    luria new [kind]    scaffold an entry: the journal by default, or any
                        configured scheme or fragment dir (adr, dp, changelog)
    luria remotes       other projects' records cited from this one
    luria init          scaffold the record into a project that has none

Two more exist for CI, which is their only regular caller:

    luria reports       write the status reports as markdown, for an artifact
    luria collect       assemble fragment directories into their views

The surface used to be wider — one command per module, eleven in all — which
mirrored the package layout rather than anyone's workflow (ADR-030). The
excess names are gone, not deprecated: a shim would be an affordance for a
workflow nobody has.

Subcommands delegate to modules that each keep their own `main()`, so any of
them still runs standalone (`python -m luria.ref_status`) — useful when a
project vendors one file instead of installing the package.
"""

import sys

COMMANDS = {
    "lint": ("luria.lint", "the docs lint — the only command that fails"),
    "link": ("luria.link_refs", "rewrite bare references as hyperlinks"),
    "index": ("luria.adr_index", "regenerate every generated view"),
    "new": ("luria.new", "scaffold an entry: journal (default), adr, dp, changelog…"),
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
