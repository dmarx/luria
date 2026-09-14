"""TOML config + per-scheme vocabulary files -> one luria.yaml.

The hazard this owns is escaping: `uid = "(\\d{4})[.:](\\d{4,5})"` does not
survive TOML -> YAML by copying bytes. Parsing with tomllib and dumping with
yaml means every value is re-encoded by a writer that knows its own rules,
which is the only version of this that is safe."""
from __future__ import annotations

import tomllib

import yaml

from pathlib import Path

def convert(root: Path) -> str:
    cfg_path = root / "luria.yaml"
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    cfg = cfg.get("luria", cfg)
    vocabs, by_text, notes = {}, {}, []
    for prefix, spec in (cfg.get("schemes") or {}).items():
        d = root / spec["dir"]
        for kind in ("tags", "statuses"):
            f = d / f"{kind}.yaml"
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            if text in by_text:
                spec[kind] = by_text[text]
                notes.append(f"  {prefix}.{kind} -> {by_text[text]} (shared)")
                continue
            name = f"{prefix.lower()}-{kind}"
            vocabs[name] = yaml.safe_load(text) or {}
            by_text[text] = name
            spec[kind] = name
            notes.append(f"  {prefix}.{kind} -> {name}")
    # A field's `vocabulary` named a file stem beside the records.
    for prefix, spec in (cfg.get("schemes") or {}).items():
        for fspec in (spec.get("fields") or {}).values():
            v = fspec.get("vocabulary")
            if v in ("tags", "statuses") and spec.get(v):
                fspec["vocabulary"] = spec[v]
            elif v and v not in vocabs:
                f = root / spec["dir"] / f"{v}.yaml"
                if f.exists():
                    vocabs[v] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                    notes.append(f"  {prefix}.fields vocabulary {v} -> {v}")
    out = {"vocabularies": vocabs, **cfg} if vocabs else cfg
    (root / "luria.yaml").write_text(
        yaml.dump(out, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8")
    return "\n".join(notes)

def run(root: str | Path = ".") -> str:
    """Convert one record in place. Leaves the TOML alone: deleting the thing
    you just converted, before anyone has looked at the result, is not a
    migration anybody should have to trust."""
    return convert(Path(root))
