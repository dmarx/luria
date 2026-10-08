# tests/test_writes.py
"""Every write goes through `luria.writes`, and the caches hear of it.

The record's caches key on `stat` — mtime and size — and a rewrite that
keeps the size inside one tick of a coarse clock moves neither. These tests
pin the clock exactly there: each write is followed by `os.utime` putting
the old mtime back, which is what such a filesystem would show. The parity
harness cannot see this, because it runs each command in a fresh process;
the failure needs read, write and read again inside one interpreter.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

from luria import config, logic, relations, writes

from test_relations import note, project

PACKAGE = Path(__file__).resolve().parent.parent / "luria"


def frozen(path: Path, text: str) -> None:
    """Rewrite `path` through the door, then put its mtime back: a write
    the clock did not see."""
    st = path.stat()
    assert len(text.encode()) == st.st_size, "the test needs a same-size edit"
    writes.write_text(path, text)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))


def test_no_module_writes_around_the_door():
    """A `write_text` or `unlink` anywhere but `luria/writes.py` is a write
    the caches never hear of."""
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if path.name == "writes.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("write_text", "write_bytes",
                                           "unlink")
                    and not (isinstance(node.func.value, ast.Name)
                             and node.func.value.id == "writes")):
                found.append(f"{path.relative_to(PACKAGE)}:{node.lineno}")
    assert found == [], "write through luria.writes instead"


def test_a_rewrite_the_clock_misses_still_reaches_the_rules(
        tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    note(root, 2)
    three = note(root, 3, extends=["LIT-001"])
    held = lambda: {(c, x) for s, f, c, x in logic.derive("relations")["held"]
                    if f == "extends"}
    assert held() == {("LIT-003", "LIT-001")}
    # Same length, same mtime, different target.
    frozen(three, three.read_text(encoding="utf-8").replace("- LIT-001",
                                                            "- LIT-002"))
    assert held() == {("LIT-003", "LIT-002")}


def test_a_fixer_reads_back_what_it_just_wrote(tmp_path, monkeypatch):
    """The in-process cycle the caches have to survive: `link --fix`
    completes a pair, and the lint that follows in the same process must
    see it complete, mtimes put back or not. (Completing adds a line, so the
    size moves too; the same-size case is the test above.)"""
    root = project(tmp_path, monkeypatch)
    one = note(root, 1, extended_by=[])
    two = note(root, 2, extends=["LIT-001"])
    stamps = {p: p.stat() for p in (one, two)}
    assert relations.rows(), "one-sided before the fix"
    relations.complete(fix=True)
    for p, st in stamps.items():
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert relations.rows() == []


def test_writing_a_view_leaves_the_facts_alone(tmp_path, monkeypatch):
    """A generated page is not a document, so `luria index` writing a few
    hundred of them does not make the next solve rebuild the facts."""
    root = project(tmp_path, monkeypatch)
    note(root, 1)
    config.current()        # as in any run that writes views
    before = writes.generation()
    (root / "docs").mkdir(exist_ok=True)
    writes.write_text(root / "docs" / "page.md", "# a view\n")
    assert writes.generation() == before
    note_path = root / "record/literature.d/LIT-001.md"
    writes.write_text(note_path, note_path.read_text(encoding="utf-8"))
    assert writes.generation() == before + 1


def test_a_write_never_loads_the_config(tmp_path, monkeypatch):
    """`luria upgrade` rewrites a config that may not load until it has."""
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    writes.write_text(tmp_path / "luria.yaml", "schemes: [not, a, mapping\n")
    assert config.current.cache_info().currsize == 0
