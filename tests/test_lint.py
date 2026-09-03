"""Tests for the lint checks that guard a *kept* copy.

The `title:` check (ADR-013), the journal's path-vs-`created:` check
(ADR-020) and the `version:`-vs-`history:` check (ADR-019) are the same shape:
a fact recorded twice, where dropping one copy isn't available, so the remedy
is to guard that the two agree.

`title:` is the source of truth and the body's H1 repeats it, because someone
reading the file on its own needs a heading. Two copies of one string is the
drifting projection [DP-3](../docs/design-principles.md#dp-3) names, and the
remedy available here is rung 2 — keep the copy, guard the property that they
agree. So the guard needs firing, not just provisioning
([DP-6](../docs/design-principles.md#dp-6)).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

from luria import lint  # noqa: E402
from tests import _scheme  # noqa: E402


def errors_for(project) -> list[str]:
    found: list[str] = []
    lint.check_frontmatter(found)
    return found


def test_agreeing_title_and_heading_pass(project):
    _scheme.decision(project, 1, "Active", title="A decision")
    assert errors_for(project) == []


def test_a_drifted_heading_is_reported(project):
    """The failure this exists for: the title is corrected in one copy only."""
    path = _scheme.decision(project, 1, "Active", title="The corrected title")
    path.write_text(path.read_text().replace(
        "# ADR-001: The corrected title", "# ADR-001: The old title"))
    errors = errors_for(project)
    assert len(errors) == 1
    assert "disagree" in errors[0]
    # Both spellings are named — a diff the reader has to go and look up is
    # half a message (DP-1).
    assert "The corrected title" in errors[0] and "The old title" in errors[0]


def test_a_missing_title_is_reported(project):
    path = _scheme.decision(project, 1, "Active", title="A decision")
    path.write_text(path.read_text().replace("title: 'A decision'\n", ""))
    assert any("no `title:`" in e for e in errors_for(project))


def test_a_body_with_no_heading_is_not_a_disagreement(project):
    """Absence isn't drift. A fragment whose body opens with prose has nothing
    to contradict the frontmatter, and demanding a heading is a different rule
    from the one this check enforces."""
    path = _scheme.decision(project, 1, "Active", title="A decision")
    path.write_text(path.read_text().replace("# ADR-001: A decision\n", ""))
    assert errors_for(project) == []


def test_the_check_covers_every_scheme(project):
    """Not just decisions — a principle's title drifts the same way, and more
    often, because principles are expected to be reworded (ADR-012)."""
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "docs/decisions"\n'
        '[luria.schemes.VP]\ndir = "docs/values"\n'
        'render = "document"\noutput = "docs/values.md"\n')
    from luria import config
    config.reset()

    path = project / "docs" / "values" / "VP-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nstatus: Active\ntitle: 'A value'\ntags:\n- record\n"
                    "---\n\n# VP-001: A different value\n\nBody.\n")
    errors = errors_for(project)
    assert len(errors) == 1 and "VP-001.md" in errors[0]


# ── The journal's path agrees with its `created:` (ADR-020) ──────────────


def journal_project(project) -> Path:
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.journals.devlog]\ndir = "devlog.d"\noutput = "docs/devlog"\n')
    from luria import config
    config.reset()
    return project / "devlog.d"


def entry(root: Path, at: str, created: str | None = "same",
          title: str = "An entry") -> Path:
    """`at` is where the file goes; `created` is what it claims — the two are
    separate arguments precisely so a test can disagree with itself."""
    path = root / f"{at}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = at.replace("/", "")
    iso = (f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T"
           f"{stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]}"
           if created == "same" else created)
    front = [f"title: {title!r}"] if title else []
    if iso is not None:
        front.append(f"created: '{iso}'")
    path.write_text("---\n" + "\n".join(front) + "\n---\n\nBody.\n")
    return path


def journal_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_journals(found)
    return found


def test_an_entry_at_its_own_timestamp_passes(project):
    entry(journal_project(project), "2026/08/03/211926")
    assert journal_errors(project) == []


def test_a_moved_entry_is_reported(project):
    """The failure this exists for: the ordering the scheme rests on says one
    thing and the frontmatter says another."""
    root = journal_project(project)
    entry(root, "2026/08/03/211926", created="2026-08-04T03:27:11")
    errors = journal_errors(project)
    assert len(errors) == 1
    # Says where it belongs, not just that it's wrong (DP-1).
    assert "devlog.d/2026/08/04/032711.md" in errors[0]


def test_an_entry_with_no_created_is_reported(project):
    """When the path implies the timestamp, the error names the remedy —
    `luria repair` populates the field from it (#33)."""
    entry(journal_project(project), "2026/08/03/211926", created=None)
    errors = journal_errors(project)
    assert any("no `created:`" in e for e in errors)
    assert any("`luria repair` populates it from the path" in e for e in errors)


def test_an_entry_no_witness_can_date_is_reported_as_such(project):
    """A path that implies nothing leaves no witness to populate from, so the
    error asks the author instead of promising a remedy that won't come."""
    root = journal_project(project)
    path = root / "notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ntitle: 'Loose notes'\n---\n\nBody.\n")
    errors = journal_errors(project)
    assert any("the path doesn't imply one" in e for e in errors)


