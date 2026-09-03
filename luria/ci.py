#!/usr/bin/env python3
"""Whether this is a build, and what that changes about what luria says.

A generated view is a **committed artifact**. Who commits it is open: the
author can regenerate and commit, or a generation job can run the generator
and push what it wrote — the second is usually better, since a view a human
has to rebuild by hand is still a hand-maintained projection (ADR-029).

Where the commit lands is decided (ADR-tmphzwg9): a view on the default
branch, where merges serialize; a source repair on the branch that authored
the source. A pull request pushes its repairs, regenerates the views in the
working tree and commits none of them, so a branch never carries a generated
file and two branches cannot conflict on one; the lint then runs in the same
job on the regenerated tree. What stays wrong is a checking job on the default
branch that regenerates and commits nothing — the output dies with the runner,
and a `luria lint` in the same job compares the generator against itself. The
staleness remedy has to carry that, because a staleness failure is usually
read first in a CI log, where the bare "run `luria index`" omits the half that
matters.

Detection is deliberately crude — every CI sets `CI` — and it only ever
changes what is *said*, never what is done: a false positive costs a sentence
of advice, a false negative leaves today's behaviour. Nothing here gates a
write or an exit code.
"""

from __future__ import annotations

import os

# `CI` alone covers GitHub Actions, GitLab, CircleCI, Buildkite, Travis and
# Woodpecker. The rest are named because a vendor that ever drops the generic
# variable should not silently take the advice with it.
CI_VARS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "BUILDKITE",
           "TF_BUILD", "TEAMCITY_VERSION", "JENKINS_URL")

# Some runners export CI=false to mean "not a build". Take them at their word.
FALSEY = {"", "0", "false", "no", "off"}


def running_in_ci(env: dict[str, str] | None = None) -> bool:
    """True when any known CI variable is set to something not falsey."""
    env = os.environ if env is None else env
    return any(env.get(v, "").strip().lower() not in FALSEY for v in CI_VARS)


def regenerate_remedy(command: str = "luria index") -> str:
    """"How do I clear this?" — answered for where the reader is standing.

    In a terminal the bare command is the whole answer. In a build the reader
    needs the half that is easy to miss: the output has to be **committed**.
    Both ways of doing that are legitimate — regenerate locally, or let a
    generation job commit and push — and the CI form names both rather than
    steering people away from automating it (ADR-029). What it warns against
    is the specific broken shape: dropping the generator into the checking job
    and committing nothing, which discards the output *and* leaves the check
    comparing the generator against itself."""
    if not running_in_ci():
        return f"run `{command}`"
    return (f"regenerate and commit the result on the default branch — run "
            f"`{command}` locally, or give CI a generation job that runs it "
            f"where merges serialize and pushes what it wrote. A pull request "
            f"regenerates the views before it lints and commits none of them, "
            f"so a stale view there means the check ran without the "
            f"generator; on the "
            f"default branch, `{command}` in the checking job alone is not "
            f"enough: nothing would commit its output, and this check would "
            f"be comparing that output against itself")


# A third helper was built here and removed before merge: a warning printed
# whenever a generator wrote inside CI. It fired on every run of a *correct*
# generation job and had to describe itself as noise in that case — and a
# warning that is usually noise trains readers to skip warnings, the flaky-
# guard dynamic this record already documents. The remedy above is the whole
# surface: it fires only when a check has actually failed (ADR-029).
