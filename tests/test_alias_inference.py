"""A spelling a reader can interpret, rendered from frontmatter (#219).

The identifier stays the number `luria concretize` assigns; the alias is a
second spelling of it, recomputed on every read and therefore always true.

The fixtures use the reserved local fixture prefix `FXL` (ADR-093), so a
specimen spelling here cannot read as a citation of any real document.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import aliases, config, doc_refs, lint


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def project(tmp_path, monkeypatch, alias: str = 'alias = "FXL-{authors[0]}-{year}-{number}"') -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"

[luria.schemes.FXL]
dir = "record/fixtures.d"
output = "docs/fixtures"
{alias}
""")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path


def note(root: Path, number: int, *, author="Kingma", year=2014,
         formerly=(), title="A paper") -> Path:
    front = ["---", f"number: {number}", "status: Active", f"title: '{title}'",
             "authors:", f"- {author}", f"year: {year}", "date: '2026-01-01'"]
    if formerly:
        front.append("formerly:")
        front += [f"- {c}" for c in formerly]
    front += ["---", "", f"# FXL-{number:03d}: {title}", "", "Body."]
    return write(root, f"record/fixtures.d/FXL-{number:03d}.md",
                 "\n".join(front) + "\n")


def scheme():
    return config.current().schemes["FXL"]


# --- rendering ---------------------------------------------------------------

def test_the_alias_renders_from_the_document(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 41)
    entry = aliases.alias_map()["FXL-Kingma-2014-41"]
    assert entry.code == "FXL-041"
    assert entry.kind == aliases.ALSO_KNOWN_AS


def test_a_template_naming_a_missing_field_renders_nothing(tmp_path, monkeypatch):
    """Half a spelling would resolve for some documents and not others, with
    nothing saying which — so a template that cannot be filled yields none."""
    root = project(tmp_path, monkeypatch,
                   'alias = "FXL-{editor}-{number}"')
    note(root, 41)
    assert aliases.alias_map() == {}


def test_no_template_means_no_derived_aliases(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, alias="")
    note(root, 41)
    assert aliases.alias_map() == {}


def test_correcting_the_source_moves_the_alias(tmp_path, monkeypatch):
    """Recomputed, therefore always true — and therefore the old spelling
    stops resolving, which is why `formerly:` has to catch it."""
    root = project(tmp_path, monkeypatch)
    note(root, 41, author="Askell")
    assert "FXL-Askell-2014-41" in aliases.alias_map()
    note(root, 41, author="Bai")
    config.reset(); aliases.reset()
    entries = aliases.alias_map()
    assert "FXL-Askell-2014-41" not in entries
    assert "FXL-Bai-2014-41" in entries


def test_a_superseded_spelling_kept_in_formerly_still_resolves(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 41, author="Bai", formerly=["FXL-Askell-2014-41"])
    entries = aliases.alias_map()
    assert entries["FXL-Bai-2014-41"].kind == aliases.ALSO_KNOWN_AS
    assert entries["FXL-Askell-2014-41"].kind == aliases.FORMERLY
    assert entries["FXL-Askell-2014-41"].code == "FXL-041"


def test_a_real_code_outranks_another_document_s_nickname(tmp_path, monkeypatch):
    """A document's own name wins: an alias that happens to spell a code
    must never shadow the document that code belongs to."""
    root = project(tmp_path, monkeypatch, 'alias = "FXL-{year}"')
    note(root, 41, year=2014)
    assert "FXL-2014" not in aliases.alias_map()


# --- resolution and the fixer ------------------------------------------------

def test_an_alias_resolves_like_the_code(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 41)
    assert doc_refs.alias_number(scheme(), "Kingma-2014-41") == 41


def test_a_shape_that_resolves_to_nothing_is_not_a_reference(
        tmp_path, monkeypatch):
    """The precision rule: the map decides, not the pattern. Otherwise a
    widened tail would start matching prose."""
    root = project(tmp_path, monkeypatch)
    note(root, 41)
    assert doc_refs.alias_number(scheme(), "based") is None
    assert doc_refs.alias_number(scheme(), "Hinton-1986-99") is None


def test_the_fixer_leaves_a_derived_alias_written(tmp_path, monkeypatch):
    """The whole point. Canonicalizing here would erase the readable
    identifier on the first `luria link --fix`."""
    root = project(tmp_path, monkeypatch)
    note(root, 41)
    ref = doc_refs.Ref(kind="scheme", num=0, start=0, end=0,
                       text="FXL-Kingma-2014-41", line=1, prefix="FXL",
                       code="Kingma-2014-41")
    assert doc_refs._label(ref) == "FXL-Kingma-2014-41"


