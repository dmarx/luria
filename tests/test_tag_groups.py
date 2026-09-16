"""`fields.<field>.groups` — which of a field's values may combine.

`tags.yaml` has always said what a tag *means* and nothing has said which may
appear together. For a pile of labels that is right; for an axis it leaves the
rule to prose. The motivating case came from a downstream record whose decision
said "exactly one strength tag" and whose fourth argument shipped with none,
four documents before anyone counted.
"""

from _config import merged
from pathlib import Path

import pytest

from luria import config, lint

CONFIG = """
issue_url: https://example.test/{n}
schemes:
  ARG:
    dir: record/arguments.d
    output: docs/arguments
    active: Active
    render: index
    axis: tags
    fields:
      tags:
        many: true
        groups:
          strength:
            tags:
            - sound
            - overreach
            - invalid
            require: exactly-one
          failure:
            tags:
            - equivocation
            - gap
            excluded_by:
            - sound
"""


def project(tmp_path: Path, monkeypatch, *tags: str, cfg: str = CONFIG) -> Path:
    (tmp_path / "luria.yaml").write_text(cfg)
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
    cfg = merged(CONFIG, {"schemes": {"ARG": {"fields": {"tags": {"groups": {
        "strength": {"require": "at-most-one"}}}}}}})
    assert errors_for(tmp_path, monkeypatch, cfg=cfg) == []


def test_a_scheme_with_no_groups_is_unconstrained(tmp_path, monkeypatch):
    """Every record that predates this feature.

    The whole field goes, not just its `groups`: a scheme that says nothing
    about its tags declares no tags field, and then has no axis either
    (ADR-098)."""
    import yaml as _yaml
    raw = _yaml.safe_load(CONFIG)
    raw["schemes"]["ARG"].pop("axis")
    raw["schemes"]["ARG"].pop("fields")
    cfg = _yaml.dump(raw, sort_keys=False)
    assert errors_for(tmp_path, monkeypatch, "anything", cfg=cfg) == []


def test_an_unknown_rule_is_a_config_error(tmp_path, monkeypatch):
    """Caught at parse time. A misspelled rule that surfaced as 'no
    violations' would be the quiet failure this feature exists to remove."""
    cfg = merged(CONFIG, {"schemes": {"ARG": {"fields": {"tags": {"groups": {
        "strength": {"require": "one"}}}}}}})
    with pytest.raises(ValueError, match="require = 'one'"):
        project(tmp_path, monkeypatch, "sound", cfg=cfg)
        config.current()


def test_a_group_with_no_tags_is_a_config_error(tmp_path, monkeypatch):
    cfg = merged(CONFIG, {"schemes": {"ARG": {"fields": {"tags": {"groups": {
        "strength": {"tags": []}}}}}}})
    with pytest.raises(ValueError, match="lists no `tags`"):
        project(tmp_path, monkeypatch, "sound", cfg=cfg)
        config.current()


ALERTED = CONFIG.replace(
    "            require: exactly-one\n",
    "            require: exactly-one\n"
    "            alert: >-\n"
    "              Exactly one because strength is an axis, not a pile. If an\n"
    "              argument needs a word these three cannot say, add it here.\n",
    1)


def test_a_group_can_print_its_own_advice(tmp_path, monkeypatch):
    """The rule is mechanical and the reason for it is not (#273). A group
    has exactly one `require`, so one alert needs no per-rule key."""
    errors = errors_for(tmp_path, monkeypatch, "gap", cfg=ALERTED)
    assert len(errors) == 1
    assert "wants exactly one of" in errors[0]
    assert "Exactly one because strength is an axis, not a pile." in errors[0]
    assert "\n    \u21b3 " in errors[0], "the alert continues the finding rather than being a second one"


def test_a_group_alert_reaches_the_excluded_by_finding_of_the_SAME_group(
        tmp_path, monkeypatch):
    """`excluded_by` is that group's rule stated from the other side, so it
    carries that group's alert — and not a different group's."""
    cfg = CONFIG.replace(
        "            excluded_by:\n",
        "            alert: >-\n"
        "              A failure mode is how the argument breaks; `sound` says\n"
        "              it does not.\n"
        "            excluded_by:\n", 1)
    errors = errors_for(tmp_path, monkeypatch, "sound", "gap", cfg=cfg)
    hit = [e for e in errors if "excludes `failure`" in e]
    assert hit, errors
    assert "A failure mode is how the argument breaks" in hit[0]


def test_one_group_s_alert_does_not_leak_onto_another_s_finding(
        tmp_path, monkeypatch):
    """The alert rides its own group. `strength` carrying one says nothing
    about a `failure` violation."""
    errors = errors_for(tmp_path, monkeypatch, "sound", "gap", cfg=ALERTED)
    hit = [e for e in errors if "excludes `failure`" in e]
    assert hit and "\u21b3" not in hit[0], hit


def test_a_group_without_an_alert_is_unchanged(tmp_path, monkeypatch):
    errors = errors_for(tmp_path, monkeypatch, "gap")
    assert len(errors) == 1 and "\u21b3" not in errors[0]
