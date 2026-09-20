"""`luria new [kind]`: one scaffold for every entry kind (ADR-036, #42).

The contract under test: identity fields a machine can compute are computed
(number, timestamp, date, filename), everything else stays the template's
placeholder, and the path comes back for an editor to take over. Kinds are
derived from config, never hardcoded.
"""
from _config import merged
import datetime as dt
from pathlib import Path

import pytest

from luria import new as new_mod
from luria.config import current


def test_the_default_kind_is_the_journal(project):
    (project / "luria.yaml").write_text(
        """
        issue_url: ''
        journals:
          devlog:
            dir: devlog.d
            output: docs/devlog
        """)
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
    (project / "luria.yaml").write_text(
        """
        issue_url: ''
        fragments:
          changelog.d:
            file: CHANGELOG.md
        """)
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
    (project / "luria.yaml").write_text(
        """
        issue_url: ''
        fragments:
          changelog.d:
            file: CHANGELOG.md
        """)
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
    (project / "luria.yaml").write_text(
        merged("""
issue_url: https://example.test/issues/{n}
schemes:
  LIT:
    dir: record/literature.d
  SOTA:
    dir: record/practices.d
""", {"schemes": {"SOTA": {"references": {
            "source": {"scheme": "LIT", "required": True, "many": many}}}}}))
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
    (project / "luria.yaml").write_text(
        """
        issue_url: https://example.test/issues/{n}
        schemes:
          ADR:
            dir: record/decisions.d
            output: docs/decisions
        """)
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


# --- influenced_by as a flag (#301) ------------------------------------------
#
# `influenced_by:` is read by the index and by edges.py as a typed relation,
# but it is not a contract field, so `declared_fields` never offered it and
# `run` refused it by name. A tool handing over a draft — the documents it
# was drawn from are exactly this list — needs the flag on every scheme.

def test_influenced_by_is_accepted_on_a_scheme_that_declares_nothing(project, capsys):
    from tests._scheme import decision
    decision(project, 1, "Active")
    new_mod.run(kind="adr", title="Drafted", influenced_by="ADR-001,ADR-002")
    written = (current().root / capsys.readouterr().out.strip()).read_text()
    assert "influenced_by:\n- ADR-001\n- ADR-002\n" in written, written
    assert "'ADR-001, ADR-002'" not in written


def test_one_influence_is_still_a_list(project):
    """The index and edges.py iterate the field; a scalar would be read as
    a string's characters, which is the #141 finding written by the tool
    that scaffolds the document."""
    from tests._scheme import decision
    decision(project, 1, "Active")
    text = new_mod.new_entry("adr", {"influenced_by": "ADR-001"}, None).read_text()
    assert "influenced_by:\n- ADR-001\n" in text, text


def test_influenced_by_survives_fire_reading_it_as_a_tuple(project):
    from tests._scheme import decision
    decision(project, 1, "Active")
    text = new_mod.new_entry("adr", {"influenced_by": ("ADR-001", "ADR-002")}, None).read_text()
    assert "influenced_by:\n- ADR-001\n- ADR-002\n" in text, text


# --- a drafts file as input (#301) -------------------------------------------
#
# strata-g's canvas exports the entries drafted on it as a `luria-drafts`
# document: each draft carries the universal fields plus the documents it was
# drawn from as `influenced_by`, and the canvas's own bookkeeping beside
# them. `luria new --draft FILE` is the hand-over.

def _drafts_file(project, payload) -> str:
    import json
    path = project / "drafts.json"
    path.write_text(json.dumps(payload))
    return str(path)


def test_a_drafts_document_files_one_entry_per_draft(project, capsys):
    from tests._scheme import decision
    decision(project, 1, "Active")
    decision(project, 2, "Active")
    path = _drafts_file(project, {
        "format": "luria-drafts", "version": 1,
        "drafts": [
            {"id": "manual-1", "scheme": "ADR", "title": "First",
             "tags": ["record", "mechanism"], "summary": "Why.",
             "influenced_by": ["ADR-001", "ADR-002"], "unresolved": [],
             "command": "luria new adr --title 'First'"},
            {"id": "manual-2", "scheme": "ADR", "title": "Second",
             "tags": [], "summary": "", "influenced_by": ["ADR-001"],
             "unresolved": ["manual-1"], "command": ""},
        ],
    })
    new_mod.run(draft=path)
    written = [current().root / line for line in capsys.readouterr().out.split()]
    assert len(written) == 2
    first, second = (w.read_text() for w in written)
    assert "title: 'First'" in first and "tags:\n- record\n- mechanism\n" in first
    assert "influenced_by:\n- ADR-001\n- ADR-002\n" in first, first
    assert "summary: >-\n  Why." in first
    assert "title: 'Second'" in second and "influenced_by:\n- ADR-001\n" in second
    # Bookkeeping never reaches the document.
    for text in (first, second):
        assert "command" not in text and "unresolved" not in text and "manual-" not in text


def test_a_single_draft_object_files_too(project, capsys):
    from tests._scheme import decision
    decision(project, 1, "Active")
    path = _drafts_file(project, {"scheme": "ADR", "title": "Alone", "influenced_by": ["ADR-001"]})
    new_mod.run(draft=path)
    text = (current().root / capsys.readouterr().out.strip()).read_text()
    assert "title: 'Alone'" in text and "influenced_by:\n- ADR-001\n" in text


