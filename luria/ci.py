#!/usr/bin/env python3
"""Whether this is a build, and what that changes about what luria says.

A generated view is a **committed artifact**: the author runs `luria index`
and commits what it wrote, and CI's only job is to verify. That split is
invisible from inside a single command, and one message straddles it badly —
"run `luria index`" is the correct remedy in a working copy and the *worst*
available action inside a checking job, where the generator rewrites the very
files the check is about to compare and the gate stops being able to fail
(ADR-029).

Since a staleness failure is usually seen first in a CI log, the remedy has to
know which side of that split it is being read on. Detection is deliberately
crude — every CI sets `CI` — and it only ever changes what is *said*, never
what is done: a false positive costs a sentence of advice, a false negative
leaves today's behaviour. Nothing here gates a write or an exit code.
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

    In a terminal the bare command is the whole answer. In a build it is a
    trap, so the CI form says the two things the short version leaves the
    reader to guess: that the fix belongs in a working copy and is committed,
    and that adding the generator *here* would make this check inert rather
    than fix it."""
    if not running_in_ci():
        return f"run `{command}`"
    return (f"run `{command}` locally and commit what it wrote — generated "
            f"views are committed artifacts. Do not add `{command}` to this "
            f"job: it would rewrite the files this check compares, and the "
            f"check would stop being able to fail")


def wasted_write_warning(command: str) -> str | None:
    """The note a writing command prints when it is writing inside a build.

    Returns None outside CI. Not an error, and not a refusal — a scheduled job
    that commits its own output (`luria collect --commit`) writes in CI
    legitimately. But a write whose result is discarded at job end looks
    exactly like one that landed, and the whole subject of this package is
    machinery that quietly stops being true (DP-1)."""
    if not running_in_ci():
        return None
    return (f"{command}: writing generated views inside CI. Unless this job "
            f"commits and pushes them, the result is discarded when the job "
            f"ends — the files this wrote will not reach the repository. If "
            f"this is a checking job, run `luria lint` instead and let the "
            f"author regenerate: a generator ahead of the check rewrites what "
            f"the check compares, so the check can no longer fail (ADR-029).")
