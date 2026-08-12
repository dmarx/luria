"""Merge-allocated schemes: temporary codes, concretization, aliases (ADR-049).

Every test here runs the loop an adopter runs: mint on a branch, cite while
the context is loaded, concretize where merges serialize, and keep the old
name resolving forever. The fixture builds a real record and drives the real
commands — the pattern ADR-045 established, because the first hand-fired run
of this machinery found a crash (`render_categories` formatting a number that
temp docs don't have) that no unit test of the minter would have seen.
"""
import re
import subprocess
from pathlib import Path

import pytest

from luria import adr_index, concretize, config, doc_refs, lint, new

TOML = """\
[luria]
issue_url = "https://example.test/issues/{n}"
[luria.schemes.ADR]
dir = "record/decisions.d"
output = "docs/decisions"
allocate = "merge"
"""


@pytest.fixture
def merge_project(tmp_path, monkeypatch):
    """A record whose ADR scheme allocates at merge, with two temporary
    documents that cite each other — one bare, one wikilinked."""
    (tmp_path / "luria.toml").write_text(TOML)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "# Docs\n\n- [Decisions](decisions/README.md)\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()

    first = new.new_entry("adr", {"title": "First decision"}, None)
    second = new.new_entry("adr", {"title": "Second decision"}, None)
    a, b = first.stem, second.stem
    first.write_text(first.read_text() + f"\nPaired with [[{b}]].\n")
    second.write_text(second.read_text() + f"\nBuilds on {a}.\n")
    subprocess.run(["git", "init", "-q", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "seed"], cwd=tmp_path, check=True)
    return tmp_path, first, second


def lint_errors() -> list[str]:
    errors: list[str] = []
    lint.check_frontmatter(errors)
    lint.check_bare_refs(errors)
    lint.check_wikilinks(errors)
    return errors


def test_a_minted_code_can_never_be_read_as_a_number(merge_project):
    _, first, second = merge_project
    scheme = config.current().schemes["ADR"]
    for path in (first, second):
        tail = scheme.temp_of(path)
        assert re.fullmatch(r"[a-z][a-z0-9]{5}", tail)
        assert scheme.number_of(path) is None, "the patterns are disjoint"


def test_temp_documents_are_first_class_on_the_branch(merge_project):
    """Indexed, linted, and their citations demanded and linkable — the whole
    point is that a branch can write against the document it just filed."""
    root, first, second = merge_project
    adr_index.run()

    index = (root / "docs" / "decisions" / "README.md").read_text()
    assert first.stem in index and second.stem in index

    errors = lint_errors()
    assert any(f"{first.stem} is not a link" in e for e in errors), \
        "a bare temp reference is demanded like any other"

    linked, count = doc_refs.linkify(second.read_text(), second)
    assert count == 1
    assert f"[{first.stem}]({first.name})" in linked


def test_concretize_assigns_renames_rewrites_and_aliases(merge_project):
    root, first, second = merge_project
    a, b = first.stem, second.stem
    doc_refs_fixed = doc_refs.linkify(second.read_text(), second)[0]
    second.write_text(doc_refs_fixed)
    adr_index.run()

    concretize.run()

    scheme = config.current().schemes["ADR"]
    docs = scheme.documents()
    assert sorted(docs) == [1, 2], "sequential numbers, no temp files left"
    assert scheme.temp_documents() == {}

    # References rewritten to the real codes, targets included.
    texts = {n: p.read_text() for n, p in docs.items()}
    by_title = {("First" if "First" in t else "Second"): (n, t)
                for n, t in texts.items()}
    n_first, t_first = by_title["First"]
    n_second, t_second = by_title["Second"]
    assert f"[ADR-{n_first:03d}](ADR-{n_first:03d}.md)" in t_second
    assert a not in t_second, "no temporary code survives outside aka:"

    # The temporary code is recorded as an alias on its own document only.
    assert re.search(rf"^aka:\n- {a}$", t_first, flags=re.MULTILINE)

    # And the views regenerated in the same run.
    index = (root / "docs" / "decisions" / "README.md").read_text()
    assert "ADR-001" in index and a not in index


def test_an_aliased_code_resolves_forever(merge_project):
    """The citation the rewriter can't reach — a PR thread, a commit message
    — must keep resolving after concretization: an old name, never a dead
    one."""
    root, first, _ = merge_project
    a = first.stem
    concretize.run()

    elsewhere = root / "docs" / "README.md"
    linked, count = doc_refs.linkify(f"As {a} said.", elsewhere)
    assert count == 1 and "record/decisions.d/ADR-" in linked
    wiki, count = doc_refs.linkify(f"And [[{a}]] too.", elsewhere)
    assert count == 1 and "record/decisions.d/ADR-" in wiki


def test_check_guards_the_trunk(merge_project):
    """A temporary code on main is always wrong and mechanically fixable, so
    it fails — ADR-035's bar for a failing check."""
    with pytest.raises(SystemExit):
        concretize.run(check=True)
    concretize.run()
    concretize.run(check=True)          # clean now: must not raise


def test_concretize_leaves_historical_files_alone(merge_project):
    """A dated record is true about its day; the alias is what keeps its
    temporary codes resolving, not a rewrite of what was written."""
    root, first, _ = merge_project
    a = first.stem
    (root / "luria.toml").write_text(
        TOML + '[luria.journals.devlog]\ndir = "record/devlog.d"\n'
               'output = "docs/devlog"\n')
    config.reset()
    entry = root / "record" / "devlog.d" / "2026" / "01" / "02" / "030405.md"
    entry.parent.mkdir(parents=True)
    entry.write_text(f"---\ntitle: 'A day'\ncreated: '2026-01-02T03:04:05'\n"
                     f"---\n\nToday we filed {a}.\n")

    concretize.run()
    assert a in entry.read_text(), "historical text stays as written"
    linked, count = doc_refs.linkify(entry.read_text(), entry)
    assert count >= 1, "…and the alias keeps it resolvable"


def test_filing_allocation_is_untouched(project):
    """The default dial: a scheme without `allocate = "merge"` still numbers
    at creation, exactly as before."""
    (project / "record" / "decisions.d").mkdir(parents=True)
    path = new.new_entry("adr", {"title": "Numbered on the spot"}, None)
    assert path.name == "ADR-001.md"
