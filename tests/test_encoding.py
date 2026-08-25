"""Files are UTF-8 by construction; the console is the platform's.

A Windows terminal at cp1252 could not encode the arrow in `luria init → path`
and could not write the check mark a status report ends on, so a scaffold
became a stack trace on a machine where nothing was wrong (#112). Worse, the
two halves disagreed: files written under cp1252 were then unreadable to the
same tool run with `PYTHONUTF8=1`.

The split this pins: **every file is UTF-8, always** — a record is portable or
it is not a record — while the console keeps its own encoding and only stops
raising. Writing UTF-8 at a cp1252 console would trade a crash for mojibake.
"""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "luria"
IO_METHODS = {"read_text", "write_text"}


def bare_io_calls(path: Path) -> list[str]:
    """`x.read_text()` / `x.write_text(...)` with no `encoding=`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute) or fn.attr not in IO_METHODS:
            continue
        if any(kw.arg == "encoding" for kw in node.keywords):
            continue
        found.append(f"{path.name}:{node.lineno}: {fn.attr}()")
    return found


def test_no_file_io_in_the_package_depends_on_the_locale():
    """The structural half. `Path.read_text()` with no encoding uses whatever
    the platform prefers, which is cp1252 on a default Windows install and
    ASCII under `LC_ALL=C` — so the default is a portability bug wherever the
    record contains an em dash, and this record's prose is full of them."""
    bare = [hit for f in sorted(PACKAGE.rglob("*.py")) for hit in bare_io_calls(f)]
    assert bare == [], "file I/O without an explicit encoding"


def test_a_generated_view_is_utf_8_whatever_the_console_is(tmp_path):
    """The behavioural half, run the way the bug arrived: a full scaffold and
    build under an ASCII locale, in a subprocess, because the interpreter
    settles its encodings at startup and no fixture can undo that."""
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C",
           "PYTHONUTF8": "0", "LURIA_ROOT": str(tmp_path),
           "HOME": str(tmp_path)}
    def run(*args):
        return subprocess.run([sys.executable, "-m", "luria.cli", *args],
                              cwd=tmp_path, env=env, capture_output=True,
                              text=True)

    assert run("init").returncode == 0, "init crashed under an ASCII locale"
    assert run("index").returncode == 0, "index crashed under an ASCII locale"
    assert run("lint").returncode == 0

    report = tmp_path / "docs" / "reports" / "reference-status.md"
    assert report.exists()
    # Decodes as UTF-8 — and contains something ASCII could not have written.
    text = report.read_text(encoding="utf-8")
    assert "✅" in text


def test_the_console_degrades_rather_than_raising(tmp_path):
    """`luria init` prints an arrow. Under a console that cannot encode one
    the line still has to arrive, because the alternative is a traceback in
    place of a scaffold."""
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C",
           "PYTHONUTF8": "0", "LURIA_ROOT": str(tmp_path),
           "HOME": str(tmp_path)}
    done = subprocess.run([sys.executable, "-m", "luria.cli", "init"],
                          cwd=tmp_path, env=env, capture_output=True, text=True)
    assert done.returncode == 0
    assert "Traceback" not in done.stderr
    assert "luria init" in done.stdout
