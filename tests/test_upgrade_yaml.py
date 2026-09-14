# tests/test_upgrade_yaml.py
"""`luria upgrade yaml` — the one way across the TOML boundary.

The new version does not read TOML at all, so a record that has not crossed
cannot be linted, indexed or repaired until it does. That makes this upgrade
the only thing standing between an existing project and a version bump, and
the reason it lives in `upgrade` rather than beside it: an upgrade repairs the
config the new version refuses to load, which is exactly this case.

What it has to get right, and what a fixture would not have caught: a regex in
a `uid` does not survive TOML -> YAML by copying bytes.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from luria import config, upgrade

TOML = '''
[luria]
issue_url = "https://example.test/issues/{n}"

[luria.remotes.ARXIV]
uid = "(\\\\d{4})[.:](\\\\d{4,5})"
url = "https://arxiv.org/abs/{1}.{2}"
title_re = "<title>(.*?)</title>"

[luria.schemes.ADR]
dir = "record/decisions.d"
output = "docs/decisions"

[luria.schemes.DP]
dir = "record/principles.d"
output = "docs/principles"
'''

WORDS = ("Active:\n  blurb: in force\nSuperseded:\n  blurb: replaced\n")


def _record(root: Path, *, shared: bool = True) -> None:
    (root / "record" / "decisions.d").mkdir(parents=True)
    (root / "record" / "principles.d").mkdir(parents=True)
    (root / "luria.toml").write_text(TOML)
    (root / "record" / "decisions.d" / "statuses.yaml").write_text(WORDS)
    (root / "record" / "principles.d" / "statuses.yaml").write_text(
        WORDS if shared else WORDS.replace("in force", "current"))


# ── the crossing ──────────────────────────────────────────────────────────

def test_it_writes_the_yaml_config(tmp_path, monkeypatch):
    _record(tmp_path)
    upgrade.run("yaml", root=str(tmp_path))
    assert (tmp_path / "luria.yaml").exists()
    loaded = yaml.safe_load((tmp_path / "luria.yaml").read_text())
    assert loaded["schemes"]["ADR"]["dir"] == "record/decisions.d"


def test_a_regex_survives_the_format_change(tmp_path, monkeypatch):
    """The hazard the whole converter exists for. TOML and YAML escape
    differently, so the bytes cannot simply move — and a `uid` that stops
    matching fails at reference-resolution time, a long way from here."""
    _record(tmp_path)
    upgrade.run("yaml", root=str(tmp_path))
    loaded = yaml.safe_load((tmp_path / "luria.yaml").read_text())
    uid = loaded["remotes"]["ARXIV"]["uid"]
    assert uid == r"(\d{4})[.:](\d{4,5})"
    assert re.fullmatch(uid, "2403.05530"), "still matches a real arXiv id"


def test_the_config_it_writes_actually_loads(tmp_path, monkeypatch):
    """End to end rather than by inspection: the point is a record that runs."""
    _record(tmp_path)
    upgrade.run("yaml", root=str(tmp_path))
    (tmp_path / "luria.toml").unlink()
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    cfg = config.current()
    assert set(cfg.schemes) == {"ADR", "DP"}
    assert cfg.remotes["ARXIV"].uid == r"(\d{4})[.:](\d{4,5})"
    config.reset()


# ── the duplication it is there to collapse ──────────────────────────────

def test_two_schemes_holding_the_same_words_end_up_naming_one_vocabulary(
        tmp_path, monkeypatch):
    """The defect that motivated the boundary: a vocabulary two schemes share
    had to be two files, and in the corpus that prompted this, ten of thirteen
    entries had drifted apart.

    inactive-ok: ADR-tmp8hp25 — Proposed, named as the decision this upgrade
    carries a record across."""
    _record(tmp_path, shared=True)
    upgrade.run("yaml", root=str(tmp_path))
    loaded = yaml.safe_load((tmp_path / "luria.yaml").read_text())
    assert len(loaded["vocabularies"]) == 1
    assert (loaded["schemes"]["ADR"]["fields"]["status"]["vocabulary"]
            == loaded["schemes"]["DP"]["fields"]["status"]["vocabulary"])


def test_words_that_differ_stay_two_vocabularies(tmp_path, monkeypatch):
    """It collapses copies, never opinions: two schemes whose words disagree
    are two vocabularies, and merging them would be the converter deciding
    something the record never said."""
    _record(tmp_path, shared=False)
    upgrade.run("yaml", root=str(tmp_path))
    loaded = yaml.safe_load((tmp_path / "luria.yaml").read_text())
    assert len(loaded["vocabularies"]) == 2
    assert (loaded["schemes"]["ADR"]["fields"]["status"]["vocabulary"]
            != loaded["schemes"]["DP"]["fields"]["status"]["vocabulary"])


def test_a_folded_vocabulary_is_wired_to_the_status_field(tmp_path,
                                                          monkeypatch):
    """The TOML fixture declares no `fields.status` — and neither did the
    records this converter exists for, because the declaration is #181's
    second half and they predate it.

    `schemes.X.statuses` does not exist on the far side of the boundary, so
    a `statuses.yaml` folded into the central table has to reach the field
    that reads it. Carrying the words across and leaving nothing pointing at
    them would be a conversion that loses the vocabulary while reporting
    success."""
    _record(tmp_path)
    upgrade.run("yaml", root=str(tmp_path))
    loaded = yaml.safe_load((tmp_path / "luria.yaml").read_text())
    named = loaded["schemes"]["ADR"]["fields"]["status"]["vocabulary"]
    assert loaded["vocabularies"][named]["Active"]["blurb"] == "in force"
    assert "statuses" not in loaded["schemes"]["ADR"]


# ── what it will not do ──────────────────────────────────────────────────

def test_it_leaves_the_toml_and_the_vocabulary_files_alone(tmp_path):
    """Deleting what you just converted, before anyone has read the result,
    is not a migration anybody should trust — it prints the `git rm` instead."""
    _record(tmp_path)
    upgrade.run("yaml", root=str(tmp_path))
    assert (tmp_path / "luria.toml").exists()
    assert (tmp_path / "record" / "decisions.d" / "statuses.yaml").exists()


def test_dry_run_writes_nothing(tmp_path):
    _record(tmp_path)
    upgrade.run("yaml", dry_run=True, root=str(tmp_path))
    assert not (tmp_path / "luria.yaml").exists()


def test_a_record_already_across_says_so(tmp_path, capsys):
    (tmp_path / "luria.yaml").write_text("issue_url: ''\n")
    upgrade.run("yaml", root=str(tmp_path))
    assert "already across" in capsys.readouterr().out


def test_another_upgrade_refuses_until_this_one_has_run(tmp_path):
    """`statuses` reads the config by its new name, so on a record still on
    TOML it would report "nothing to upgrade" — true, and useless."""
    import pytest
    _record(tmp_path)
    with pytest.raises(SystemExit, match="upgrade yaml"):
        upgrade.run("statuses", root=str(tmp_path))


def test_it_is_listed_with_what_it_waits_on(capsys):
    upgrade.run()
    out = capsys.readouterr().out
    assert "luria upgrade yaml" in out and "remove when" in out
