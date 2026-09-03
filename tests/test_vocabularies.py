"""A frontmatter field backed by a scheme-local controlled vocabulary.

The third instance of a shape the scheme directory already had twice:
`statuses.yaml` behind `status:`, `tags.yaml` behind `tags:`. A downstream
world-building record carries `worlds: [A, C]` on 37 of 75 entries from a
closed six-value set, absent meaning B, with a page per world wanted — not a
reference, not a tag, not a status. Declared explicitly, closed, with a
default that is an effective value and never a rewrite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from luria import adr_index, config, contract, lint, site
from luria.config import current


WORLDS = """\
A:
  label: The unbroken line
  blurb: the trajectory where the treaty holds
B:
  label: The default
  blurb: where most scenes sit
C:
  label: The long winter
"""


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def scene(root: Path, n: int, extra: str = "") -> Path:
    front = ["---", "status: Active", f"title: 'Scene {n}'", "tags:", "- record",
             "date: '2026-01-01'"]
    if extra:
        front.append(extra)
    front += ["---", "", f"# SCENE-{n:03d}: Scene {n}", "", "Body."]
    return write(root, f"record/scenes.d/SCENE-{n:03d}.md", "\n".join(front) + "\n")


def world(tmp_path, monkeypatch, table: str = 'many = true\ndefault = ["B"]',
          vocab: str = WORLDS, name: str = "worlds") -> Path:
    write(tmp_path, "luria.toml", f"""
