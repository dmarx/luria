# tests/test_timing.py
"""`LURIA_TIMINGS`: where a run spends its time, printed only on request."""

from __future__ import annotations

from luria.timing import timed


def test_a_timed_block_is_silent_by_default(monkeypatch, capsys):
    monkeypatch.delenv("LURIA_TIMINGS", raising=False)
    with timed("facts"):
        pass
    assert capsys.readouterr().err == ""


def test_a_timed_block_reports_when_asked(monkeypatch, capsys):
    monkeypatch.setenv("LURIA_TIMINGS", "1")
    with timed("facts") as t:
        t["note"] = "3 facts"
    err = capsys.readouterr().err
    assert err.startswith("luria: timing: facts ") and ", cpu " in err
    assert err.endswith("s (3 facts)\n")


def test_zero_means_off(monkeypatch, capsys):
    monkeypatch.setenv("LURIA_TIMINGS", "0")
    with timed("facts"):
        pass
    assert capsys.readouterr().err == ""
