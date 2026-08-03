"""Tests for the `title:` frontmatter check (ADR-013).

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