def test_a_draft_key_the_scheme_has_no_opinion_about_is_refused_by_name(project):
    from tests._scheme import decision
    decision(project, 1, "Active")
    path = _drafts_file(project, {"scheme": "ADR", "title": "T", "sauce": "LIT-1"})
    with pytest.raises(SystemExit) as caught:
        new_mod.run(draft=path)
    assert "sauce" in str(caught.value) and "influenced_by" in str(caught.value)


def test_a_draft_for_another_kind_than_the_one_asked_for_is_refused(project):
    from tests._scheme import decision
    decision(project, 1, "Active")
    path = _drafts_file(project, {"scheme": "DP", "title": "T"})
    with pytest.raises(SystemExit) as caught:
        new_mod.run(kind="adr", draft=path)
    assert "'dp'" in str(caught.value) and "'adr'" in str(caught.value)


def test_draft_and_field_flags_do_not_mix(project):
    from tests._scheme import decision
    decision(project, 1, "Active")
    path = _drafts_file(project, {"scheme": "ADR", "title": "T"})
    with pytest.raises(SystemExit) as caught:
        new_mod.run(draft=path, title="Other")
    assert "--draft" in str(caught.value)


def test_the_heading_follows_the_title_even_when_the_form_disagreed_with_itself(project):
    """A form whose `title:` and `# CODE:` heading carry different
    placeholder text scaffolded a document the lint rejected on first read:
    the heading was only rewritten when it repeated the form's `title:`.
    The heading is derived from the title, so it is rewritten by rule."""
    from luria import config
    (project / "luria.yaml").write_text(
        """
        issue_url: https://example.test/issues/{n}
        schemes:
          ADR:
            dir: record/decisions.d
            output: docs/decisions
        """)
    config.reset()
    d = project / "record" / "decisions.d"
    d.mkdir(parents=True, exist_ok=True)
    (d / "_template.md").write_text(
        "---\nstatus: Proposed\ntitle: 'A short imperative title'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# ADR-NNN: Decision, stated as the thing you did\n\nBody.\n")
    text = new_mod.new_entry("adr", {"title": "Filed by a tool"}, None).read_text()
    assert "title: 'Filed by a tool'" in text
    assert "# ADR-001: Filed by a tool" in text, text
    assert "Decision, stated as the thing you did" not in text


# ── the body ──────────────────────────────────────────────────────────────
# `--body` (and a draft's `body` key) hands over the prose: a tool that let
# someone author the document — strata-g's drop dialog — has more than
# frontmatter to file, and the alternative is a scaffold whose body is the
# template's instructions, to be replaced by hand in an editor.


def test_a_body_replaces_the_template_prose_below_the_heading(project, capsys):
    tpl = current().root / "record" / "decisions.d" / "_template.md"
    tpl.write_text("---\ntitle: 'Placeholder'\nstatus: Proposed\ntags:\n- record\n"
                   "date: '2026-01-01'\n---\n\n# ADR-NNN: Placeholder\n\n"
                   "## Context\n\nWhat was true.\n\n## Decision\n\nWhat was decided.\n")
    new_mod.run("adr", title="Bodied", body="## Context\n\nIt rained.\n\n## Decision\n\nWe stayed in.")
    text = (current().root / capsys.readouterr().out.strip()).read_text()
    assert "# ADR-001: Bodied\n\n## Context\n\nIt rained.\n\n## Decision\n\nWe stayed in.\n" in text
    assert "What was true" not in text and "Placeholder" not in text.split("---")[2]
    # The frontmatter is untouched by the body.
    assert "title: 'Bodied'" in text and "tags:\n- record" in text


def test_a_body_that_opens_with_its_own_heading_does_not_double_it(project, capsys):
    new_mod.run("adr", title="Once", body="# ADR-999: Once\n\nProse.")
    text = (current().root / capsys.readouterr().out.strip()).read_text()
    assert text.count("\n# ") == 1, text
    assert "# ADR-001: Once\n\nProse.\n" in text


def test_a_body_reaches_a_journal_entry_and_a_fragment(project, capsys):
    from luria import config
    # The fixture's YAML is written indented eight spaces (a triple-quoted
    # literal), so what is appended keeps that base indentation.
    (current().root / "luria.yaml").write_text(
        (current().root / "luria.yaml").read_text().rstrip("\n") + "\n"
        + "        journals:\n          devlog:\n            dir: devlog.d\n            output: docs/devlog\n"
        + "        fragments:\n          changelog.d:\n            file: CHANGELOG.md\n            style: changelog\n")
    config.reset()
    new_mod.run("devlog", title="Noted", body="**What.** It happened.")
    entry = (current().root / capsys.readouterr().out.strip()).read_text()
    assert entry.endswith("---\n\n**What.** It happened.\n"), entry
    assert "Write the entry here" not in entry
    new_mod.run("changelog", body="### Added\n\n- A body.")
    frag = (current().root / capsys.readouterr().out.strip()).read_text()
    assert frag == "### Added\n\n- A body.\n"


def test_a_draft_carries_its_body(project, capsys):
    from tests._scheme import decision
    decision(project, 1, "Active")
    path = _drafts_file(project, {
        "scheme": "ADR", "title": "Drafted", "influenced_by": ["ADR-001"],
        "body": "## Context\n\nDrawn on the canvas.\n",
    })
    new_mod.run(draft=path)
    text = (current().root / capsys.readouterr().out.strip()).read_text()
    assert "# ADR-002: Drafted\n\n## Context\n\nDrawn on the canvas.\n" in text
    assert "influenced_by:\n- ADR-001\n" in text
