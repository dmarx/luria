"""Tests for the lint checks that guard a *kept* copy.

The `title:` check (ADR-013), the journal's path-vs-`created:` check
(ADR-020) and the `version:`-vs-`history:` check (ADR-019) are the same shape:
a fact recorded twice, where dropping one copy isn't available, so the remedy
is to guard that the two agree.

`title:` is the source of truth and the body's H1 repeats it, because someone
reading the file on its own needs a heading. Two copies of one string is the
drifting projection [DP-3](../meta/design-principles.md#dp-3) names, and the
remedy available here is rung 2 — keep the copy, guard the property that they
agree. So the guard needs firing, not just provisioning
([DP-6](../meta/design-principles.md#dp-6)).
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
        '[luria.schemes.DP]\ndir = "docs/principles"\n'
        'render = "document"\noutput = "docs/design-principles.md"\n')
    from luria import config
    config.reset()

    path = project / "docs" / "principles" / "DP-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nstatus: Active\ntitle: 'A value'\ntags:\n- record\n"
                    "---\n\n# DP-001: A different value\n\nBody.\n")
    errors = errors_for(project)
    assert len(errors) == 1 and "DP-001.md" in errors[0]


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
    entry(journal_project(project), "2026/08/03/211926", created=None)
    assert any("no `created:`" in e for e in journal_errors(project))


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


# ── Documentation roots (ADR-021) ────────────────────────────────────────


def two_roots(project) -> None:
    """A project shaped like this repo: prose in `docs/`, the record in
    `meta/`, each root indexed by its own README."""
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\ndocs = ["docs", "meta"]\ndecisions = "meta/decisions"\n'
        '[luria.schemes.ADR]\ndir = "meta/decisions"\n')
    from luria import config
    config.reset()
    (project / "meta").mkdir(exist_ok=True)
    (project / "docs" / "README.md").write_text(
        "# Docs\n\n- [Doctrine](doctrine.md)\n- [Values](design-principles.md)\n")
    (project / "docs" / "doctrine.md").write_text("# Doctrine\n")
    (project / "meta" / "README.md").write_text("# Record\n")


def index_errors(project) -> list[str]:
    found: list[str] = []
    lint.check_docs_index(found)
    return found


def test_each_root_is_checked_against_its_own_index(project):
    two_roots(project)
    assert index_errors(project) == []


def test_an_unindexed_page_in_the_second_root_is_reported(project):
    """The failure the second root would otherwise be exempt from: before
    `paths.docs` took a list, only the first root was checked at all."""
    two_roots(project)
    (project / "meta" / "notes.md").write_text("# Notes\n")
    errors = index_errors(project)
    assert len(errors) == 1
    assert "meta/README.md" in errors[0] and "notes.md" in errors[0]


def test_an_index_does_not_satisfy_the_other_root(project):
    """Coverage is per root. Listing `meta/`'s page from `docs/README.md` is
    not the same claim and must not silence the check."""
    two_roots(project)
    (project / "meta" / "notes.md").write_text("# Notes\n")
    (project / "docs" / "README.md").write_text(
        "# Docs\n\n- [Doctrine](doctrine.md)\n- [Values](design-principles.md)\n"
        "- [Notes](notes.md)\n")
    assert any("meta/README.md" in e for e in index_errors(project))


def test_a_journals_entry_directory_is_not_a_page_to_index(project):
    """`meta/devlog.d/` holds sources, like a scheme directory — and once the
    record moved into a documentation root, the index check could see it."""
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\ndocs = ["docs", "meta"]\n'
        '[luria.journals.devlog]\ndir = "meta/devlog.d"\noutput = "meta/devlog"\n')
    from luria import config
    config.reset()
    entries = project / "meta" / "devlog.d"
    entries.mkdir(parents=True)
    (entries / "_template.md").write_text("---\ntitle: 'Shape'\n---\n\nShape.\n")
    (project / "meta" / "README.md").write_text("# Record\n")
    assert index_errors(project) == []
