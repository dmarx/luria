# tests/test_yaml_edit.py
"""Editing a config without destroying it.

Three commands rewrite a file a person wrote. Both obvious ways of doing that
are wrong in a way nothing reports: `OmegaConf.merge` composes correctly and
drops every comment, and line surgery keeps the comments and puts the block in
the wrong mapping — because YAML nests by indentation, so an indented block
appended to a document joins whichever top-level key happens to be last.

These are tests for the failure modes, not for the API: each one is a shape
the old line-editing produced and a parser cannot.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from luria import yaml_edit

CONFIG = """\
# what this record is
vocabularies:
  statuses:
    Active:
      blurb: in force   # the one that must exist
schemes:
  # ADR — decisions.
  ADR:
    dir: record/decisions.d
remotes:
  ADR:
    url: https://example.test/adr
journals:
  devlog:
    dir: record/devlog.d
"""


def _loaded(text: str) -> dict:
    return yaml.safe_load(text)


def test_a_block_lands_in_the_mapping_it_was_addressed_to():
    # The bug: appended after `journals:`, an indented RFC block becomes a
    # journal, and every reader agrees it is one.
    data = yaml_edit.load(CONFIG)
    yaml_edit.set_block(yaml_edit.ensure(data, ("schemes",)), "RFC",
                        {"dir": "record/rfcs.d"})
    out = _loaded(yaml_edit.dump(data))
    assert "RFC" in out["schemes"]
    assert "RFC" not in out["journals"]


def test_an_edit_keeps_the_comments_the_file_came_with():
    data = yaml_edit.load(CONFIG)
    yaml_edit.merge_into(data, {"output": "docs/decisions"}, ("schemes", "ADR"))
    out = yaml_edit.dump(data)
    assert "# what this record is" in out
    assert "# ADR — decisions." in out
    assert "# the one that must exist" in out


def test_a_new_block_carries_its_own_comment_above_it():
    data = yaml_edit.load(CONFIG)
    yaml_edit.set_block(yaml_edit.ensure(data, ("schemes",)), "RFC",
                        {"dir": "record/rfcs.d"}, before="RFC — proposals.")
    out = yaml_edit.dump(data)
    assert "  # RFC — proposals.\n  RFC:\n" in out


def test_merging_a_family_keeps_the_families_already_there():
    # Assignment rather than a deep merge would drop ADR, silently and whole.
    data = yaml_edit.load(CONFIG)
    yaml_edit.merge_into(data, {"schemes": {"RFC": {"dir": "record/rfcs.d"}}})
    out = _loaded(yaml_edit.dump(data))
    assert set(out["schemes"]) == {"ADR", "RFC"}


def test_a_rename_reaches_only_the_mapping_it_names():
    # `ADR` is a scheme and a remote here. A text sweep cannot tell them
    # apart; that is the whole reason this goes through a parser.
    data = yaml_edit.load(CONFIG)
    assert yaml_edit.rename_key(data, ("schemes",), "ADR", "DEC")
    out = _loaded(yaml_edit.dump(data))
    assert set(out["schemes"]) == {"DEC"}
    assert set(out["remotes"]) == {"ADR"}


def test_a_renamed_key_stays_where_its_author_put_it():
    data = yaml_edit.load(CONFIG)
    yaml_edit.rename_key(data, ("schemes",), "ADR", "DEC")
    out = yaml_edit.dump(data)
    assert "  # ADR — decisions.\n  DEC:\n" in out
    assert out.index("vocabularies:") < out.index("schemes:") < out.index("remotes:")


def test_renaming_what_is_not_there_changes_nothing():
    data = yaml_edit.load(CONFIG)
    assert not yaml_edit.rename_key(data, ("schemes",), "RFC", "DEC")
    assert not yaml_edit.rename_key(data, ("nowhere",), "ADR", "DEC")
    # Refuses to collide rather than overwriting the key it would land on.
    assert not yaml_edit.rename_key(data, ("schemes",), "ADR", "ADR")


def test_at_reports_absence_rather_than_inventing_it():
    data = yaml_edit.load(CONFIG)
    assert yaml_edit.at(data, ("schemes", "ADR"))["dir"] == "record/decisions.d"
    assert yaml_edit.at(data, ("schemes", "RFC")) is None
    assert "RFC" not in _loaded(yaml_edit.dump(data))["schemes"]


def test_span_is_the_lines_the_block_occupies():
    data = yaml_edit.load(CONFIG)
    lines = CONFIG.splitlines()
    start, stop = yaml_edit.span(data, ("schemes", "ADR"))
    assert lines[start].strip() == "ADR:"
    assert lines[stop].strip() == "remotes:"
    # The last entry in the document runs to the end.
    assert yaml_edit.span(data, ("journals", "devlog"))[1] is None
    assert yaml_edit.span(data, ("schemes", "RFC")) is None


def test_a_regex_survives_the_round_trip():
    # The `uid` patterns are the thing a re-encode breaks, and the reason
    # every emitter in this project is a writer that knows its own rules.
    text = 'remotes:\n  ARXIV:\n    uid: (\\d{4})[.:](\\d{4,5})\n'
    out = _loaded(yaml_edit.dump(yaml_edit.load(text)))
    assert out["remotes"]["ARXIV"]["uid"] == "(\\d{4})[.:](\\d{4,5})"


def test_the_shipped_template_is_already_in_the_shape_this_emits():
    # Otherwise the first one-key edit to any config reflows the whole file,
    # and a one-line change reads as a rewrite.
    text = (Path(__file__).resolve().parents[1] / "template"
            / "luria.yaml").read_text(encoding="utf-8")
    assert yaml_edit.dump(yaml_edit.load(text)) == text
