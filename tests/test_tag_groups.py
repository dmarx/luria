"""`[luria.schemes.X.tag_groups]` — which of a scheme's tags may combine.

`tags.yaml` has always said what a tag *means* and nothing has said which may
appear together. For a pile of labels that is right; for an axis it leaves the
rule to prose. The motivating case came from a downstream record whose decision
said "exactly one strength tag" and whose fourth argument shipped with none,
four documents before anyone counted.
"""
from pathlib import Path

import pytest

from luria import config, lint

CONFIG = """\
[luria]
issue_url = "https://example.test/{n}"

[luria.schemes.ARG]
dir = "record/arguments.d"
output = "docs/arguments"
active = "Active"
render = "index"

[luria.schemes.ARG.tag_groups.strength]
tags = ["sound", "overreach", "invalid"]
require = "exactly-one"

[luria.schemes.ARG.tag_groups.failure]
tags = ["equivocation", "gap"]
excluded_by = ["sound"]
"""


def project(tmp_path: Path, monkeypatch, *tags: str, cfg: str = CONFIG) -> Path:
    (tmp_path / "luria.toml").write_text(cfg)
    d = tmp_path / "record" / "arguments.d"
    d.mkdir(parents=True)
    block = ("tags:\n" + "".join(f"- {t}\n" for t in tags)) if tags else "tags: []\n"
    (d / "ARG-001.md").write_text(
        f"---\nstatus: Active\ntitle: 'An argument'\nversion: 1\n"
        f"{block}date: '2026-01-01'\n---\n\n# ARG-001: An argument\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def errors_for(tmp_path, monkeypatch, *tags: str, cfg: str = CONFIG) -> list[str]:
    project(tmp_path, monkeypatch, *tags, cfg=cfg)
    errors: list[str] = []
    lint.check_contracts(errors)
    return errors


def test_exactly_one_is_satisfied(tmp_path, monkeypatch):
    assert errors_for(tmp_path, monkeypatch, "overreach") == []


def test_exactly_one_rejects_none(tmp_path, monkeypatch):
    """The defect this feature was built for: an argument carrying only a
    failure mode and no strength."""
    errors = errors_for(tmp_path, monkeypatch, "gap")
    assert len(errors) == 1
    assert "wants exactly one of" in errors[0] and "has none" in errors[0]


def test_exactly_one_rejects_two(tmp_path, monkeypatch):
    errors = errors_for(tmp_path, monkeypatch, "sound", "invalid")
    assert len(errors) == 1
    assert "invalid, sound" in errors[0]


def test_excluded_by_catches_a_contradiction(tmp_path, monkeypatch):
    """Naming how an argument fails contradicts saying it does not."""
    errors = errors_for(tmp_path, monkeypatch, "sound", "gap")
    assert len(errors) == 1
    assert "sound excludes `failure`" in errors[0]


def test_excluded_by_is_silent_when_the_group_is_absent(tmp_path, monkeypatch):
    assert errors_for(tmp_path, monkeypatch, "sound") == []


def test_at_most_one_allows_zero(tmp_path, monkeypatch):
    cfg = CONFIG.replace('require = "exactly-one"', 'require = "at-most-one"')
    assert errors_for(tmp_path, monkeypatch, cfg=cfg) == []


def test_a_scheme_with_no_groups_is_unconstrained(tmp_path, monkeypatch):
    """Every record that predates this feature."""
    cfg = CONFIG.split("[luria.schemes.ARG.tag_groups.strength]")[0]
    assert errors_for(tmp_path, monkeypatch, "anything", cfg=cfg) == []


def test_an_unknown_rule_is_a_config_error(tmp_path, monkeypatch):
    """Caught at parse time. A misspelled rule that surfaced as 'no
    violations' would be the quiet failure this feature exists to remove."""
    cfg = CONFIG.replace('require = "exactly-one"', 'require = "one"')
    with pytest.raises(ValueError, match="require = 'one'"):
        project(tmp_path, monkeypatch, "sound", cfg=cfg)
        config.current()


def test_a_group_with_no_tags_is_a_config_error(tmp_path, monkeypatch):
    cfg = CONFIG.replace('tags = ["sound", "overreach", "invalid"]', "tags = []")
    with pytest.raises(ValueError, match="lists no tags"):
        project(tmp_path, monkeypatch, "sound", cfg=cfg)
        config.current()
