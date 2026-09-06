# tests/test_relations.py
"""A relation and its converse (#180).

`compared_against` is symmetric and `extends` is not, and the first
implementation drew the wrong conclusion from that: it completed the
symmetric one and refused to touch the directed one at all. But the
constraint is narrower than "directed relations are untouchable". What is
never valid is mirroring a relation into *its own* field — `extends: A` on
the document A extends asserts something false, and shows up as a cycle.
Writing it into a *converse* field is valid, and symmetry is simply the case
where the converse is the relation itself.

So a relation may declare its converse, and only then is anything completed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import subprocess

from luria import config, relations


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


PAIRED = """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", required = false, many = true, converse = "extended_by" }
extended_by = { scheme = "LIT", required = false, many = true, converse = "extends" }
compared_against = { scheme = "LIT", required = false, many = true, converse = "compared_against" }
"""

UNPAIRED = """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", required = false, many = true }
compared_against = { scheme = "LIT", required = false, many = true }
"""


def project(tmp_path, monkeypatch, extra: str = PAIRED) -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.LIT]
dir = "record/literature.d"
output = "docs/literature"
{extra}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def note(root: Path, number: int, title: str = "A note", **fields) -> Path:
    front = ["---", "status: Active", f"title: {title!r}", "tags:",
             "- record", "date: '2026-01-01'"]
    for name, codes in fields.items():
        if codes:
            front.append(f"{name}:")
            front += [f"- {c}" for c in codes]
    front += ["---", "", f"# LIT-{number:03d}: {title}", "", "Body."]
    return write(root, f"record/literature.d/LIT-{number:03d}.md",
                 "\n".join(front) + "\n")


# --- what the config may declare --------------------------------------------

def test_a_converse_must_name_a_declared_reference(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="extended_by"):
        project(tmp_path, monkeypatch, """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", many = true, converse = "extended_by" }
""")
        config.current()


def test_a_converse_must_be_mutual(tmp_path, monkeypatch):
    """The converse of the converse is the relation. A half-declaration
    leaves one direction completing and the other not."""
    with pytest.raises(ValueError, match="mutual|converse"):
        project(tmp_path, monkeypatch, """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", many = true, converse = "extended_by" }
extended_by = { scheme = "LIT", many = true }
""")
        config.current()


def test_a_converse_must_point_at_the_same_scheme(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="scheme"):
        project(tmp_path, monkeypatch, """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", many = true, converse = "extended_by" }
extended_by = { scheme = "ADR", many = true, converse = "extends" }
""")
        config.current()


def test_both_sides_of_a_pair_hold_a_list(tmp_path, monkeypatch):
    """Completion writes into either side, and N documents can extend one."""
    with pytest.raises(ValueError, match="many|list"):
        project(tmp_path, monkeypatch, """
[luria.schemes.LIT.references]
extends = { scheme = "LIT", many = true, converse = "extended_by" }
extended_by = { scheme = "LIT", converse = "extends" }
""")
        config.current()


def test_a_relation_is_its_own_converse_when_it_says_so(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch)
    pairs = relations.pairs()
    assert ("LIT", "compared_against", "compared_against") in pairs
    assert ("LIT", "extends", "extended_by") in pairs


# --- what gets completed ----------------------------------------------------

def test_a_directed_relation_completes_into_its_converse(
        tmp_path, monkeypatch):
    """The correction. `extends` is directed and is completed anyway —
    into `extended_by`, where the fact is true."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    todo = relations.completions()
    assert len(todo) == 1
    assert todo[0].path.name == "LIT-001.md"
    assert todo[0].field == "extended_by" and todo[0].code == "LIT-002"


