"""The entry point's surface: what dispatches, what refuses, and how.

The dispatch itself is exercised end-to-end by every other test file; what
needs its own tests is the refusal behavior — a retired command must name its
successor rather than plead ignorance (ADR-030, DP-1).
"""

from __future__ import annotations

import pytest

from luria import cli


def test_help_tiers_the_commands(capsys):
    assert cli.main(["--help"]) == 0
    out = capsys.readouterr().out
    contributor = out.index("commands:")
    ci_tier = out.index("run by CI")
    assert contributor < ci_tier
    for name in cli.COMMANDS:
        assert f"\n  {name}" in out
    for name in cli.CI_COMMANDS:
        assert out.index(f"\n  {name}") > ci_tier


@pytest.mark.parametrize("name,successor", [
    ("badges", "luria index"),
    ("ref-status", "luria reports"),
    ("pending", "luria reports"),
])
def test_retired_commands_name_their_successor(capsys, name, successor):
    assert cli.main([name]) == 2
    err = capsys.readouterr().err
    assert "retired" in err
    assert successor in err
    assert "unknown" not in err, "a retirement is not ignorance"


def test_unknown_command_shows_usage(capsys):
    assert cli.main(["frobnicate"]) == 2
    err = capsys.readouterr().err
    assert "unknown command" in err
    assert "usage:" in err


def test_no_retired_command_is_still_registered():
    registered = set(cli.COMMANDS) | set(cli.CI_COMMANDS)
    assert not registered & set(cli.RETIRED)
