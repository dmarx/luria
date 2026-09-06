"""`luria new [kind]`: one scaffold for every entry kind (ADR-036, #42).

The contract under test: identity fields a machine can compute are computed
(number, timestamp, date, filename), everything else stays the template's
placeholder, and the path comes back for an editor to take over. Kinds are
derived from config, never hardcoded.
"""
import datetime as dt
from pathlib import Path

import pytest

from luria import new as new_mod
from luria.config import current


def test_the_default_kind_is_the_journal(project):
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n'
        '[luria.journals.devlog]\ndir = "devlog.d"\noutput = "docs/devlog"\n')
    from luria import config
    config.reset()

    path = new_mod.new_entry(None, {}, None)
    assert path.suffix == ".md" and "devlog.d" in str(path)
    text = path.read_text()
    assert "created: '" in text
    assert "title:" in text, "a placeholder title, for the lint to accept"


def test_a_scheme_gets_the_next_free_number(project):
    from tests._scheme import decision
    decision(project, 1, "Active")
    path = new_mod.new_entry("adr", {}, None)
    assert path.name == "ADR-002.md"
    text = path.read_text()
    assert f"date: '{dt.date.today().isoformat()}'" in text


def test_the_template_is_copied_with_the_code_filled_in(project):
    scheme = current().schemes["ADR"]
    scheme.dir.mkdir(parents=True, exist_ok=True)
    (scheme.dir / "_template.md").write_text(
        "---\nstatus: Proposed\ntitle: 'A placeholder'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# ADR-NNN: A placeholder\n\nBody.\n")
    path = new_mod.new_entry("adr", {}, None)
    text = path.read_text()
    assert "# ADR-001: A placeholder" in text
    assert "ADR-NNN" not in text
    assert "date: '2026-01-01'" not in text, "the date is stamped, not copied"


def test_named_fields_are_optional_but_honoured(project):
    scheme = current().schemes["ADR"]
    scheme.dir.mkdir(parents=True, exist_ok=True)
    (scheme.dir / "_template.md").write_text(
        "---\nstatus: Proposed\ntitle: 'A placeholder'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# ADR-NNN: A placeholder\n\nBody.\n")
    path = new_mod.new_entry("adr", {"title": "Chosen on the command line",
                                     "status": "Active"}, None)
    text = path.read_text()
    assert "title: 'Chosen on the command line'" in text
    assert "# ADR-001: Chosen on the command line" in text, \
        "the heading follows the title, or the lint fails on arrival"
    assert "status: 'Active'" in text


def test_a_fragment_takes_the_given_name(project):
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n'
        '[luria.fragments."changelog.d"]\nfile = "CHANGELOG.md"\n')
    from luria import config
    config.reset()
    (project / "changelog.d").mkdir()
    (project / "changelog.d" / "_template.md").write_text("### Changed\n\n- \n")

    path = new_mod.new_entry("changelog", {}, "my-name")
    assert path == project / "changelog.d" / "my-name.md"
    assert path.read_text() == "### Changed\n\n- \n"
    assert new_mod.new_entry("changelog", {}, "my-name") == path, \
        "an explicit name is an address — asking again reopens, not duplicates"


def test_an_unnamed_fragment_is_stamped_like_a_journal_entry(project):
    """The default identity is the filing moment (ADR-036 v2). It used to be
    the git branch, which collided the first time a branch was restarted
    after a squash merge and refiled: `luria new changelog` reopened the
    MERGED fragment and muddled two PRs into one batch."""
    import re
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n'
        '[luria.fragments."changelog.d"]\nfile = "CHANGELOG.md"\n')
    from luria import config
    config.reset()
    (project / "changelog.d").mkdir()

    path = new_mod.new_entry("changelog", {}, None)
    assert re.fullmatch(r"\d{8}-\d{6}\.md", path.name), path.name
    assert path.parent == project / "changelog.d", \
        "flat, not yyyy/mm/dd/ nested — the collector globs one level deep"


def test_an_unknown_kind_names_what_this_project_scaffolds(project):
    from tests._scheme import decision
    decision(project, 1, "Active")
    with pytest.raises(SystemExit) as exc:
        new_mod.new_entry("rfc", {}, None)
    assert "adr" in str(exc.value)


def test_a_comma_separated_tags_flag_survives_fire(project):
    """`luria new adr --tags record,mechanism` reaches `run` as a tuple:
    Fire reads a comma-separated argument as a Python literal. The
    scaffolder took `.split(",")` on it and crashed, so the one spelling
    the help text invites was the one that failed."""
    from luria import new
    path = new.new_entry("adr", {"tags": ("record", "mechanism")}, None)
    text = path.read_text()
    assert "tags:\n- record\n- mechanism\n" in text