def test_completion_runs_in_both_directions(tmp_path, monkeypatch):
    """Declaring the converse is as good as declaring the relation."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original", extended_by=["LIT-002"])
    note(root, 2, "The replacement")
    todo = relations.completions()
    assert len(todo) == 1
    assert todo[0].path.name == "LIT-002.md"
    assert todo[0].field == "extends" and todo[0].code == "LIT-001"


def test_a_relation_with_no_converse_is_never_completed(
        tmp_path, monkeypatch):
    """The user's condition: absent a declared duality, inventing the
    reverse edge is a guess, so nothing is written and nothing is reported."""
    root = project(tmp_path, monkeypatch, UNPAIRED)
    note(root, 1, "One design")
    note(root, 2, "The other", compared_against=["LIT-001"], extends=["LIT-001"])
    assert relations.completions() == []
    assert relations.rows() == []


def test_a_symmetric_relation_completes_into_itself(tmp_path, monkeypatch):
    """Self-converse is symmetry — the same rule, not a second one."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "One design")
    note(root, 2, "The other", compared_against=["LIT-001"])
    todo = relations.completions()
    assert len(todo) == 1
    assert todo[0].field == "compared_against" and todo[0].code == "LIT-002"


def test_a_relation_is_never_mirrored_into_its_own_field(
        tmp_path, monkeypatch):
    """The constraint that survives: A extends B does not make B extend A."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    text = (root / "record/literature.d/LIT-001.md").read_text()
    assert "extended_by:" in text
    assert "extends:" not in text


def test_writing_the_back_reference_clears_the_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert relations.rows()
    relations.complete(fix=True)
    config.reset()
    assert relations.rows() == []


def test_completing_is_idempotent(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    assert relations.complete(fix=True) == []


def test_without_fix_nothing_is_written(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    before = (root / "record/literature.d/LIT-001.md").read_text()
    assert relations.complete(fix=False)
    assert (root / "record/literature.d/LIT-001.md").read_text() == before


def test_a_scalar_field_becomes_a_list_rather_than_losing_a_value(
        tmp_path, monkeypatch):
    """`many` accepts one code written as a scalar. Appending must keep the
    value that was there — the failure would be silent and delete a relation."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "One replacement")
    note(root, 3, "Another replacement", extends=["LIT-001"])
    p = root / "record/literature.d/LIT-001.md"
    p.write_text(p.read_text().replace(
        "tags:", "extended_by: LIT-002\ntags:", 1))
    config.reset()
    relations.complete(fix=True)
    config.reset()
    text = (root / "record/literature.d/LIT-001.md").read_text()
    assert "- LIT-002" in text and "- LIT-003" in text


def test_a_contradiction_across_the_pair_is_not_completable(
        tmp_path, monkeypatch):
    """`extends: B` and `extended_by: B` on one document says B is both
    older and newer. There is no side to write; a person has to choose."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "Both at once", extends=["LIT-001"], extended_by=["LIT-001"])
    assert relations.completions() == []
    assert relations.rows()


def test_the_finding_names_the_field_it_would_write(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    row, = relations.rows()
    assert "extended_by" in row and "luria link --fix" in row


# --- the fixer --------------------------------------------------------------

def test_link_fix_completes_by_default(tmp_path, monkeypatch):
    from luria import link_refs
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    link_refs.run(fix=True)
    config.reset()
    assert relations.rows() == []


def test_links_only_reproduces_the_old_behaviour(tmp_path, monkeypatch):
    from luria import link_refs
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    before = (root / "record/literature.d/LIT-001.md").read_text()
    link_refs.run(fix=True, links_only=True)
    config.reset()
    assert (root / "record/literature.d/LIT-001.md").read_text() == before
    assert relations.rows()


def test_the_class_is_promotable_and_wired(tmp_path, monkeypatch):
    from luria import lint
    assert "one-sided-relations" in lint.FAILABLE
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert "one-sided-relations" in {n for n, _, _ in lint.status_sections()}


# --- Adding versus removing (#181) -----------------------------------------
#
# The first cut of this mechanism was monotonic: it wrote a missing side and
# had no idea a side could go away. Delete `extends: LIT-001` from LIT-002,
# run `--fix`, and it came back — because a one-sided pair has two readings
# and the working tree holds neither of them. Which side *changed* is the
# missing fact, and it lives in the last committed state.


def commit(root: Path, message: str = "state") -> None:
    for args in (["init", "-q", "-b", "main"], ["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t",
                  "commit", "-q", "-m", message]):
        subprocess.run(["git", *args], cwd=root, check=False,
                       capture_output=True)


def edit(root: Path, number: int, old: str, new: str = "") -> None:
    p = root / f"record/literature.d/LIT-{number:03d}.md"
    p.write_text(p.read_text().replace(old, new))
    config.reset()


def test_a_side_added_since_the_last_commit_is_propagated(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement")
    commit(root)
    edit(root, 2, "tags:", "extends:\n- LIT-001\ntags:")
    relations.complete(fix=True)
    assert "extended_by:" in (root / "record/literature.d/LIT-001.md").read_text()


def test_a_side_removed_since_the_last_commit_prunes_the_other(
        tmp_path, monkeypatch):
    """The bug this exists to fix. The author deletes the relation from the
    document that declared it; the back-reference must go, not come back."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "extends:\n- LIT-001\n")
    relations.complete(fix=True)
    first = (root / "record/literature.d/LIT-001.md").read_text()
    second = (root / "record/literature.d/LIT-002.md").read_text()
    assert "LIT-002" not in first, "the stale back-reference survived"
    assert "LIT-001" not in second, "the deleted relation was written back"


