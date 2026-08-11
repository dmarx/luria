"""The configuration reference is derived from the schema, not transcribed.

The point of every test here is the same property, approached from different
sides: **a key that exists in `luria.toml`'s schema is a row in the reference,
whether or not anyone remembered to describe it.** A page that merely *looked*
right today would be worth nothing — a hand-written one looks right today too,
and that is exactly the failure this module exists to prevent (DP-3).
"""
from dataclasses import make_dataclass

import pytest

from luria import config_doc
from luria.config import Fragment, Journal, Remote, RemoteScheme, Scheme, Site, current


ALL_SECTIONS = [Scheme, Fragment, Journal, Remote, RemoteScheme, Site]


def test_renders_a_page_with_every_section():
    text = config_doc.render()
    assert text.startswith("# Configuration")
    for _, cls, _ in config_doc.SECTIONS:
        assert cls in ALL_SECTIONS


@pytest.mark.parametrize("cls", ALL_SECTIONS)
def test_every_public_field_of_every_config_dataclass_has_a_row(cls):
    """The guarantee, stated once per schema class.

    Not "the fields I listed appear" — *every* field, read from the class at
    render time. Add one to `Site` and this test starts covering it with no
    edit here, which is the same mechanism that puts it on the page."""
    text = config_doc.render()
    for name, _, _ in config_doc.rows(cls):
        assert f"| `{name}` |" in text, f"{cls.__name__}.{name} missing"


def test_a_new_field_appears_without_touching_the_renderer():
    """The load-bearing claim, fired directly.

    `rows()` reads `dataclasses.fields()`, so a class it has never seen
    renders anyway. If this ever fails, the module has grown a hand-maintained
    list and the whole design is void."""
    Invented = make_dataclass("Invented", [("prefix", str), ("novel_key", str, "x")])
    names = [name for name, _, _ in config_doc.rows(Invented)]
    assert names == ["prefix", "novel_key"]
    assert "| `novel_key` |" in config_doc.table(Invented)


def test_private_fields_are_not_documented():
    """`_root` and `_raw` are plumbing, not keys anyone writes."""
    assert "_raw" not in config_doc.render()
    assert "_root" not in config_doc.render()


def test_union_types_do_not_break_the_table():
    """`Path | None` carries markdown's own column separator.

    Unescaped, the row silently becomes four columns and every row under it
    shifts — the kind of break that renders as a slightly wrong table rather
    than an error."""
    row = [r for r in config_doc.rows(Scheme) if r[0] == "output"][0]
    assert "|" in row[1], "precondition: output's type is a union"
    assert r"Path \| None" in config_doc.table(Scheme)


def test_keys_luria_fills_itself_are_not_labelled_required():
    """A prefix comes from the table's name; a site title derives from
    `issue_url`. Calling either "required" sends a reader looking for a key
    to write that does not exist."""
    scheme = dict((name, default) for name, _, default in config_doc.rows(Scheme))
    assert scheme["prefix"] == "*the table's own name*"
    assert scheme["dir"] == "*required*"

    site = dict((name, default) for name, _, default in config_doc.rows(Site))
    assert site["title"] == "*derived from `issue_url`*"


def test_defaults_are_the_schema_not_this_repos_config():
    """`output` is unset for a scheme you add, whatever this repo sets for its
    own ADRs. Reading the shipped `luria.toml` here would document a default
    that does not exist."""
    scheme = dict((name, default) for name, _, default in config_doc.rows(Scheme))
    assert scheme["output"] == "*unset*"
    assert current().schemes["ADR"].output is not None, "precondition"


def test_indented_examples_become_fenced_blocks():
    assert config_doc.fence("Prose.\n\n    [luria]\n    a = 1\n") == (
        "Prose.\n\n```toml\n[luria]\na = 1\n```\n")


def test_page_is_registered_as_generated():
    """Which is what keeps the bare-reference lint off a page made of example
    codes, and keeps `luria link --fix` from rewriting them."""
    cfg = current()
    assert cfg.is_generated(cfg.config_doc)
    assert cfg.config_doc not in __import__(
        "luria.doc_refs", fromlist=["doc_files"]).doc_files()


def test_renders_into_the_index_alongside_every_other_view():
    from luria import adr_index
    assert current().config_doc in adr_index.outputs()


def test_outputs_can_be_redirected(tmp_path):
    (path,) = config_doc.outputs(tmp_path)
    assert path == tmp_path / "configuration.md"


def test_render_is_deterministic():
    """A committed view checked for staleness must be a pure function of the
    schema — nothing clock-dependent, or it goes stale at midnight."""
    assert config_doc.render() == config_doc.render()


def test_states_what_is_not_configurable():
    """A reference that lists only dials reads as though everything is one."""
    text = config_doc.render()
    assert "## What is not configurable" in text
    assert "LURIA_JOBS" in text and "LURIA_ROOT" in text