def test_the_fixer_still_upgrades_a_past_spelling(tmp_path, monkeypatch):
    """The opposite instruction, over the same map — which is why an entry
    carries its kind rather than the caller guessing from shape."""
    root = project(tmp_path, monkeypatch)
    note(root, 41, formerly=["FXL-tmpabcde"])
    ref = doc_refs.Ref(kind="scheme", num=0, start=0, end=0,
                       text="FXL-tmpabcde", line=1, prefix="FXL",
                       code="tmpabcde")
    assert doc_refs._label(ref) == "FXL-041"


# --- collisions --------------------------------------------------------------

def test_two_documents_on_one_spelling_is_a_violation(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, 'alias = "FXL-{authors[0]}-{year}"')
    note(root, 41); note(root, 42)
    errors: list[str] = []
    lint.check_alias_collisions(errors)
    assert len(errors) == 1
    assert "renders `FXL-Kingma-2014` for FXL-041, FXL-042" in errors[0]


def test_the_number_makes_collisions_impossible(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 41); note(root, 42)
    errors: list[str] = []
    lint.check_alias_collisions(errors)
    assert errors == []


# --- refused at load ---------------------------------------------------------

def test_a_template_without_the_prefix_is_refused(tmp_path, monkeypatch):
    """Every scanner finds a code by its prefix first, so a spelling without
    one is unreachable however well it resolves."""
    project(tmp_path, monkeypatch, 'alias = "{authors[0]}-{year}"')
    with pytest.raises(ValueError, match="does not start with 'FXL-'"):
        config.current()


def test_an_unrenderable_template_is_refused(tmp_path, monkeypatch):
    project(tmp_path, monkeypatch, 'alias = "FXL-{authors[0"')
    with pytest.raises(ValueError, match="not a template"):
        config.current()


# --- retiring a superseded spelling ------------------------------------------

def _git(root, *args):
    import subprocess
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def committed_project(tmp_path, monkeypatch, **kw):
    root = project(tmp_path, monkeypatch, **kw)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.test")
    _git(root, "config", "user.name", "T")
    return root


def test_a_changed_source_field_retires_the_old_spelling(tmp_path, monkeypatch):
    """The old spelling comes from git rather than a stored ledger: the
    previous frontmatter is already written down, so recording each rendered
    alias in the document too would be a copy per revision."""
    from luria import repair
    root = committed_project(tmp_path, monkeypatch)
    note(root, 41, author="Askell")
    _git(root, "add", "-A"); _git(root, "commit", "-qm", "filed")

    note(root, 41, author="Bai")          # the attribution is corrected
    config.reset(); aliases.reset()
    changed = repair.retire_aliases(scheme())
    assert [p.name for p in changed] == ["FXL-041.md"]

    config.reset(); aliases.reset()
    entries = aliases.alias_map()
    assert entries["FXL-Bai-2014-41"].kind == aliases.ALSO_KNOWN_AS
    assert entries["FXL-Askell-2014-41"].kind == aliases.FORMERLY
    assert entries["FXL-Askell-2014-41"].code == "FXL-041"


def test_the_retirement_is_idempotent(tmp_path, monkeypatch):
    from luria import repair
    root = committed_project(tmp_path, monkeypatch)
    note(root, 41, author="Askell")
    _git(root, "add", "-A"); _git(root, "commit", "-qm", "filed")
    note(root, 41, author="Bai")
    config.reset(); aliases.reset()
    repair.retire_aliases(scheme())
    config.reset(); aliases.reset()
    assert repair.retire_aliases(scheme()) == []


def test_an_unchanged_alias_retires_nothing(tmp_path, monkeypatch):
    from luria import repair
    root = committed_project(tmp_path, monkeypatch)
    note(root, 41, author="Askell")
    _git(root, "add", "-A"); _git(root, "commit", "-qm", "filed")
    note(root, 41, author="Askell", title="A retitled paper")
    config.reset(); aliases.reset()
    assert repair.retire_aliases(scheme()) == []


def test_a_document_with_no_history_retires_nothing(tmp_path, monkeypatch):
    """Absence of history is not a change of spelling. A repair that guessed
    here would write a `formerly:` naming something that never existed."""
    from luria import repair
    root = committed_project(tmp_path, monkeypatch)
    note(root, 41)
    _git(root, "add", "-A"); _git(root, "commit", "-qm", "empty-ish")
    note(root, 42, author="Ba")           # never committed
    config.reset(); aliases.reset()
    assert [p.name for p in repair.retire_aliases(scheme())] == []


def test_no_template_means_no_retirement(tmp_path, monkeypatch):
    from luria import repair
    root = committed_project(tmp_path, monkeypatch, alias="")
    note(root, 41)
    assert repair.retire_aliases(scheme()) == []
