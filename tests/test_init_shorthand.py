"""`--schemes` / `--journals`: the defaults plus a little, without the boilerplate.

The conventional scheme table is four lines and three of them follow from the
prefix, which makes them the first thing a new project types and the part with
no decision in it. The shorthand is an argument rather than a stored format:
what lands in `luria.toml` is the ordinary explicit table, so nothing reads the
shorthand back and a reader of the config sees what every other project sees.
"""

import pytest

from luria import config, init


def scaffold(root, **kw):
    init.write(root, **kw)
    config.reset()
    return config.load(root)


# --- what it writes ------------------------------------------------------

def test_a_bare_prefix_gets_the_conventional_paths(tmp_path):
    cfg = scaffold(tmp_path, schemes="RFC")
    rfc = cfg.schemes["RFC"]
    assert rfc.dir == tmp_path / "record" / "rfcs.d"
    assert rfc.output == tmp_path / "docs" / "rfcs"
    assert rfc.render == "index"


def test_a_document_scheme_outputs_one_page(tmp_path):
    cfg = scaffold(tmp_path, schemes="SPEC:document")
    spec = cfg.schemes["SPEC"]
    assert spec.render == "document"
    assert spec.output == tmp_path / "docs" / "specs.md"


def test_the_shipped_schemes_survive(tmp_path):
    """"Mostly the defaults" has to mean additive. A declared family replaces
    the shipped one whole (ADR-047), so the template's own tables staying in
    the file is what keeps ADR and DP alive alongside the new one."""
    cfg = scaffold(tmp_path, schemes="RFC")
    assert set(cfg.schemes) == {"ADR", "DP", "RFC"}


def test_several_at_once(tmp_path):
    cfg = scaffold(tmp_path, schemes="RFC,SPEC:document",
                   journals="incidents:day")
    assert set(cfg.schemes) == {"ADR", "DP", "RFC", "SPEC"}
    assert cfg.journals["incidents"].granularity == "day"
    assert cfg.journals["incidents"].dir == tmp_path / "record" / "incidents.d"
    assert set(cfg.journals) == {"devlog", "incidents"}, "the devlog survives"


def test_a_journal_defaults_to_monthly(tmp_path):
    cfg = scaffold(tmp_path, journals="meetings")
    assert cfg.journals["meetings"].granularity == "month"
    assert cfg.journals["meetings"].title == "Meetings"


def test_a_plural_prefix_is_not_doubled(tmp_path):
    cfg = scaffold(tmp_path, schemes="NOTES")
    assert cfg.schemes["NOTES"].dir == tmp_path / "record" / "notes.d"


def test_the_prefix_is_upcased(tmp_path):
    cfg = scaffold(tmp_path, schemes="rfc")
    assert "RFC" in cfg.schemes


# --- the scaffold it produces is a working record ------------------------

def test_the_new_scheme_is_scaffolded_like_any_other(tmp_path):
    scaffold(tmp_path, schemes="RFC")
    assert (tmp_path / "record" / "rfcs.d" / "_template.md").exists()
    assert (tmp_path / "record" / "rfcs.d" / "README.stub").exists()


def test_the_config_it_writes_is_ordinary_toml(tmp_path):
    """No shorthand survives into the file — the whole design. A reader of
    this config sees what every other project's config looks like."""
    scaffold(tmp_path, schemes="RFC:document")
    text = (tmp_path / "luria.toml").read_text()
    assert "[luria.schemes.RFC]" in text
    assert 'render = "document"' in text
    assert "--schemes" not in text


# --- refusals ------------------------------------------------------------

def test_an_unknown_render_names_the_vocabulary(tmp_path):
    with pytest.raises(SystemExit, match="index, document"):
        init.plan(tmp_path, schemes="RFC:pamphlet")


def test_an_unknown_granularity_names_the_vocabulary(tmp_path):
    with pytest.raises(SystemExit, match="year, month, day"):
        init.plan(tmp_path, journals="incidents:fortnight")


def test_redeclaring_a_shipped_scheme_is_refused(tmp_path):
    """Silently merging would be worse: the template's ADR table carries the
    decision doctrine, and a second one would either duplicate or shadow it."""
    with pytest.raises(SystemExit, match="already declares ADR"):
        init.plan(tmp_path, schemes="ADR")


def test_shorthand_against_an_existing_config_is_refused(tmp_path):
    """The shorthand extends the shipped template. Where a config already
    exists the shape is somebody's decision, and appending to it from a flag
    would edit a file the project owns."""
    (tmp_path / "luria.toml").write_text('[luria]\nissue_url = ""\n')
    with pytest.raises(SystemExit, match="already exists"):
        init.plan(tmp_path, schemes="RFC")


def test_an_empty_entry_is_ignored_not_guessed_at(tmp_path):
    cfg = scaffold(tmp_path, schemes="RFC,")
    assert set(cfg.schemes) == {"ADR", "DP", "RFC"}
