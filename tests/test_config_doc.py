"""The configuration reference is derived from the schema, not transcribed.

The point of every test here is the same property, approached from different
sides: **a key that exists in `luria.yaml`'s schema is a row in the reference,
whether or not anyone remembered to describe it.** A page that merely *looked*
right today would be worth nothing — a hand-written one looks right today too,
and that is exactly the failure this module exists to prevent (DP-3).
"""
import re
from dataclasses import make_dataclass

import pytest

from luria import config as config_mod
from luria import config_doc
from luria.config import Fragment, Journal, Remote, RemoteScheme, Scheme, Site, current


#: Read off the module, not listed here — the same reason the rows are.
ALL_SECTIONS = config_doc.tables()


def test_renders_a_page_with_every_section():
    text = config_doc.render()
    assert text.startswith("# Configuration")
    for title, _, _ in config_doc.SECTIONS:
        assert f"\n## {title}\n" in text


@pytest.mark.parametrize("cls", ALL_SECTIONS, ids=lambda c: c.__name__)
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
    own ADRs. Reading the shipped `luria.yaml` here would document a default
    that does not exist."""
    scheme = dict((name, default) for name, _, default in config_doc.rows(Scheme))
    assert scheme["output"] == "*unset*"
    assert current().schemes["ADR"].output is not None, "precondition"


def test_indented_examples_become_fenced_blocks():
    assert config_doc.fence("Prose.\n\n    luria:\n      a: 1\n") == (
        "Prose.\n\n```yaml\nluria:\n  a: 1\n```\n")


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


# --- Where the reference renders (ADR-059) ---------------------------------
#
# The page is generated so it cannot drift from `config.py`. That argument
# only holds where `config.py` is a file the reader can open, so the page
# renders where its source lives and nowhere else. Everything below is that
# one rule, checked from both sides.

def test_this_repo_owns_the_schema():
    """The positive case has to be asserted somewhere, or the gate could be
    stuck closed and every other test here would still pass."""
    assert current().owns_schema


def test_an_adopting_project_does_not_own_the_schema(project):
    """A project that installed the package has no `luria/config.py` of its
    own, so the reference would be a vendored copy of somebody else's file —
    already a release out of date, with nothing in their repository
    responsible for it."""
    assert not current().owns_schema


def test_the_reference_is_not_a_view_in_an_adopting_project(project):
    from luria import adr_index
    assert current().config_doc not in adr_index.outputs()


def test_the_record_description_is_a_view_in_both(project):
    """The other half of the split: the page that *is* about their project
    renders everywhere, including here."""
    from luria import adr_index
    assert current().record_doc in adr_index.outputs()


def test_retire_removes_a_reference_luria_wrote(project):
    """The upgrade path. Before ADR-059 the page rendered into every adopting
    project, so a bump leaves one behind that nothing will ever update."""
    stale = current().config_doc
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text(config_doc.render())
    assert config_doc.retire() == [stale]
    assert not stale.exists()


def test_retire_leaves_a_page_the_project_wrote_itself(project):
    """Deleting a file in somebody else's repository wants a better reason
    than "we stopped writing it". The generator's marker is the proof, and
    prose that happens to share the name is not ours to remove."""
    theirs = current().config_doc
    theirs.parent.mkdir(parents=True, exist_ok=True)
    theirs.write_text("# Configuration\n\nHow *we* configure our deployment.\n")
    assert config_doc.retire() == []
    assert theirs.exists()


def test_retire_never_touches_the_reference_where_it_belongs():
    """Here, the page is the deliverable — a cleanup that removed it would be
    a generator deleting its own output."""
    assert config_doc.retire() == []
    assert current().config_doc.exists()


# --- Coverage is derived, not transcribed (DP-3) ----------------------------
#
# `rows()` always read the schema, so no *key* could go missing. Two lists
# above it did not, and both silently rotted: `SECTIONS` decided which classes
# got a section at all, and `PLAIN` spelled out which scalar keys existed. A
# `chains` family, seven nested tables, `lint.mute` and `lint.network` were
# absent from the reference for as long as they had existed. The property the
# module claimed — the schema decides what the page holds — now covers the
# sections and the scalars too.

def test_every_table_in_the_defaults_has_a_section():
    """The gap that let `chains` go undocumented for its whole life.

    A key whose default is a dict is a table, and a table wants a section —
    whether a dataclass renders it (`schemes`, `chains`) or a scalar list
    does (`paths`, `lint`). The old test asked "is every section I listed a
    class I know?", which passes forever while the schema grows underneath
    it. This asks the question that can fail."""
    text = config_doc.render()
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    for key, value in config_mod.DEFAULTS.items():
        if not isinstance(value, dict):
            continue
        assert any(f"`{key}" in h for h in headings), f"no section for {key}"


def test_a_new_nested_table_cannot_be_silently_absent(monkeypatch):
    """Fired directly: a class the module has never heard of still renders."""
    Invented = make_dataclass("Invented", [("novel_key", str, "x")])
    Invented.__doc__ = "A table nobody described."
    monkeypatch.setattr(config_doc, "tables", lambda: [Invented])
    text = config_doc.render()
    assert "Invented" in text
    assert "| `novel_key` |" in text


def test_every_scalar_key_in_the_defaults_has_a_row():
    """`lint.mute` and `lint.network` existed for releases with no row.

    The scalar tables have no dataclass behind them, so the schema they are
    read from is `config.DEFAULTS` — the same file, the same guarantee."""
    text = config_doc.render()
    for _, subtree, _, _ in config_doc.PLAIN:
        for key in config_doc.plain_keys(subtree):
            assert f"| `{key}` |" in text, f"{subtree or 'luria'}.{key} missing"


def test_an_undescribed_scalar_key_still_gets_a_row():
    """The stamp's promise, fired. Prose is what a person supplies; the row
    is what the schema supplies, and the second must not wait on the first."""
    rendered = config_doc.plain_table(["invented"], {"invented": 7}, {})
    assert "| `invented` |" in rendered


def test_every_scalar_key_is_described():
    """The other half: a row with no prose is a reminder, not a reference.

    It renders — a reader sees the key exists — and this fails, so the
    reminder is answered in CI rather than in a reader's head."""
    undescribed = sorted(f"{subtree or 'luria'}.{key}"
                         for _, subtree, _, prose in config_doc.PLAIN
                         for key in config_doc.plain_keys(subtree)
                         if key not in prose)
    assert not undescribed, f"no prose for {undescribed}"


