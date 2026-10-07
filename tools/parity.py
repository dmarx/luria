# tools/parity.py
"""Byte-for-byte parity between two luria builds on real records.

The logic-core migration (ADR on a logic core in clingo) moves luria's graph
decisions from Python walks to rules, one subsystem at a time. A step is
admissible only if it changes nothing a user sees, or changes exactly the
defect it says it fixes. This is the check: run `luria lint`,
`luria index` and `luria reports` with a baseline build and a candidate build, each on its own
copy of each record, and compare.

    python tools/parity.py --baseline OLD/bin/luria --candidate NEW/bin/luria \\
        RECORD [RECORD ...]

Each record is copied with its `.git`, because the converse fixer reads HEAD
as its baseline. The copy's `luria.yaml` is set to `lint.network: never`, so
both runs answer from the lockfile alone and the comparison cannot depend on
whether arXiv answered. Exit 0 means every record matched.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ruamel.yaml import YAML


def _hermetic(root: Path) -> None:
    """Pin `lint.network: never` in the copy, keeping the file's layout."""
    path = root / "luria.yaml"
    yaml = YAML()
    yaml.preserve_quotes = True
    data = yaml.load(path.read_text(encoding="utf-8"))
    data.setdefault("lint", {})["network"] = "never"
    with path.open("w", encoding="utf-8") as out:
        yaml.dump(data, out)


def _run(luria: str, root: Path, *args: str) -> tuple[int, str]:
    env = {**os.environ, "LURIA_ROOT": str(root), "PYTHONWARNINGS": "ignore"}
    done = subprocess.run([luria, *args], cwd=root, env=env,
                          capture_output=True, text=True)
    text = (done.stdout + done.stderr).replace(str(root), "<root>")
    return done.returncode, text


def _tree(root: Path) -> dict[str, str]:
    """Every file under the copy except git's own, by content hash."""
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            out[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()).hexdigest()
    return out


def _side(luria: str, record: Path, into: Path) -> dict:
    root = into / record.name
    shutil.copytree(record, root, symlinks=True)
    _hermetic(root)
    lint_code, lint_out = _run(luria, root, "lint")
    index_code, index_out = _run(luria, root, "index")
    reports_code, reports_out = _run(luria, root, "reports")
    return {"root": root, "lint": (lint_code, lint_out),
            "index": (index_code, index_out),
            "reports": (reports_code, reports_out), "tree": _tree(root)}


def _diff(a: str, b: str, label: str, limit: int = 40) -> str:
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                      f"baseline {label}", f"candidate {label}",
                                      lineterm="", n=1))
    tail = [f"... {len(lines) - limit} more"] if len(lines) > limit else []
    return "\n".join(lines[:limit] + tail)


def compare(baseline: str, candidate: str, record: Path) -> list[str]:
    """Every way the candidate's output differs from the baseline's."""
    with tempfile.TemporaryDirectory() as tmp:
        old = _side(baseline, record, Path(tmp) / "baseline")
        new = _side(candidate, record, Path(tmp) / "candidate")
        problems = []
        for step in ("lint", "index", "reports"):
            if old[step] != new[step]:
                problems.append(
                    f"`luria {step}` differs (exit {old[step][0]} → "
                    f"{new[step][0]}):\n" + _diff(old[step][1], new[step][1], step))
        for rel in sorted(set(old["tree"]) | set(new["tree"])):
            if old["tree"].get(rel) == new["tree"].get(rel):
                continue
            a = old["root"] / rel
            b = new["root"] / rel
            if not a.exists() or not b.exists():
                problems.append(f"{rel}: written by only the "
                                f"{'candidate' if b.exists() else 'baseline'}")
                continue
            problems.append(f"{rel} differs:\n" + _diff(
                a.read_text(encoding="utf-8", errors="replace"),
                b.read_text(encoding="utf-8", errors="replace"), rel))
        return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = 0
    for record in args.records:
        problems = compare(args.baseline, args.candidate, record.resolve())
        verdict = "identical" if not problems else f"{len(problems)} difference(s)"
        print(f"{record}: {verdict}")
        for problem in problems:
            print("  " + problem.replace("\n", "\n  "))
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
