# tests/test_axis.py
"""`tags` is a field a scheme declares, not an axis the code assumes.

`status` stopped being special in #181 and finished stopping in
ADR-tmp8hp25. `tags` was the last one, and it held out for two stated
reasons: a vocabulary is closed by construction and `tags` is open, and
`tag_groups` constrain a subset of a field's values, which a vocabulary
cannot express. Both are now things a declaration says — `closed: false`
and `fields.<field>.groups` — so what is left of "the tag axis" is one
key naming WHICH field a scheme heads its index with.

These are tests for that: what the declaration can now say, and what the
code no longer assumes.
"""

# inactive-ok-file: ADR-tmp8hp25 — Proposed. Every mention names it as the
# decision this file implements or is written against; the citation is to the
# reasoning, not a claim the decision is settled.

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_index as builder, config, lint

BASE = """
issue_url: https://example.test/issues/{n}
vocabularies:
  topics:
    record:
      label: Record
      blurb: how the anthology stores things
  worlds:
    A: {label: The unbroken line}
    B: {label: The other one}
schemes:
  SCENE:
    dir: record/scenes.d
    output: docs/scenes
    active: Active
    render: index
%s
"""


def project(tmp_path, monkeypatch, scheme_keys: str, *, front: str = "") -> Path:
    (tmp_path / "luria.yaml").write_text(BASE % scheme_keys)
    d = tmp_path / "record" / "scenes.d"
    d.mkdir(parents=True)
    (d / "SCENE-001.md").write_text(
        "---\nstatus: Active\ntitle: 'A scene'\nversion: 1\n"
        f"{front}date: '2026-01-01'\n---\n\n# SCENE-001: A scene\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


OPEN_TAGS = """    axis: tags
    fields:
      tags:
        vocabulary: topics
        many: true
        closed: false
"""


# --- open and closed ------------------------------------------------------

def test_an_open_vocabulary_accepts_a_value_it_does_not_declare():
    """The reason `tags` could not be a vocabulary before. A project
    declares the values it has an opinion about — order, label, blurb — and
    reaching for a new one stays an edit to a document."""
    assert "closed: false" in OPEN_TAGS


def test_an_undeclared_value_on_an_open_field_is_not_a_finding(
        tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, OPEN_TAGS,
            front="tags:\n- record\n- homemade\n")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert errors == [], errors


def test_the_same_value_on_a_closed_field_is_a_finding(tmp_path, monkeypatch):
    """Closed is still the default and still checked — `closed: false` opens
    one field, not the mechanism."""
    project(tmp_path, monkeypatch,
            OPEN_TAGS.replace("        closed: false\n", ""),
            front="tags:\n- record\n- homemade\n")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("homemade" in e for e in errors), errors


# --- the axis is named, not assumed ---------------------------------------

def test_a_scheme_may_head_its_index_with_a_field_that_is_not_tags(
        tmp_path, monkeypatch):
    """The payoff. A world-bible's axis is `worlds`, and nothing in the code
    has an opinion about which word that is: the pages land under the
    field's own name, and the index groups by it."""
    root = project(tmp_path, monkeypatch, """    axis: worlds
    fields:
      worlds:
        vocabulary: worlds
        many: true
        closed: false
""", front="worlds:\n- A\n")
    scheme = config.current().schemes["SCENE"]
    assert scheme.axis == "worlds" and scheme.tags_vocab == "worlds"
    assert scheme.tag_dir == root / "docs" / "scenes" / "worlds"
    out = builder.outputs()
    assert (root / "docs/scenes/worlds/A.md") in out
    assert "The unbroken line" in out[root / "docs/scenes/README.md"]


def test_a_scheme_with_no_axis_renders_no_categories(tmp_path, monkeypatch):
    """And is not told it is missing any. A scheme that declares no taxonomy
    has none — which the old code could not express, because every scheme
    had `tags` whether it wanted one or not."""
    root = project(tmp_path, monkeypatch, "", front="tags:\n- record\n")
    assert config.current().schemes["SCENE"].axis == ""
    out = builder.outputs()
    assert not [p for p in out if "/tags/" in p.as_posix()]
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert not [e for e in errors if "tags" in e], errors


def test_an_axis_must_name_a_field_the_scheme_declares(tmp_path, monkeypatch):
    """Eagerly, like every other declaration: an axis pointing at nothing
    renders an empty categories block, and an empty one is indistinguishable
    from a correct one."""
    with pytest.raises(ValueError, match="does not declare"):
        project(tmp_path, monkeypatch, "    axis: nowhere\n")
        config.current()


# --- the keys that moved --------------------------------------------------

def test_a_scheme_level_tags_key_says_where_the_vocabulary_goes(
        tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="fields.tags.vocabulary"):
        project(tmp_path, monkeypatch, "    tags: topics\n")
        config.current()


def test_a_scheme_level_tag_groups_key_says_where_the_groups_go(
        tmp_path, monkeypatch):
    """A group constrains a subset of ONE field's values, so it is declared
    under that field — which is also what lets a scheme group two different
    fields, where `schemes.X.tag_groups` could only ever mean `tags`."""
    with pytest.raises(ValueError, match=r"fields.<field>.groups"):
        project(tmp_path, monkeypatch,
                "    tag_groups:\n      t:\n        tags: [record]\n")
        config.current()


def test_a_group_names_the_field_it_constrains(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, """    axis: worlds
    fields:
      worlds:
        vocabulary: worlds
        many: true
        groups:
          line:
            tags: [A, B]
            require: exactly-one
""", front="worlds:\n- A\n- B\n")
    group, = config.current().schemes["SCENE"].tag_groups
    assert group.field == "worlds"
    errors: list[str] = []
    lint.check_contracts(errors)
    assert any("`line` wants exactly one" in e for e in errors), errors


def test_a_group_reads_its_own_field_not_a_key_called_tags(
        tmp_path, monkeypatch):
    """The bug this shape removes: the check read `meta["tags"]` whatever
    the group was about, so a group on any other field saw nothing and
    passed every document."""
    project(tmp_path, monkeypatch, """    axis: worlds
    fields:
      worlds:
        vocabulary: worlds
        many: true
        groups:
          line:
            tags: [A, B]
            require: exactly-one
""", front="tags:\n- A\n- B\nworlds:\n- A\n")
    errors: list[str] = []
    lint.check_contracts(errors)
    assert not [e for e in errors if "`line`" in e], errors
