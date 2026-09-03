"""The record description is derived from the loaded config, not transcribed.

Every test here is the same property from a different side: **a family a
project declares is a row on its page, whether or not anyone remembered to
describe it.** A page that merely *looks* right against this repo's own
config would be worth nothing — a hand-written one looks right too, and that
is the failure this module exists to prevent (DP-3). So the fixtures declare
shapes Luria does not ship: an `RFC` scheme, two journals, a renamed fragment
directory. Anything hardcoded to `ADR`/`devlog` fails them.
"""
import pytest

from luria import adr_index, config, record_doc
from luria.config import current


@pytest.fixture
def unusual(tmp_path, monkeypatch):
    """A project whose record shares no vocabulary with Luria's own."""
    (tmp_path / "spec.d").mkdir()
    (tmp_path / "notes.d").mkdir()
    (tmp_path / "incidents.d").mkdir()
    (tmp_path / "news.d").mkdir()
    (tmp_path / "luria.toml").write_text("""
[luria]
issue_url = "https://example.test/issues/{n}"
stale_days = 14

[luria.paths]
docs = "documentation"

[luria.schemes.RFC]
dir = "spec.d"
output = "documentation/specs"
active = "Ratified"

[luria.fragments."news.d"]
file = "NEWS.md"

[luria.journals.notes]
dir = "notes.d"
output = "documentation/notes"
granularity = "year"
title = "Field notes"

[luria.journals.incidents]
dir = "incidents.d"
output = "documentation/incidents"
title = "Incidents"

[luria.remotes.LU]
name = "luria"
repo = "dmarx/luria"
dir = "record/decisions.d"
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    yield tmp_path
    config.reset()


def test_names_every_scheme_the_project_declared(unusual):
    section = record_doc.render().split("## Referable")[1].split("\n## ")[0]
    assert "`RFC-001`" in section and "`spec.d/`" in section
    assert "`Ratified`" in section
    # The shipped default is *absent*, because a declared family replaces it
    # whole (ADR-047). A page that named ADR here would be describing Luria,
    # not this project. Scoped to the section because the remote below is
    # legitimately cited as `LU-ADR-001` — somebody else's ADR, which is the
    # whole point of a prefix.
    assert "ADR-001" not in section


def test_names_every_journal_including_the_second(unusual):
    text = record_doc.render()
    for name, title, grain in [("notes", "Field notes", "year"),
                               ("incidents", "Incidents", "month")]:
        assert f"`{name}`" in text and title in text
        assert grain in text


def test_names_the_fragment_directory_and_its_target(unusual):
    text = record_doc.render()
    assert "`news.d/`" in text and "`NEWS.md`" in text
    assert "changelog.d" not in text


def test_names_each_remote_by_the_prefix_a_citation_carries(unusual):
    text = record_doc.render()
    assert "`LU-" in text and "dmarx/luria" in text


def test_filing_table_offers_exactly_what_the_cli_dispatches_on(unusual):
    """The commands are the CLI's own mapping, so the table cannot advertise
    a kind `luria new` would reject — the drift this page exists to not have."""
    from luria.new import kinds
    text = record_doc.render()
    for kind in kinds():
        assert f"--kind {kind} " in text, f"{kind} missing from the table"
    assert "--kind adr " not in text


def test_a_new_family_appears_without_touching_the_renderer(unusual):
    """The load-bearing claim, fired directly rather than inferred."""
    before = record_doc.render()
    assert "POLICY-001" not in before
    (unusual / "policy.d").mkdir()
    (unusual / "luria.toml").write_text(
        (unusual / "luria.toml").read_text()
        + '\n[luria.schemes.POLICY]\ndir = "policy.d"\n')
    config.reset()
    assert "`POLICY-001`" in record_doc.render()


def test_settings_table_shows_what_changed_and_not_what_did_not(unusual):
    text = record_doc.render().split("## Settings")[1]
    assert "`stale_days`" in text and "`14`" in text and "`90`" in text
    # `fail_on` is untouched, so it is not a decision this project made.
    assert "fail_on" not in text


def test_a_nested_table_is_one_row_not_one_row_per_colour(project):
    """A theme is one choice with two dozen colours in it. Flattened all the
    way it buries every other row, which is how a diff stops being readable."""
    (project / "luria.toml").write_text(
        (project / "luria.toml").read_text()
        + '\n[luria.site.theme.light]\n'
        + "".join(f'c{i} = "#00000{i}"\n' for i in range(9)))
    config.reset()
    text = record_doc.render()
    assert "`site.theme`" in text
    assert "c0" not in text and "#000000" not in text


def test_family_tables_stay_out_of_the_settings_diff(unusual):
    """They are the sections above, and a declared family is replaced whole
    rather than merged — "differs from the default" is not a question that
    means anything about one."""
    text = record_doc.render().split("## Settings")[1]
    for family in record_doc.FAMILIES:
        assert f"`{family}" not in text


def test_the_page_is_the_same_after_the_generator_has_run(unusual):
    """Idempotence, and it has bitten once: a first draft asked the
    filesystem whether each path was a directory, so a directory `luria index`
    created on its own run flipped a trailing slash — the page rendered, was
    written, and then compared unequal to itself. `luria index && luria lint`
    on a fresh `luria init` is where it surfaced."""
    first = record_doc.render()
    adr_index.run()
    assert record_doc.render() == first
    assert (unusual / "documentation" / "record.md").read_text() == first


def test_the_page_lands_where_the_docs_surface_is(unusual):
    assert current().record_doc == unusual / "documentation" / "record.md"


def test_the_fixer_leaves_it_alone(unusual):
    """It is made of example codes — `RFC-001` names nothing. Rewriting them
    into links would report the page to itself on the next lint."""
    assert current().is_generated(current().record_doc)


# --- what an entry must carry (#141) --------------------------------------

def test_the_page_says_when_no_scheme_demands_more_than_the_standard_fields(unusual):
    section = record_doc.render().split("## What an entry must carry")[1].split("\n## ")[0]
    assert "Nothing beyond the standard fields" in section
    assert "requires" in section and "references" in section


def test_the_page_lists_each_obligation_with_where_it_was_declared(unusual):
    (unusual / "luria.toml").write_text(
        (unusual / "luria.toml").read_text()
        + '\n[luria.schemes.RFC.tag_groups.track]\n'
          'tags = ["fast", "slow"]\nrequire = "exactly-one"\n')
    config.reset()
    text = (unusual / "luria.toml").read_text().replace(
        'active = "Ratified"', 'active = "Ratified"\nrequires = ["champion"]')
    (unusual / "luria.toml").write_text(text)
    config.reset()
    section = record_doc.render().split("## What an entry must carry")[1].split("\n## ")[0]
    assert "`RFC`" in section
    assert "`champion`" in section and "schemes.RFC.requires" in section
    assert "`track`" in section and "exactly one of `fast`, `slow`" in section
    assert "Nothing beyond" not in section