def test_pruning_is_idempotent(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "extends:\n- LIT-001\n")
    relations.complete(fix=True)
    config.reset()
    assert relations.complete(fix=True) == []


def test_a_pruned_field_that_empties_is_removed_entirely(
        tmp_path, monkeypatch):
    """A bare `extended_by:` with nothing under it is not valid frontmatter
    for a reference field, and reads as a relation nobody can name."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "extends:\n- LIT-001\n")
    relations.complete(fix=True)
    assert "extended_by" not in (
        root / "record/literature.d/LIT-001.md").read_text()


def test_a_pruned_field_keeps_its_other_codes(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "One replacement", extends=["LIT-001"])
    note(root, 3, "Another replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "extends:\n- LIT-001\n")
    relations.complete(fix=True)
    text = (root / "record/literature.d/LIT-001.md").read_text()
    assert "LIT-003" in text and "LIT-002" not in text


def test_removing_both_sides_needs_no_repair(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "extends:\n- LIT-001\n")
    edit(root, 1, "extended_by:\n- LIT-002\n")
    assert relations.completions() == []
    assert relations.rows() == []


def test_one_side_added_while_the_other_was_removed_is_a_conflict(
        tmp_path, monkeypatch):
    """Both edits are deliberate and they contradict. Writing either loses
    one of them, so the fixer reports and touches nothing."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    commit(root)
    # one editor withdraws the relation, another asserts it from the far side
    edit(root, 2, "extends:\n- LIT-001\n")
    edit(root, 1, "tags:", "extended_by:\n- LIT-002\ntags:")
    before = (root / "record/literature.d/LIT-001.md").read_text()
    assert relations.completions() == []
    assert any("contradict" in r or "both" in r for r in relations.rows())
    relations.complete(fix=True)
    assert (root / "record/literature.d/LIT-001.md").read_text() == before


def test_an_unchanged_one_sided_pair_still_completes(tmp_path, monkeypatch):
    """The migration path: a record that predates the fixer has one-sided
    pairs at HEAD too, and nothing has changed. Adding is the safe reading —
    a deletion the author repeats becomes a change, and prunes."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    commit(root)
    assert len(relations.completions()) == 1


def test_a_document_git_has_never_seen_reads_as_added(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    commit(root)
    note(root, 2, "The replacement", extends=["LIT-001"])
    config.reset()
    assert len(relations.completions()) == 1


def test_without_git_everything_reads_as_added(tmp_path, monkeypatch):
    """No repository, no baseline — the fixer keeps its old behaviour rather
    than refusing to work."""
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    assert len(relations.completions()) == 1


def test_a_symmetric_relation_prunes_too(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "One design")
    note(root, 2, "The other", compared_against=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "compared_against:\n- LIT-001\n")
    relations.complete(fix=True)
    assert "LIT-002" not in (
        root / "record/literature.d/LIT-001.md").read_text()


def test_the_finding_says_which_way_the_fixer_will_go(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1, "The original")
    note(root, 2, "The replacement", extends=["LIT-001"])
    relations.complete(fix=True)
    config.reset()
    commit(root)
    edit(root, 2, "extends:\n- LIT-001\n")
    row, = relations.rows()
    assert "remove" in row or "stale" in row, row
