"""What luria says differently when it is being read in a build (ADR-029).

The failure these cover is not a wrong number — it is correct advice given in
the one place it must not be followed. "run `luria index`" clears a staleness
failure in a working copy and, inside a checking job, makes the check inert:
the generator rewrites the files the check is about to compare, so it can no
longer fail. An adopter followed that message verbatim into their CI and got a
green build with a dead gate.

So these tests are about *text*, and they assert on the part that carries the
warning rather than on whole strings — a message that can be reworded without a
test failing is one that will be.
"""
import pytest

from _scheme import decision

from luria import badges, ci, lint


@pytest.fixture(autouse=True)
def _no_ambient_ci(monkeypatch):
    """The suite itself runs in CI, so every var must be cleared per-test or
    these assertions read the runner's environment instead of the fixture's —
    a test that passes locally and inverts on GitHub Actions."""
    for var in ci.CI_VARS:
        monkeypatch.delenv(var, raising=False)


# ── Detection ────────────────────────────────────────────────────────────


def test_a_bare_shell_is_not_ci():
    assert ci.running_in_ci() is False


@pytest.mark.parametrize("var", ci.CI_VARS)
def test_any_known_variable_is_enough(monkeypatch, var):
    """Every vendor gets its own name, so dropping the generic `CI` doesn't
    silently take the advice with it."""
    monkeypatch.setenv(var, "true")
    assert ci.running_in_ci() is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "  False  "])
def test_a_runner_saying_not_a_build_is_believed(monkeypatch, value):
    """Some runners export CI=false to mean exactly that."""
    monkeypatch.setenv("CI", value)
    assert ci.running_in_ci() is False


# ── The remedy ───────────────────────────────────────────────────────────


def test_a_terminal_gets_the_bare_command():
    """In a working copy the command *is* the whole answer; padding it with CI
    advice would train people to skim the one message that matters."""
    assert ci.regenerate_remedy() == "run `luria index`"


def test_ci_is_offered_both_ways_to_commit(monkeypatch):
    """The remedy must not steer people away from automating regeneration —
    that was this decision's rejected first draft, and it outlaws generation
    jobs. Both legitimate routes get named (ADR-029)."""
    monkeypatch.setenv("CI", "true")
    remedy = ci.regenerate_remedy()
    assert "locally" in remedy
    assert "generation job" in remedy and "pushes" in remedy


def test_ci_warns_against_the_shape_that_commits_nothing(monkeypatch):
    """The broken shape is specifically 'generator in the checking job on the
    default branch, output committed by nobody' — not 'a generator ran in
    CI', and not a branch, which carries no view of its own (ADR-068)."""
    monkeypatch.setenv("CI", "true")
    remedy = ci.regenerate_remedy()
    assert "default branch" in remedy
    assert "carries no view of its own and is not checked for one" in remedy
    assert "comparing that output against itself" in remedy


def test_the_remedy_never_forbids_generating_in_ci(monkeypatch):
    """A guard on the correction, since the wrong version reads perfectly well
    and would sail through review a second time."""
    monkeypatch.setenv("CI", "true")
    remedy = ci.regenerate_remedy().lower()
    for forbidding in ("do not add", "never", "must not", "nothing that writes"):
        assert forbidding not in remedy, f"remedy forbids generation: {remedy!r}"


def test_the_remedy_names_the_command_it_was_given(monkeypatch):
    monkeypatch.setenv("CI", "true")
    assert "`luria collect`" in ci.regenerate_remedy("luria collect")


# ── Reaching the messages people actually read ───────────────────────────


def test_the_staleness_check_carries_the_ci_remedy(monkeypatch, project, capsys):
    """The integration that matters: this is the exact string an adopter reads
    in a build log when the index goes stale, and the reason they reached for
    the wrong fix. `luria index --check` is where it is read now — the lint
    asks no staleness question (ADR-068)."""
    from luria import adr_index
    decision(project, 1, "Active")
    (project / "docs" / "decisions" / "README.md").write_text("stale\n")
    monkeypatch.setenv("CI", "true")

    with pytest.raises(SystemExit):
        adr_index.run(check=True)
    err = capsys.readouterr().err
    assert "regenerate and commit the result" in err
    assert "generation job" in err


def test_bare_badges_says_it_only_printed(capsys, monkeypatch, project):
    """Bare `python -m luria.badges` exits 0 having written nothing. Printing
    the markdown is legitimate; looking like a write is not (DP-1). The
    `luria badges` command itself is retired (ADR-030), so only the module
    entry point can reach this."""
    decision(project, 1, "Active")
    assert badges.run() is None

    out, err = capsys.readouterr()
    assert badges.OPEN in out, "the markdown still goes to stdout"
    assert "printed only" in err
    assert "printed only" not in out, "stdout stays clean for redirection"
