"""The entry point under Fire (ADR-039): typed functions, derived help,
exit codes by SystemExit only.

The dispatch itself is exercised end-to-end by every other test file and by
the smoke run in publish.yml; what needs its own tests is the surface — the
eight commands are registered, an unknown name refuses with the list, and a
failing gate's exit code survives Fire.
"""

from __future__ import annotations

import subprocess
import sys

from luria import adr_index, cli, collect, init, link_refs, lint, new, remotes, reports


def test_the_eight_commands_are_registered():
    assert cli.COMMANDS == {
        "lint": lint.run, "link": link_refs.run, "index": adr_index.run,
        "new": new.run, "remotes": remotes.run, "init": init.run,
        "reports": reports.run, "collect": collect.run,
    }


def _luria(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "luria.cli", *args],
                          capture_output=True, text=True)


def test_an_unknown_command_refuses_with_the_list():
    proc = _luria("frobnicate")
    assert proc.returncode == 2
    assert "Cannot find key" in proc.stderr
    for name in cli.COMMANDS:
        assert name in proc.stderr, "the refusal names what does exist"


def test_help_derives_from_the_functions():
    proc = _luria("--", "--help")
    out = proc.stdout + proc.stderr
    for name in cli.COMMANDS:
        assert name in out


def test_a_failing_gate_exits_nonzero(tmp_path, monkeypatch):
    """`luria lint` as a CI gate: SystemExit must survive Fire — Fire prints
    return values, so an exit code can never be a return value."""
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    (tmp_path / "luria.toml").write_text('[luria]\nissue_url = ""\n')
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("# Docs\n")
    (docs / "unindexed.md").write_text("# Orphan\n")
    proc = subprocess.run([sys.executable, "-m", "luria.cli", "lint"],
                          capture_output=True, text=True,
                          env={**__import__("os").environ,
                               "LURIA_ROOT": str(tmp_path)})
    assert proc.returncode == 1
    assert "missing index entry" in proc.stderr
