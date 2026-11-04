# tests/test_unconcretize.py
"""`luria unconcretize CODE`: give a branch's number back, as a temporary code.

A filing-allocated scheme takes the next free number on the branch. When the
trunk takes the same number first, the two documents collide at merge: an
add/add conflict on the file, and every citation the branch wrote now names
the trunk's document. The fix is the inverse of `luria concretize`: the
document becomes temporary, and `concretize` numbers it at merge.

The command does not ask why: it flips the documents it is named, and
rewrites their codes everywhere `concretize` would. For a collision, run it
on the branch before merging the trunk, while every occurrence in the tree
still means the branch's document.

The case that asked for it: nucleation#387 filed ADR-068 on a branch while
the trunk merged a different ADR-068. The fix was by hand.
"""
import subprocess
from pathlib import Path

import pytest

from luria import concretize, config, unconcretize

YAML = """
issue_url: https://example.test/issues/{n}
schemes:
  ADR:
    dir: record/decisions.d
    output: docs/decisions
"""


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=root, check=True, capture_output=True, text=True).stdout


def adr(root: Path, number: int, title: str, body: str = "") -> Path:
    path = root / "record" / "decisions.d" / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nnumber: {number}\nstatus: Proposed\n"
                    f"title: {title!r}\ntags:\n- record\ndate: '2026-01-01'\n"
                    f"---\n\n# ADR-{number:03d}: {title}\n\n{body}\n")
    return path


@pytest.fixture
def branch(tmp_path, monkeypatch):
    """A trunk with ADR-001, and a branch `feature` that filed ADR-002 and
    cites it: in its own new file, and in a line it added to a file the
    trunk already had.
    Then the trunk takes ADR-002 for itself."""
    root = tmp_path
    (root / "luria.yaml").write_text(YAML)
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()
    adr(root, 1, "Trunk decision")
    notes = root / "docs" / "notes.md"
    notes.parent.mkdir(parents=True)
    notes.write_text("# Notes\n\nNothing here yet.\n")
    git(root, "init", "-q", "-b", "main", ".")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "trunk")
    git(root, "checkout", "-qb", "feature")
    adr(root, 2, "Branch decision", "Builds on ADR-001. See ADR-0021, unrelated.")
    notes.write_text(notes.read_text() + "\nThe branch files ADR-002.\n")
    (root / "docs" / "branch.md").write_text(
        "Per [ADR-002](../record/decisions.d/ADR-002.md), and #adr-002.\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "branch")
    git(root, "checkout", "-q", "main")
    adr(root, 2, "Trunk's own second decision")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "trunk takes 2")
    git(root, "checkout", "-q", "feature")
    config.reset()
    return root


def temp_doc(root: Path) -> Path:
    temps = config.current().schemes["ADR"].temp_documents()
    assert len(temps) == 1, temps
    return next(iter(temps.values()))


def test_the_document_becomes_temporary(branch):
    unconcretize.run("ADR-002")
    doc = temp_doc(branch)
    code = doc.stem
    assert not (branch / "record/decisions.d/ADR-002.md").exists()
    text = doc.read_text()
    assert "number:" not in text
    assert f"# {code}: Branch decision" in text
    assert "formerly:" not in text, "the number goes back; it is not an alias"


def test_by_default_every_occurrence_is_rewritten(branch):
    unconcretize.run("ADR-002")
    code = temp_doc(branch).stem
    notes = (branch / "docs" / "notes.md").read_text()
    assert f"The branch files {code}." in notes
    linked = (branch / "docs" / "branch.md").read_text()
    assert f"[{code}](../record/decisions.d/{code}.md)" in linked
    assert f"#{code.lower()}" in linked


def test_the_config_is_rewritten_too(branch):
    cfg = branch / "luria.yaml"
    cfg.write_text(cfg.read_text() + "# the rule ADR-002 adopted\n")
    unconcretize.run("ADR-002")
    assert f"# the rule {temp_doc(branch).stem} adopted" in cfg.read_text()


def test_a_longer_code_is_not_a_match(branch):
    unconcretize.run("ADR-002")
    assert "See ADR-0021, unrelated." in temp_doc(branch).read_text()


def test_the_branch_then_merges_cleanly_and_concretizes(branch):
    unconcretize.run("ADR-002")
    git(branch, "add", "-A")
    git(branch, "commit", "-qm", "give the number back")
    git(branch, "merge", "-q", "--no-edit", "main")
    config.reset()
    concretize.run()
    docs = config.current().schemes["ADR"].documents()
    assert sorted(docs) == [1, 2, 3]
    assert "Branch decision" in docs[3].read_text()
    assert "Trunk's own second decision" in docs[2].read_text()
    assert "The branch files ADR-003." in (branch / "docs/notes.md").read_text()


def test_several_codes_at_once_renumber_a_scheme(branch):
    """Giving back every number and concretizing renumbers the scheme
    contiguously, in concretize's order: when each temporary file was
    committed. Files given back in one commit tie, so which takes which
    number is concretize's tie-break, not something this command promises."""
    unconcretize.run("ADR-001", "ADR-002")
    assert config.current().schemes["ADR"].documents() == {}
    assert len(config.current().schemes["ADR"].temp_documents()) == 2
    git(branch, "add", "-A")
    git(branch, "commit", "-qm", "give both back")
    config.reset()
    concretize.run()
    docs = config.current().schemes["ADR"].documents()
    assert sorted(docs) == [1, 2]
    titles = sorted(p.read_text().split("title: ")[1].split("\n")[0]
                    for p in docs.values())
    assert titles == ["'Branch decision'", "'Trunk decision'"]


def test_a_code_with_no_document_is_refused(branch):
    with pytest.raises(SystemExit, match="ADR-009"):
        unconcretize.run("ADR-009")


def test_it_says_what_it_did(branch, capsys):
    unconcretize.run("ADR-002")
    out = capsys.readouterr().out
    code = temp_doc(branch).stem
    assert f"ADR-002 → {code}" in out
    assert "3 file(s)" in out