# --- Reference fields as flags (#169) ---------------------------------------
#
# `new` accepted four flags and nothing else, so a tool driving the CLI could
# not set a reference field at all; and had it been able to, `_sub_line` would
# have rendered `--source LIT-1,LIT-2` as the string `'LIT-1, LIT-2'` — the
# stringified list #141 made a finding of. The scaffold has to know the shape
# the contract declares, for the same reason the template does.

def _plural_project(project, many: bool = True):
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n\n'
        '[luria.schemes.LIT]\ndir = "record/literature.d"\n\n'
        '[luria.schemes.SOTA]\ndir = "record/practices.d"\n\n'
        '[luria.schemes.SOTA.references]\n'
        f'source = {{ scheme = "LIT", required = true, many = {str(many).lower()} }}\n')
    from luria import config
    config.reset()
    scheme = current().schemes["SOTA"]
    scheme.dir.mkdir(parents=True, exist_ok=True)
    (scheme.dir / "_template.md").write_text(
        "---\nstatus: Proposed\ntitle: 'A placeholder'\ntags:\n- record\n"
        "date: '2026-01-01'\n"
        + ("source:\n- LIT-000\n" if many else "source: LIT-000\n")
        + "---\n\n# SOTA-NNN: A placeholder\n\nBody.\n")
    return scheme


def test_a_plural_reference_flag_is_written_as_a_list(project):
    _plural_project(project)
    path = new_mod.new_entry("sota", {"source": "LIT-134,LIT-140"}, None)
    text = path.read_text()
    assert "source:\n- LIT-134\n- LIT-140\n" in text, text
    assert "'LIT-134, LIT-140'" not in text


def test_one_code_for_a_plural_reference_is_still_a_list(project):
    _plural_project(project)
    text = new_mod.new_entry("sota", {"source": "LIT-134"}, None).read_text()
    assert "source:\n- LIT-134\n" in text


def test_a_scalar_reference_flag_stays_scalar(project):
    _plural_project(project, many=False)
    text = new_mod.new_entry("sota", {"source": "LIT-134"}, None).read_text()
    assert "source: 'LIT-134'" in text
    assert "\n- LIT-134" not in text


def test_a_field_absent_from_the_template_is_added_not_dropped(project):
    """`_sub_line` substitutes; a field the form does not scaffold matched
    nothing and the value vanished with the command reporting success."""
    _plural_project(project)
    scheme = current().schemes["SOTA"]
    (scheme.dir / "_template.md").write_text(
        "---\nstatus: Proposed\ntitle: 'A placeholder'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# SOTA-NNN: A placeholder\n\nBody.\n")
    text = new_mod.new_entry("sota", {"source": "LIT-134"}, None).read_text()
    assert "source:\n- LIT-134\n" in text, text


def test_an_undeclared_flag_is_refused_by_name(project):
    """Silently accepting an unknown field would write a key the scheme has
    no opinion about into every document a script files."""
    _plural_project(project)
    with pytest.raises(SystemExit) as caught:
        new_mod.run(kind="sota", sauce="LIT-134")
    assert "sauce" in str(caught.value) and "source" in str(caught.value)


def test_a_declared_flag_reaches_the_document_through_run(project, capsys):
    _plural_project(project)
    new_mod.run(kind="sota", source="LIT-134,LIT-140")
    written = (current().root / capsys.readouterr().out.strip()).read_text()
    assert "source:\n- LIT-134\n- LIT-140\n" in written



def test_an_unfilled_summary_is_dropped_not_copied_from_the_form(project):
    """The form's `summary:` explains what a summary is for. A document
    scaffolded without one used to carry that explanation as its summary,
    and two Proposed decisions reached the published index saying it. The
    key goes; the comment above it stays as the instruction."""
    from luria import config, new
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        'output = "docs/decisions"\n')
    config.reset()
    d = project / "record" / "decisions.d"
    d.mkdir(parents=True, exist_ok=True)
    (d / "_template.md").write_text(
        "---\nstatus: Proposed\ntitle: 'Title'\ntags:\n- record\n"
        "date: '2026-01-01'\n# What the index shows.\nsummary: >-\n"
        "  One-paragraph description of the decision.\n---\n\n"
        "# ADR-NNN: Title\n")
    scheme = config.current().schemes["ADR"]
    bare = new.new_scheme_doc(scheme, {"title": "Bare"}).read_text()
    assert "summary:" not in bare
    assert "# What the index shows." in bare, "the instruction survives"
    filled = new.new_scheme_doc(scheme, {"title": "Filled",
                                         "summary": "We chose it."}).read_text()
    assert "summary: >-\n  We chose it." in filled
