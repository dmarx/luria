# tests/test_store_boundary.py
"""Every source is read and written through `luria/store.py` (#110).

The shape `test_one_reader` holds for parsing, held one layer down for I/O:
a module that opens a path for itself sees the filesystem, and under the
SQLite backend the filesystem is not where the record is. That module would
read an empty directory and report a clean record — the silent kind of
wrong. So no module but the store calls the `Path` methods that touch the
disk; `store.py` names the encoding once and routes by path.
"""
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

DISK = {"read_text", "write_text", "read_bytes", "write_bytes", "glob",
        "rglob", "iterdir", "unlink", "exists", "is_file", "is_dir",
        "stat", "rename", "open"}


def _disk_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute) or fn.attr not in DISK:
            continue
        if isinstance(fn.value, ast.Name) and fn.value.id in ("store", "re",
                                                              "shutil", "os"):
            continue
        if fn.attr == "open" and not isinstance(fn.value, ast.Name):
            continue
        found.append(f"{path.name}:{node.lineno}: .{fn.attr}()")
    return found


def test_only_the_store_touches_the_disk():
    offenders = []
    for path in sorted((REPO / "luria").glob("*.py")):
        if path.name == "store.py":
            continue
        offenders += _disk_calls(path)
    assert not offenders, (
        "these open a path for themselves instead of asking `store`: "
        + ", ".join(offenders))
