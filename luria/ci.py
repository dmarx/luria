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

The second question this module answers is the inverse: whether a commit
message has accidentally told the forge **not to build**. See
`prose_skip_marker` — same posture, nothing gated, only something said.
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


# A third helper was built here and removed before merge: a warning printed
# whenever a generator wrote inside CI. It fired on every run of a *correct*
# generation job and had to describe itself as noise in that case — and a
# warning that is usually noise trains readers to skip warnings, the flaky-
# guard dynamic this record already documents. The remedy above is the whole
# surface: it fires only when a check has actually failed (ADR-029).


# ── Skip markers written as prose ────────────────────────────────────────
#
# The forge skips a workflow run when the head commit's message carries one
# of these. That is a useful convention and this package depends on it: the
# generate action marks its own commits so a bot push opens no run.
#
# The hazard is that the convention has no escape: a message *describing* the
# marker contains the marker, so writing about it suppresses the build for the
# commit that writes about it. Observed in the wild, in a commit adopting this
# very workflow, by an author who had read the warning first — which is the
# evidence that a comment was not enough.
#
# GitHub documents the marker as honoured in the first or last line. Measured,
# it is broader than that: a marker in the middle of a body suppressed every
# workflow on the commit. So the position below is not a claim about what the
# forge honours; it is a claim about what the AUTHOR meant.
SKIP_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]",
                "[skip actions]", "[actions skip]")


def prose_skip_marker(message: str) -> str | None:
    """The skip marker this message carries in a *prose* position, or None.

    The whole design is the position, and it is what keeps this quiet enough
    to be worth having. Someone deliberately skipping a build puts the marker
    where the convention puts it — the subject line, or a trailer at the end —
    and every tool that generates one does the same, this package's own
    generate action included. Someone *writing about* the convention lands it
    in the middle of a paragraph.

    So a marker in the first or last line is read as an instruction and passes
    silently; one in the body is read as prose and is reported. That single
    rule is why no author check is needed: the bot's `docs: regenerate views
    [skip ci]` is one line, which is first and last at once, and never fires.

    The failure being caught is unusually easy to miss, which is the argument
    for catching it at all. A suppressed run is not a red build — it is *no*
    build, and the pull request goes on displaying the previous commit's green
    checks. Silence is indistinguishable from success unless someone thinks to
    ask which commit the green belongs to.
    """
    lines = message.strip().splitlines()
    # Two lines or fewer is all instruction position and no body.
    for line in lines[1:-1]:
        lowered = line.lower()
        for marker in SKIP_MARKERS:
            if marker in lowered:
                return marker
    return None


def commits(rev_range: str) -> list[tuple[str, str]]:
    """`(sha, message)` for each commit in the range, newest first.

    Returns nothing when git cannot answer — a shallow checkout is the
    ordinary case (`actions/checkout` fetches depth 1 by default), and a
    guard that cannot see history has nothing to say. It must not turn that
    into a failure: the build would break on a checkout setting rather than
    on anything about the code.
    """
    import subprocess
    try:
        out = subprocess.run(
            ["git", "log", "--format=%H%n%B%x00", rev_range],
            capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    found = []
    for chunk in out.split("\0"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        sha, _, message = chunk.partition("\n")
        found.append((sha.strip(), message))
    return found


def run(rev_range: str = "HEAD~20..HEAD", strict: bool = False) -> None:
    """Report commits that tell the forge not to build while meaning to talk
    about it — a skip marker sitting in prose rather than in the subject or a
    trailer (`prose_skip_marker`).

    Prints nothing when there is nothing to say. That is deliberate and it is
    the lesson this module already learned once: a warning printed on correct
    runs trains readers to skip warnings, and the check that fires on every
    green build is the one nobody reads on the red one.

    Warns rather than fails by default, matching the record's posture
    everywhere else; `--strict` promotes it for a project that wants the
    build to stop.
    """
    import sys
    hits = [(sha, marker)
            for sha, message in commits(rev_range)
            if (marker := prose_skip_marker(message))]
    if not hits:
        return
    annotate = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    for sha, marker in hits:
        text = (f"{sha[:8]} carries `{marker}` in its message body. If this "
                f"commit was ever the tip of a push, its checks did not run "
                f"— a suppressed run is not a red build, it is no build, and "
                f"the previous commit's green stays on display. Write about "
                f"the marker in prose, or move it to the subject line if the "
                f"skip was meant.")
        print(f"::warning::{text}" if annotate else f"luria: {text}",
              file=sys.stderr)
    if strict:
        raise SystemExit(1)
