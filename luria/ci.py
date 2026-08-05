#!/usr/bin/env python3
"""Whether this is a build, and what that changes about what luria says.

A generated view is a **committed artifact**. Who commits it is open: the
author can regenerate and commit, or a generation job can run the generator
and push what it wrote — the second is usually better, since a view a human
has to rebuild by hand is still a hand-maintained projection (ADR-029).

What is *not* open is dropping the generator into a checking job and
committing nothing. That discards the output and, if a `luria lint` follows in
the same job, leaves the lint comparing the generator's output against itself
so it can no longer fail. The message that has to carry this is the staleness
remedy, because a staleness failure is usually read first in a CI log — where
the bare "run `luria index`" omits exactly the half that matters.

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
    return (f"regenerate and commit the result — run `{command}` locally, or "
            f"give CI a generation job that runs it and pushes what it wrote. "
            f"Adding `{command}` to this checking job is not enough on its "
            f"own: nothing would commit its output, and this check would be "
            f"comparing that output against itself")


def wasted_write_warning(command: str) -> str | None:
    """The note a writing command prints when it is writing inside a build.

    Returns None outside CI, and never refuses: writing in CI is how a
    generation job works (`luria collect --commit`, a `luria index` step that
    pushes). This is the alarm for the case that *looks* identical from the
    log — a write whose result is discarded at job end — because the whole
    subject of this package is machinery that quietly stops being true
    (DP-1)."""
    if not running_in_ci():
        return None
    return (f"{command}: writing generated views inside CI. If this job "
            f"commits and pushes them, all is well and this note is noise. If "
            f"it does not, the result is discarded when the job ends — the "
            f"files this wrote will never reach the repository, and if a "
            f"`luria lint` runs after it in the same job, that lint is now "
            f"comparing the generator's output against itself and can no "
            f"longer fail (ADR-029).")
