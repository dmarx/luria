# tests/test_repair_config.py
"""Every `luria repair` flag can also be set in `luria.yaml`, under `repair:`.

A flag only on the command line is a flag the CI repair never passes, so a
record that wants it everywhere would have to edit a workflow. The config
holds the record's standing choice, and the command line overrides it for
one run.
"""
import inspect

import pytest

from _config import merged

from luria import config, repair


def test_every_repair_flag_has_a_config_key():
    """The guard that keeps the rule true for the next flag too."""
    flags = set(inspect.signature(repair.run).parameters)
    assert flags == set(config.DEFAULTS["repair"])
    assert set(inspect.signature(repair.apply).parameters) == flags


def test_every_repair_flag_defaults_off():
    assert all(v is False for v in config.DEFAULTS["repair"].values())


def test_the_config_reads_the_table(project):
    (project / "luria.yaml").write_text(merged(
        (project / "luria.yaml").read_text(), {"repair": {"prune_stale": True}}))
    config.reset()
    assert config.current().repair == {"prune_stale": True}


def test_an_unknown_key_is_refused(project):
    (project / "luria.yaml").write_text(merged(
        (project / "luria.yaml").read_text(), {"repair": {"prune": True}}))
    config.reset()
    with pytest.raises(ValueError, match="repair.*prune"):
        config.current()


def test_a_value_that_is_not_true_or_false_is_refused(project):
    (project / "luria.yaml").write_text(merged(
        (project / "luria.yaml").read_text(),
        {"repair": {"prune_stale": "yes please"}}))
    config.reset()
    with pytest.raises(ValueError, match="prune_stale"):
        config.current()
