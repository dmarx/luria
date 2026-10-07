# tools/wheel_smoke.py
"""Does the built wheel run on its own?

CI's tests run from an editable install, which reads `luria/logic/*.lp`
straight out of the checkout, so passing them says nothing about whether
the wheel carries those files. Without them the installed CLI cannot load a
config: consistency is checked by rules on every load. This takes the
interpreter of an environment the wheel was installed into and checks, from
outside the checkout:

- `luria` is imported from that environment, not from the source tree;
- every `luria/logic/*.lp` in the source tree is in the wheel, readable
  through `importlib.resources` by `logic.rules`, and not empty;
- the installed CLI lints and prints the facts of a copy of an example, once
  with the usual `PATH` and once with git out of reach — 0.36.0 ran without
  git, and a record outside any repository must still read as one.

    python tools/wheel_smoke.py --python VENV/bin/python

Exit 0 means the wheel runs.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "knowledge-base"

PROBE = """
import json, luria
from importlib import resources
from luria import logic
names = sorted(p.name[:-3] for p in resources.files("luria.logic").iterdir()
               if p.name.endswith(".lp"))
read = {n: len(logic.rules(n)) for n in names}
print(json.dumps({"file": luria.__file__, "programs": names, "read": read}))
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--python", required=True,
                        help="the interpreter the wheel was installed into")
    args = parser.parse_args(argv)
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        # Isolated and away from the checkout, so nothing but the installed
        # package can answer the import.
        probe = subprocess.run([args.python, "-I", "-c", PROBE], cwd=tmp,
                               capture_output=True, text=True)
        if probe.returncode:
            print(probe.stderr, file=sys.stderr)
            return 1
        found = json.loads(probe.stdout)
        if Path(found["file"]).resolve().is_relative_to(ROOT):
            problems.append(f"luria imported from the checkout ({found['file']})"
                            f", not the installed wheel")
        expected = sorted(p.stem for p in (ROOT / "luria" / "logic").glob("*.lp"))
        if missing := sorted(set(expected) - set(found["programs"])):
            problems.append(f"the wheel lacks {', '.join(missing)}.lp")
        if empty := sorted(n for n, size in found["read"].items() if not size):
            problems.append(f"empty in the wheel: {', '.join(empty)}")
        record = Path(tmp) / "record"
        shutil.copytree(EXAMPLE, record)
        bin_dir = Path(args.python).parent
        luria = str(bin_dir / "luria")
        paths = {"with git": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
                 "without git": str(bin_dir)}
        for where, path in paths.items():
            for command in (["lint"], ["facts", "scheme", "chain"]):
                done = subprocess.run([luria, *command], cwd=record,
                                      capture_output=True, text=True,
                                      env={"PATH": path, "HOME": tmp,
                                           "LURIA_ROOT": str(record)})
                if done.returncode:
                    problems.append(
                        f"`luria {' '.join(command)}` {where} exited "
                        f"{done.returncode}:\n{done.stdout}{done.stderr}")
    print(f"luria from {found['file']}")
    print(f"programs: {', '.join(found['programs'])}")
    for problem in problems:
        print(f"FAIL: {problem}")
    if not problems:
        print("the wheel runs")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
