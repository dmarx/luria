# tools/config_parity.py
"""Does a candidate build refuse a broken luria.yaml exactly as the baseline does?

`tools/parity.py` compares builds on real records, and a real record's
config is valid, so it never reaches a refusal. This breaks one record's
config in seeded ways — a converse renamed, unrequited or single-valued, a
reference naming an undeclared scheme, an invariant one end cannot hold, a
chain over a missing scheme, field, output or facet — loads each mutant with
both builds, and compares what each raised, word for word.

    python tools/config_parity.py --baseline OLD/bin/python \\
        --candidate NEW/bin/python [--seed 7] [--count 150] [--chains-only] \\
        RECORD [RECORD ...]

Each interpreter must import the build it stands for; it runs isolated
(`-I`), so a checkout in the working directory cannot shadow it. Exit 0 means every
mutant was refused (or accepted) identically.
"""
from __future__ import annotations

import argparse
import copy
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

LOAD = """
import sys
from pathlib import Path
from luria import config
root = Path(sys.argv[1])
for path in sys.argv[2:]:
    try:
        config.load(root, Path(path).read_text())
        print("OK")
    except Exception as e:
        print(type(e).__name__, str(e).replace("\\n", " "))
"""


def _refs(d: dict) -> list[tuple[str, str, dict]]:
    return [(p, f, r) for p, s in d["schemes"].items()
            for f, r in ((s or {}).get("references") or {}).items()
            if isinstance(r, dict)]


def _targets(prefix: str, ref: dict) -> list[str]:
    ts = ref.get("scheme", prefix)
    return ts if isinstance(ts, list) else [ts]


def _mutations(rng: random.Random) -> dict:
    def paired(d):
        return [x for x in _refs(d) if x[2].get("converse")]

    def converse_renamed(d):
        p, f, r = rng.choice(paired(d))
        r["converse"] += "_x"

    def converse_unrequited(d):
        p, f, r = rng.choice(paired(d))
        back = d["schemes"][rng.choice(_targets(p, r))]["references"].get(
            r["converse"])
        if back:
            back.pop("converse", None)

    def converse_elsewhere(d):
        p, f, r = rng.choice(paired(d))
        back = d["schemes"][rng.choice(_targets(p, r))]["references"].get(
            r["converse"])
        others = [s for s in d["schemes"] if s != p]
        if back and others:
            back["scheme"] = rng.choice(others)

    def single(d):
        rng.choice(paired(d))[2]["many"] = False

    def unknown_target(d):
        p, f, r = rng.choice(_refs(d))
        r["scheme"] = rng.choice(["NOPE", _targets(p, r) + ["ZZZ"]])

    def invariant(d):
        rng.choice(_refs(d))[2]["invariant"] = rng.choice(
            ["nosuch", "tags", "status", "title"])

    def chain(d):
        name = rng.choice(list(d["chains"]))
        c = d["chains"][name]
        fields = [f for _, f, _ in _refs(d)]
        key = rng.choice(["scheme", "relation", "relations", "sibling",
                          "facet_by", "output", "invariant"])
        if key == "scheme":
            c["scheme"] = rng.choice(["nope", *d["schemes"]])
        elif key == "relation":
            c["relation"] = rng.choice(["nope", *fields])
        elif key == "relations":
            c["relation"] = [rng.choice(fields), "nope"]
        elif key == "sibling":
            c["sibling"] = rng.choice(["nope", *fields])
        elif key == "facet_by":
            c["facet_by"] = ["status", rng.choice(["nope", "tags"])]
        elif key == "output":
            c.pop("output", None)
        else:
            c["invariant"] = rng.choice(["nope", "tags", "status"])

    return {"schemes": [converse_renamed, converse_unrequited,
                        converse_elsewhere, single, unknown_target, invariant,
                        chain],
            "chains": [chain]}


def mutants(config: Path, seed: int, count: int, chains_only: bool) -> list[str]:
    base = yaml.safe_load(config.read_text(encoding="utf-8"))
    rng = random.Random(seed)
    pool = _mutations(rng)["chains" if chains_only else "schemes"]
    out = []
    for _ in range(count):
        d = copy.deepcopy(base)
        for mutate in rng.sample(pool, min(len(pool), rng.choice([1, 1, 2, 3]))):
            try:
                mutate(d)
            except (IndexError, KeyError, TypeError, AttributeError):
                pass        # this config has nothing that mutation can break
        out.append(yaml.safe_dump(d, sort_keys=False))
    return out


def refusals(python: str, root: Path, texts: list[str]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, text in enumerate(texts):
            path = Path(tmp) / f"{i:04d}.yaml"
            path.write_text(text, encoding="utf-8")
            paths.append(str(path))
        # Isolated, or `-c` puts the working directory on sys.path and a
        # checkout there shadows the build being tested.
        done = subprocess.run([python, "-I", "-c", LOAD, str(root), *paths],
                              capture_output=True, text=True, check=True)
    return done.stdout.splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--count", type=int, default=150)
    parser.add_argument("--chains-only", action="store_true")
    parser.add_argument("records", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = 0
    for record in args.records:
        root = record.resolve()
        texts = mutants(root / "luria.yaml", args.seed, args.count,
                        args.chains_only)
        old = refusals(args.baseline, root, texts)
        new = refusals(args.candidate, root, texts)
        differ = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
        print(f"{record}: {len(texts)} mutants, "
              f"{sum(1 for o in old if o != 'OK')} refused — "
              f"{'identical' if not differ else f'{len(differ)} differ'}")
        for i in differ[:10]:
            print(f"  #{i}\n    baseline:  {old[i]}\n    candidate: {new[i]}")
        failed += bool(differ) or len(old) != len(new)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