def test_an_untitled_entry_is_reported(project):
    """The title is what the book's contents list shows, so it isn't optional
    the way `tags:` is."""
    entry(journal_project(project), "2026/08/03/211926", title="")
    assert any("no `title:`" in e for e in journal_errors(project))


def test_the_template_is_exempt(project):
    root = journal_project(project)
    root.mkdir(parents=True, exist_ok=True)
    (root / "_template.md").write_text("---\ntitle: 'Shape'\n---\n\nShape.\n")
    assert journal_errors(project) == []


# ── `version:` agrees with `history:` (ADR-019) ──────────────────────────


def version_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_version_history(found)
    return found


def versioned(project, version: int, history: str = "") -> Path:
    path = _scheme.decision(project, 1, "Active", title="A decision")
    path.write_text(path.read_text().replace(
        "status: Active\n", f"status: Active\nversion: {version}\n{history}"))
    return path


def test_version_one_needs_no_history(project):
    versioned(project, 1)
    assert version_errors(project) == []


def test_a_bumped_version_with_no_history_is_reported(project):
    """A silent revision wearing a version number — which is the thing
    ADR-019 permits corrections *because* it rules out."""
    versioned(project, 2)
    assert any("no `history:`" in e for e in version_errors(project))


def test_history_that_agrees_passes(project):
    versioned(project, 2, "history:\n- version: 2\n  changed: 'Reworded.'\n")
    assert version_errors(project) == []


def test_history_that_lags_the_version_is_reported(project):
    versioned(project, 3, "history:\n- version: 2\n  changed: 'Reworded.'\n")
    errors = version_errors(project)
    assert len(errors) == 1 and "ends at version 2" in errors[0]


# ── A view directory holds only generated files (ADR-021) ────────────────


def generated_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_generated_index(found)
    return found


def test_a_hand_written_file_in_a_view_dir_is_a_violation(project):
    """The payoff of the read/write boundary: "don't hand-edit" is a checkable
    property, and its failure polarity points the right way — the stray file
    fails the build rather than quietly surviving beside the views."""
    from luria import config
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        'output = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, "Active")
    from luria import adr_index as builder
    for path, text in builder.outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert generated_errors(project) == []

    (project / "docs" / "decisions" / "notes.md").write_text("# Stray\n")
    errors = generated_errors(project)
    assert len(errors) == 1
    assert "notes.md" in errors[0] and "generator" in errors[0]


# ── The enforcement dial (ADR-035) ───────────────────────────────────────


def dial_project(project, fail_on: str = "") -> None:
    """A project with a retired decision cited from a docs page, and the
    dial set to `fail_on` (a TOML list body, e.g. '"retired-citations"')."""
    _scheme.decision(project, 12, "Superseded")
    page = project / "docs" / "notes.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("Still leaning on ADR-012 here.\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        f'[luria.lint]\nfail_on = [{fail_on}]\n')
    from luria import config
    config.reset()


def dial_errors(capsys) -> tuple[list[str], str]:
    found: list[str] = []
    lint.report_warnings(found)
    return found, capsys.readouterr().err


def test_the_default_posture_is_warn_only(project, capsys):
    """Nothing configured, nothing fails — every argument for warn-first
    survives as the argument for warn-by-default (ADR-035)."""
    dial_project(project)
    errors, err = dial_errors(capsys)
    assert errors == []
    assert "retired documents cited unacknowledged" in err


def test_a_promoted_class_fails_instead_of_printing(project, capsys):
    dial_project(project, '"retired-citations"')
    errors, err = dial_errors(capsys)
    assert any("failing: `fail_on`" in e for e in errors)
    assert any("ADR-012" in e for e in errors), "the detail rows come along"
    assert "retired documents cited unacknowledged" not in err, \
        "promoted, not duplicated"


def test_every_emitted_class_is_nameable_in_the_dial(project, capsys):
    """A class the linter can emit must be one the dial accepts.

    `legacy-spellings` was reported by `status_sections` but missing from
    FAILABLE, so a project asking to enforce it was told the class did not
    exist — the dial rejecting a notch it was already printing (DP-1). The
    assertion is over the whole vocabulary, not the one that bit."""
    dial_project(project, '"legacy-spellings"')
    errors, _ = dial_errors(capsys)
    assert not any("is no warning class" in e for e in errors), errors


def test_an_acknowledged_row_never_fails(project, capsys):
    """The dial changes the consequence, not the accounting — `inactive-ok:`
    is the escape hatch under enforcement too."""
    dial_project(project, '"retired-citations"')
    page = project / "docs" / "notes.md"
    page.write_text("<!-- inactive-ok: ADR-012 — quoted deliberately -->\n"
                    "Still leaning on ADR-012 here.\n")
    errors, _ = dial_errors(capsys)
    assert errors == []


def test_a_wrong_notch_is_an_error(project, capsys):
    """A dial set to a notch that doesn't exist must not silently enforce
    nothing (DP-1)."""
    dial_project(project, '"retired-refs"')
    errors, _ = dial_errors(capsys)
    assert any("no warning class" in e and "retired-citations" in e
               for e in errors)


def test_pending_documents_can_be_promoted(project, capsys):
    _scheme.decision(project, 2, "Proposed")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.lint]\nfail_on = ["pending-documents"]\n')
    from luria import config
    config.reset()
    errors, _ = dial_errors(capsys)
    assert any("undecided document(s)" in e and "failing" in e for e in errors)
