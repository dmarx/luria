"""`luria` — one entry point for the whole record, driven by Fire (ADR-039).

    luria lint          check the record; the only command that can fail
    luria link [--fix]  rewrite bare references as hyperlinks
    luria repair        write every mechanical source repair: links, a
                        journal entry's missing `created:`
    luria index         regenerate every generated view, badges included
    luria new [kind]    scaffold an entry: the journal by default, or any
                        configured scheme or fragment dir (adr, dp, changelog)
    luria concretize    assign real numbers to temporary codes (ADR-049);
                        --check is the trunk's guard
    luria migrate       execute a migration spec: rename a scheme, move
                        documents between schemes (ADR-040)
    luria remotes       other projects' records cited from this one
    luria site          stage the record as a Quartz vault, ready to build
    luria init          scaffold the record into a project that has none
    luria config        write a starting luria.toml and stop, for editing
                        before anything is scaffolded

Two more exist for CI, which is their only regular caller:

    luria reports       write the status reports as markdown, for an artifact
    luria collect       assemble fragment directories into their views

Each command is a plain typed function (`<module>.run`), and Fire derives the
flags and help from the signatures and docstrings — there is no argparse
layer left to drift from the functions it wrapped. A command signals failure
by raising `SystemExit`, never by returning a value: Fire prints return
values, and a CI gate's exit code is not output.

The modules still run standalone (`python -m luria.ref_status --all`) via the
same functions — useful when a project vendors one file instead of installing
the package.
"""

import sys

import fire

from . import (adr_index, collect, concretize, init, link_refs, lint, migrate,
               new, remotes, repair, reports, site)

COMMANDS = {
    "lint": lint.run,
    "link": link_refs.run,
    "repair": repair.run,
    "index": adr_index.run,
    "new": new.run,
    "concretize": concretize.run,
    "migrate": migrate.run,
    "remotes": remotes.run,
    "site": site.run,
    "init": init.run,
    "config": init.config_run,
    "reports": reports.run,
    "collect": collect.run,
}

# Run by CI on every push; runnable by hand, but nothing in the contributor
# workflow needs them — `collect` even mildly misfires locally, consuming
# fragments a reviewer was meant to see on the branch.
CI_COMMANDS = {
    "reports": ("luria.reports", "write the status reports as markdown"),
    "collect": ("luria.collect", "assemble fragments into their views"),
}


def _survivable_console() -> None:
    """Never let a console encoding turn output into a traceback.

    Every file this package reads and writes is UTF-8 by construction, but the
    *console* belongs to the platform: a Windows terminal at cp1252 cannot
    encode the arrow in `luria init → path`, and the default behaviour is to
    raise rather than to degrade. That turned a scaffold into a stack trace on
    a machine where nothing was wrong (#112).

    The stream keeps its own encoding — writing UTF-8 at a cp1252 console
    would trade a crash for mojibake — and only its error handling changes, so
    a character the console cannot show becomes `?` and the line still reads.
    Set `PYTHONUTF8=1` for full fidelity."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass          # not a reconfigurable stream; nothing to protect


def main() -> int:
    _survivable_console()
    fire.Fire(COMMANDS, name="luria")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
