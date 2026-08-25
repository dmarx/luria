"""`luria` — one entry point for the whole record, driven by Fire (ADR-039).

    luria lint          check the record; the only command that can fail
    luria link [--fix]  rewrite bare references as hyperlinks
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

Two more exist for CI, which is their only regular caller:

    luria reports       write the status reports as markdown, for an artifact
    luria collect       assemble fragment directories into their views
    luria skip-markers  commits whose message told the forge not to build

Each command is a plain typed function (`<module>.run`), and Fire derives the
flags and help from the signatures and docstrings — there is no argparse
layer left to drift from the functions it wrapped. A command signals failure
by raising `SystemExit`, never by returning a value: Fire prints return
values, and a CI gate's exit code is not output.

The modules still run standalone (`python -m luria.ref_status --all`) via the
same functions — useful when a project vendors one file instead of installing
the package.
"""

import fire

from . import (adr_index, ci, collect, concretize, init, link_refs, lint,
               migrate, new, remotes, reports, site)

COMMANDS = {
    "lint": lint.run,
    "link": link_refs.run,
    "index": adr_index.run,
    "new": new.run,
    "concretize": concretize.run,
    "migrate": migrate.run,
    "remotes": remotes.run,
    "site": site.run,
    "init": init.run,
    "reports": reports.run,
    "collect": collect.run,
    "skip-markers": ci.run,
}

# Run by CI on every push; runnable by hand, but nothing in the contributor
# workflow needs them — `collect` even mildly misfires locally, consuming
# fragments a reviewer was meant to see on the branch.
CI_COMMANDS = {
    "reports": ("luria.reports", "write the status reports as markdown"),
    "collect": ("luria.collect", "assemble fragments into their views"),
    "skip-markers": ("luria.ci", "commits that suppressed their own build"),
}


def main() -> int:
    fire.Fire(COMMANDS, name="luria")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
