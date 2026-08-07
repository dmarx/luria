"""`luria init` never overwrites, and says something useful when it skips
the one file an agent reads first (ADR-037)."""
import sys
from pathlib import Path

from luria import init


def test_existing_files_are_kept_verbatim(tmp_path, capsys):
    (tmp_path / "CLAUDE.md").write_text("mine, hands off\n")
    written, skipped, kept = init.write(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text() == "mine, hands off\n"
    assert any(p.name == "CLAUDE.md" for p in kept)
    assert skipped >= 1 and written >= 1


def test_a_kept_claude_md_gets_the_map_pointer(tmp_path, monkeypatch, capsys):
    """The file isn't touched — the recommendation goes to stdout, where
    permission isn't needed."""
    (tmp_path / "CLAUDE.md").write_text("mine, hands off\n")
    monkeypatch.setattr(sys, "argv",
                        ["luria init", "--into", str(tmp_path), "--dry-run"])
    assert init.main() == 0
    out = capsys.readouterr().out
    assert "left alone" in out and "luria --help" in out
    assert (tmp_path / "CLAUDE.md").read_text() == "mine, hands off\n"