[luria]
issue_url = "https://example.test/issues/{{n}}"
[luria.schemes.SCENE]
dir = "record/scenes.d"
output = "docs/scenes"
[luria.schemes.SCENE.vocabularies.{name}]
{table}
""")
    if vocab is not None:
        write(tmp_path, f"record/scenes.d/{name}.yaml", vocab)
    write(tmp_path, "docs/README.md", "# Docs\n\n- [Scenes](scenes/README.md)\n"
                                      "- [The record](record.md)\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def field():
    f, = contract.for_scheme(current().schemes["SCENE"]).fields
    return f


# --- declaration ----------------------------------------------------------

def test_a_declared_vocabulary_is_read_with_its_values(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch)
    v, = current().schemes["SCENE"].vocabularies
    assert (v.name, v.many, v.required, v.default) == ("worlds", True, False, ("B",))
    assert v.file == tmp_path / "record/scenes.d/worlds.yaml"
    f = field()
    assert f.vocabulary == "worlds" and f.values == ("A", "B", "C")
    assert f.many and not f.required and f.default == ("B",)


def test_the_defaults_are_one_optional_value_and_no_default(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch, table="")
    v, = current().schemes["SCENE"].vocabularies
    assert (v.many, v.required, v.default) == (False, False, None)


def test_a_vocabulary_with_no_file_is_a_config_error(tmp_path, monkeypatch):
    """Eager, like a tag group that constrains nothing: a declared axis with
    no values would surface as 'no violations', which is the quiet failure."""
    world(tmp_path, monkeypatch, vocab=None)
    with pytest.raises(ValueError, match="no values"):
        current()


def test_a_default_outside_the_vocabulary_is_a_config_error(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch, table='many = true\ndefault = ["Z"]')
    with pytest.raises(ValueError, match="not in"):
        current()


def test_a_default_takes_the_fields_shape(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch, table='default = ["B"]')
    with pytest.raises(ValueError, match="one value"):
        current()
    config.reset()
    world(tmp_path, monkeypatch, table='many = true\ndefault = "B"')
    with pytest.raises(ValueError, match="a list"):
        current()


def test_required_and_default_together_is_a_config_error(tmp_path, monkeypatch):
    """A field with a default is never absent, so `required` says nothing —
    and a key that says nothing reads as though it did."""
    world(tmp_path, monkeypatch, table='required = true\ndefault = "B"')
    with pytest.raises(ValueError, match="never absent"):
        current()


def test_the_built_in_axes_cannot_be_redeclared(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch, name="tags", vocab="a:\n  label: A\n")
    with pytest.raises(ValueError, match="built in"):
        current()


# --- the contract ---------------------------------------------------------

def test_describe_names_the_values_the_default_and_both_files(tmp_path, monkeypatch):
    world(tmp_path, monkeypatch)
    line, = contract.describe(contract.for_scheme(current().schemes["SCENE"]))
    assert "`worlds`" in line and "one or more of `A`, `B`, `C`" in line
    assert "absent means `B`" in line
    assert "schemes.SCENE.vocabularies.worlds" in line
    assert "record/scenes.d/worlds.yaml" in line


def findings() -> list[str]:
    errors: list[str] = []
    lint.check_contracts(errors)
    return errors


def test_a_value_outside_the_vocabulary_is_a_finding(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    scene(root, 1, "worlds:\n- A\n- Z")
    e, = findings()
    assert "`worlds: Z` is not in the `worlds` vocabulary" in e
    assert "record/scenes.d/worlds.yaml" in e


def test_a_list_where_one_value_was_declared_is_a_finding(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch, table="")
    scene(root, 1, "worlds:\n- A\n- B")
    e, = findings()
    assert "holds 2 values" in e and "one `worlds` value" in e


def test_an_absent_field_with_a_default_is_not_a_finding(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    scene(root, 1)
    assert findings() == []


def test_a_required_vocabulary_field_may_not_be_absent(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch, table="many = true\nrequired = true")
    scene(root, 1)
    e, = findings()
    assert "no `worlds:`" in e and "schemes.SCENE.vocabularies.worlds" in e


def test_effective_values_apply_the_default_without_touching_the_source(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    path = scene(root, 1)
    f = field()
    assert contract.effective_values(f, None) == ["B"]
    assert contract.effective_values(f, ["A", "C"]) == ["A", "C"]
    assert "worlds" not in path.read_text()


# --- a page per value ------------------------------------------------------

def rendered(root: Path) -> dict[Path, str]:
    return adr_index.outputs()


def test_the_index_renders_a_page_per_value_beside_the_tag_pages(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    scene(root, 1, "worlds:\n- A\n- C")
    scene(root, 2)
    out = rendered(root)
    pages = {p.relative_to(root).as_posix() for p in out}
    assert {"docs/scenes/worlds/A.md", "docs/scenes/worlds/B.md",
            "docs/scenes/worlds/C.md"} <= pages
    assert "docs/scenes/tags/record.md" in pages


def test_an_absent_field_lists_the_entry_under_the_default(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    scene(root, 1, "worlds:\n- A")
    scene(root, 2)
    out = rendered(root)
    b = out[root / "docs/scenes/worlds/B.md"]
    a = out[root / "docs/scenes/worlds/A.md"]
    assert "SCENE-002" in b and "SCENE-001" not in b
    assert "SCENE-001" in a and "SCENE-002" not in a
    assert "the default" in b.lower()


def test_the_index_links_every_value_and_says_which_is_the_default(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    scene(root, 1, "worlds:\n- A")
    index = rendered(root)[root / "docs/scenes/README.md"]
    assert "(worlds/A.md)" in index and "(worlds/B.md)" in index
    assert "The unbroken line" in index
    assert "default" in index


def test_value_pages_are_generated_views_nobody_has_to_link(tmp_path, monkeypatch):
    """Owned by the generator like the tag pages: a stale one is an orphan,
    and the docs index is not asked to list them one by one."""
    root = world(tmp_path, monkeypatch)
    scene(root, 1, "worlds:\n- A")
    adr_index.run()
    assert root / "docs/scenes/worlds" in adr_index.view_dirs()
    errors: list[str] = []
    lint.check_docs_index(errors)
    lint.check_generated_index(errors)
    assert errors == [], errors
    write(root, "docs/scenes/worlds/Z.md", "# stale\n")
    errors = []
    lint.check_generated_index(errors)
    assert any("Z.md" in e for e in errors), errors


# --- rendered on the site ----------------------------------------------

def test_the_record_line_shows_the_written_values_not_the_default(tmp_path, monkeypatch):
    root = world(tmp_path, monkeypatch)
    path = scene(root, 1, "worlds:\n- A\n- C")
    line = site.record_line({"status": "Active", "worlds": ["A", "C"]}, path)
    assert "**Worlds** [A](../../docs/scenes/worlds/A.md) · [C](../../docs/scenes/worlds/C.md)" in line
    quiet = site.record_line({"status": "Active"}, scene(root, 2))
    assert "Worlds" not in quiet