# --- The file is YAML ------------------------------------------------------

def test_examples_are_fenced_as_yaml():
    """`luria.yaml` replaced `luria.toml` in #257; the fence language did not
    move, so every example on the page was labelled as the format it is not."""
    text = config_doc.render()
    assert "```toml" not in text
    assert "```yaml" in text


def test_no_example_is_still_written_in_toml():
    """#286 rewrote the example configs and reached only some docstrings.

    What it left is worse than a wrong fence: a `[table.header]` became a bare
    backticked line and the body under it stayed `key = "value"`, so the page
    showed a reader YAML that is not YAML. Parsing is the check — a TOML body
    under a YAML fence is what this is looking for, not a spelling."""
    import yaml
    text = config_doc.render()
    for block in re.findall(r"```yaml\n(.*?)```", text, re.DOTALL):
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError as exc:                    # pragma: no cover
            raise AssertionError(f"not YAML:\n{block}\n{exc}") from exc
        assert isinstance(parsed, dict), \
            f"example parses as {type(parsed).__name__}, not a mapping:\n{block}"


# --- Prose that outlived what it described ---------------------------------

def test_migration_is_not_listed_as_missing():
    """`luria migrate` shipped; the reference went on saying it had not."""
    text = config_doc.render()
    assert "there is no migration command" not in text


def test_the_shape_table_names_every_family():
    """The overview table is prose, and prose about a list of tables is a
    projection of that list."""
    text = config_doc.render()
    for family in config_doc.FAMILIES:
        assert f"| `{family}" in text, f"{family} missing from the shape table"
