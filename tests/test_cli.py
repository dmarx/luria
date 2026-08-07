"""The entry point's surface: what dispatches, and how a refusal reads.

The dispatch itself is exercised end-to-end by every other test file; what
needs its own tests is the shape of the surface (ADR-030) — two tiers in the
help, and a clean "unknown command" for everything else, the retired names
included: they are gone, not deprecated, so nothing here knows them.
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


@pytest.mark.parametrize("name", ["frobnicate", "badges", "ref-status", "pending"])
def test_unknown_commands_show_usage(capsys, name):
    """One refusal for everything unregistered — a removed command is not a
    special case, because keeping it special would be keeping it."""
    assert cli.main([name]) == 2
    err = capsys.readouterr().err
    assert "unknown command" in err
    assert "usage:" in err
