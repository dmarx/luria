# tools/parity.py
"""Byte-for-byte parity between two luria builds on real records.

The logic-core migration (ADR on a logic core in clingo) moves luria's graph
decisions from Python walks to rules, one subsystem at a time. A step is
admissible only if it changes nothing a user sees, or changes exactly the
defect it says it fixes. This is the check: run `luria lint`,
`luria index`, `luria reports`, `luria link` and `luria link --fix` with a
baseline build and a candidate build, each on its own copy of each record,
and compare what they print and every file they leave.

    python tools/parity.py --baseline OLD/bin/luria --candidate NEW/bin/luria \\
        [--perturb SEED] RECORD [RECORD ...]

A record whose relations already agree gives the converse fixer nothing to
do, so `--perturb` gives it work first, the same on both sides: from a
seeded sample of the documents that declare a converse-paired field, one
code is dropped and committed (a one-sided edge nobody touched, which the
fixer completes), and from another sample one is dropped and left
uncommitted (a withdrawal, which the fixer propagates).

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
import random
import re
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


def _paired(root: Path) -> dict[Path, set[str]]:
    """Per scheme directory, the reference fields that declare a converse,
    and the converses they name on the schemes they point at."""
    data = YAML(typ="safe").load((root / "luria.yaml").read_text(encoding="utf-8"))
    schemes = data.get("schemes") or {}
    out: dict[Path, set[str]] = {}
    for prefix, scheme in schemes.items():
        for field, ref in ((scheme or {}).get("references") or {}).items():
            if not isinstance(ref, dict) or not ref.get("converse"):
                continue
            out.setdefault(root / scheme["dir"], set()).add(field)
            far = ref.get("scheme", prefix)
            for target in far if isinstance(far, list) else [far]:
                if target in schemes and "dir" in schemes[target]:
                    out.setdefault(root / schemes[target]["dir"],
                                   set()).add(ref["converse"])
    return out


def _drop_one(path: Path, fields: set[str]) -> bool:
    """Remove the first list item under the first paired field `path`
    declares as a block list. False when it declares none."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        name = line.split(":", 1)[0]
        if name in fields and line.rstrip() == f"{name}:" and \
                i + 1 < len(lines) and re.match(r"- \S", lines[i + 1]):
            del lines[i + 1]
            if not (i + 1 < len(lines) and lines[i + 1].startswith("- ")):
                del lines[i]       # an emptied list goes with its key
            path.write_text("".join(lines), encoding="utf-8")
            return True
    return False


def _perturb(root: Path, seed: int) -> int:
    """Drop one paired code from a seeded sample of documents: a third
    committed, a third left in the working tree. Returns how many."""
    candidates = sorted((path, fields) for d, fields in _paired(root).items()
                        if d.is_dir() for path in d.glob("*.md"))
    rng = random.Random(seed)
    rng.shuffle(candidates)
    third = len(candidates) // 3
    committed = [p for p, f in candidates[:third] if _drop_one(p, f)]
    if committed:
        git = ["git", "-c", "user.name=parity", "-c", "user.email=parity@luria"]
        subprocess.run([*git, "add", *map(str, committed)], cwd=root,
                       check=True, capture_output=True)
        subprocess.run([*git, "commit", "-q", "--no-verify", "-m", "parity"],
                       cwd=root, check=True, capture_output=True)
    pending = [p for p, f in candidates[third:2 * third] if _drop_one(p, f)]
    return len(committed) + len(pending)


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


STEPS = {"lint": ("lint",), "index": ("index",), "reports": ("reports",),
         "link": ("link",), "link --fix": ("link", "--fix")}


def _side(luria: str, record: Path, into: Path, seed: int | None) -> dict:
    root = into / record.name
    shutil.copytree(record, root, symlinks=True)
    _hermetic(root)
    out: dict = {"root": root}
    if seed is not None:
        out["perturbed"] = _perturb(root, seed)
    for step, args in STEPS.items():
        out[step] = _run(luria, root, *args)
    out["tree"] = _tree(root)
    return out


def _diff(a: str, b: str, label: str, limit: int = 40) -> str:
    lines = list(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                      f"baseline {label}", f"candidate {label}",
                                      lineterm="", n=1))
    tail = [f"... {len(lines) - limit} more"] if len(lines) > limit else []
    return "\n".join(lines[:limit] + tail)


def compare(baseline: str, candidate: str, record: Path,
            seed: int | None = None) -> tuple[list[str], int]:
    """Every way the candidate's output differs from the baseline's, and
    how many documents were perturbed first."""
    with tempfile.TemporaryDirectory() as tmp:
        old = _side(baseline, record, Path(tmp) / "baseline", seed)
        new = _side(candidate, record, Path(tmp) / "candidate", seed)
        problems = []
        for step in STEPS:
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
        return problems, old.get("perturbed", 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--perturb", type=int, default=None, metavar="SEED")
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = 0
    for record in args.records:
        problems, perturbed = compare(args.baseline, args.candidate,
                                      record.resolve(), args.perturb)
        verdict = "identical" if not problems else f"{len(problems)} difference(s)"
        extra = f" ({perturbed} perturbed)" if args.perturb is not None else ""
        print(f"{record}{extra}: {verdict}")
        for problem in problems:
            print("  " + problem.replace("\n", "\n  "))
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
