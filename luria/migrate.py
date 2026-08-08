#!/usr/bin/env python3
"""`luria migrate` — execute a migration spec (ADR-040).

    luria migrate 0001                  # run record/migrations.d/0001-*.toml
    luria migrate 0001 --dry-run        # print the plan: mapping, moves, files
    luria migrate 0001 --commit         # run, commit, append blame-ignore

A migration renames a scheme, or moves documents between schemes, without
losing the record's memory. The spec is a TOML file in `record/migrations.d/`
(`luria new migration` scaffolds one) — the executable plan and the audit
trail in one artifact:

    title = "Design principles become guiding principles"
    issue = "#29"

    [[operations]]
    op = "rename_scheme"
    from = "DP"
    to = "GP"
    output = "docs/guiding-principles.md"   # optional: the view moves too
    remotes = ["LU"]                        # remotes that mirror THIS project
    configs = ["template/luria.toml"]       # extra config files to edit

    [[operations]]
    op = "move_doc"
    doc = "DP-4"
    to = "NRM"                              # auto-numbered in the target
    # strategy = "supersede"                # copy + tombstone instead of move

What an operation does, in ADR-040's terms:

- **Addresses, never claims.** The sweep rewrites codes, anchors, filenames
  and view paths — the machinery-authored layer. Prose stays put.
- **Full rewrite, history included.** Every tracked file is swept — journals
  and the changelog too. One spelling tree-wide afterwards; git holds the
  history, and `--commit` appends the migration to `.git-blame-ignore-revs`
  so blame reads through it.
- **Mapping-driven, never prefix-driven.** Only the enumerated pairs are
  rewritten. A fixture number survives by not being in the mapping; a
  composed remote code (`SG-DP-18`) survives because remote spans are
  masked — another project's namespace is theirs. Remotes named in
  `remotes = [...]` are the exception: they mirror this project, so their
  composed codes follow the rename.
- **`formerly:` is identity.** Every moved document is stamped with its old
  code, which is what feeds rung 1: the alias map, the `legacy-spellings`
  warning, and the fixer that modernizes in-flight branches.

The spec file itself and everything else in the migrations directory is
never swept: the spec's mapping is written in old spellings *on purpose* —
it is the one artifact whose job is to remember them.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import aliases as aliases_mod
from . import remotes
from .config import current

MIGRATIONS_DIR = "record/migrations.d"
BLAME_IGNORE = ".git-blame-ignore-revs"


@dataclass(frozen=True)
class Pair:
    old: str                    # canonical old code, e.g. DP-004
    new: str                    # canonical new code, e.g. GP-004

    @property
    def parts(self) -> tuple[str, int, str, int]:
        op, on = aliases_mod.split(self.old)
        np, nn = aliases_mod.split(self.new)
        return op, on, np, nn


@dataclass
class Plan:
    title: str
    mapping: list[Pair] = field(default_factory=list)
    # Composed pairs for remotes that mirror this project: `LU-DP-004` →
    # `LU-GP-004`. Same Pair shape — `split` reads the number off the tail,
    # so `LU-DP` is just a longer prefix.
    composed: list[Pair] = field(default_factory=list)
    path_pairs: list[tuple[str, str]] = field(default_factory=list)
    moves: list[tuple[Path, Path]] = field(default_factory=list)
    stamps: dict[Path, str] = field(default_factory=dict)  # new path → old code
    # (file, old section header, new section header)
    section_renames: list[tuple[Path, str, str]] = field(default_factory=list)
    # Supersede mode: (source path, new status line) + fresh copies to write.
    tombstones: list[tuple[Path, str]] = field(default_factory=list)
    copies: list[tuple[Path, Path, str, str]] = field(default_factory=list)


def _spec_path(ref: str) -> Path:
    """The spec file `ref` names: a path, a filename, or a leading number."""
    cfg = current()
    direct = Path(ref)
    if direct.exists():
        return direct.resolve()
    mig_dir = cfg.root / MIGRATIONS_DIR
    for candidate in (mig_dir / ref, mig_dir / f"{ref}.toml"):
        if candidate.exists():
            return candidate
    matches = sorted(mig_dir.glob(f"{ref}*.toml")) if mig_dir.exists() else []
    if len(matches) == 1:
        return matches[0]
    have = ", ".join(p.name for p in sorted(mig_dir.glob("*.toml"))) \
        if mig_dir.exists() else "none"
    raise SystemExit(f"luria migrate: no spec matches {ref!r} in "
                     f"{MIGRATIONS_DIR}/ (have: {have})")


def _plan_rename(plan: Plan, op: dict) -> None:
    cfg = current()
    old_prefix, new_prefix = op["from"].upper(), op["to"].upper()
    scheme = cfg.schemes.get(old_prefix)
    if scheme is None:
        raise SystemExit(f"luria migrate: no scheme {old_prefix!r} in config")
    if new_prefix in cfg.schemes and op.get("strategy") != "supersede":
        raise SystemExit(f"luria migrate: scheme {new_prefix!r} already exists")

    docs = scheme.documents()
    if op.get("strategy") == "supersede":
        target = cfg.schemes.get(new_prefix)
        if target is None:
            raise SystemExit("luria migrate: strategy=\"supersede\" copies "
                             f"into an existing scheme — add {new_prefix!r} "
                             "to luria.toml first")
        for number, path in docs.items():
            new_code, old_code = target.code(number), scheme.code(number)
            plan.copies.append((path, target.dir / target.filename(number),
                                old_code, new_code))
            plan.tombstones.append(
                (path, f"Superseded — by {new_code}"))
        return

    for number, path in docs.items():
        old_code, new_code = scheme.code(number), f"{new_prefix}-{number:03d}"
        new_path = path.with_name(f"{new_code}.md")
        plan.mapping.append(Pair(old_code, new_code))
        plan.moves.append((path, new_path))
        plan.stamps[new_path] = f"{old_prefix}-{number}"
        for remote_prefix in op.get("remotes", []):
            remote = cfg.remotes.get(remote_prefix.upper())
            delim = remote.delim if remote else "-"
            plan.composed.append(Pair(
                f"{remote_prefix.upper()}{delim}{old_code}",
                f"{remote_prefix.upper()}{delim}{new_code}"))

    configs = [cfg.root / "luria.toml"] + \
        [cfg.root / c for c in op.get("configs", [])]
    for config_file in configs:
        if not config_file.exists():
            raise SystemExit(f"luria migrate: {config_file} not found")
        plan.section_renames.append(
            (config_file, f"[luria.schemes.{old_prefix}]",
             f"[luria.schemes.{new_prefix}]"))
        for remote_prefix in op.get("remotes", []):
            plan.section_renames.append(
                (config_file,
                 f"[luria.remotes.{remote_prefix}.schemes.{old_prefix}]",
                 f"[luria.remotes.{remote_prefix}.schemes.{new_prefix}]"))

    if op.get("output") and scheme.output:
        old_rel = cfg.rel(scheme.output)
        plan.path_pairs.append((old_rel, op["output"]))
        old_name, new_name = Path(old_rel).name, Path(op["output"]).name
        if old_name != new_name and (Path(old_rel).parent
                                     == Path(op["output"]).parent):
            # Relative spellings (`../docs/<name>`) carry only the basename;
            # a same-directory rename swaps it everywhere the full pair
            # wouldn't reach. Never emitted when the directory changes —
            # a bare basename can't say which directory it meant.
            plan.path_pairs.append((old_name, new_name))


def _plan_move(plan: Plan, op: dict) -> None:
    cfg = current()
    old_code = aliases_mod.canon(op["doc"])
    if old_code is None:
        raise SystemExit(f"luria migrate: {op['doc']!r} is not a code")
    old_prefix, number = aliases_mod.split(old_code)
    source = cfg.schemes.get(old_prefix)
    target = cfg.schemes.get(op["to"].upper())
    if source is None or target is None:
        raise SystemExit("luria migrate: move_doc needs both schemes in "
                         f"config (have: {', '.join(cfg.schemes)})")
    path = source.documents().get(number)
    if path is None:
        raise SystemExit(f"luria migrate: {old_code} has no document")
    new_number = max(target.documents(), default=0) + 1
    new_code = target.code(new_number)
    new_path = target.dir / target.filename(new_number)
    if op.get("strategy") == "supersede":
        plan.copies.append((path, new_path, old_code, new_code))
        plan.tombstones.append((path, f"Superseded — by {new_code}"))
        return
    plan.mapping.append(Pair(old_code, new_code))
    plan.moves.append((path, new_path))
    plan.stamps[new_path] = f"{old_prefix}-{number}"


def build_plan(spec: dict, title: str) -> Plan:
    plan = Plan(title=title)
    for op in spec.get("operations", []):
        kind = op.get("op")
        if kind == "rename_scheme":
            _plan_rename(plan, op)
        elif kind == "move_doc":
            _plan_move(plan, op)
        else:
            raise SystemExit(f"luria migrate: unknown op {kind!r} "
                             "(know: rename_scheme, move_doc)")
    return plan


# ── The sweep ────────────────────────────────────────────────────────────


def _tracked_files() -> list[Path]:
    cfg = current()
    out = subprocess.run(["git", "ls-files"], cwd=cfg.root,
                         capture_output=True, text=True, check=True)
    keep = []
    for name in out.stdout.splitlines():
        if name.startswith(MIGRATIONS_DIR):
            continue                     # the spec remembers old spellings
        keep.append(cfg.root / name)
    return keep


def sweep_text(text: str, plan: Plan) -> tuple[str, int]:
    """Every mapped spelling in one text, rewritten. Masks only what the
    mapping doesn't own: composed remote codes (another project's namespace)
    that the spec didn't explicitly claim via `remotes = [...]`."""
    count = 0
    claimed = {p.old for p in plan.composed}

    def masked_spans(text: str) -> list[tuple[int, int]]:
        spans = [(r.start, r.end) for r in remotes.references(text)
                 if r.composed not in claimed]
        # `formerly:` lists are the one place old spellings are the point —
        # they are the record's memory of this very operation, and of every
        # one before it. A later migration sweeping an earlier migration's
        # trail would corrupt exactly what makes aliases derivable.
        spans += [m.span() for m in
                  re.finditer(r"^formerly:\n(?:- .*\n)*", text, re.MULTILINE)]
        return spans

    def swap(text: str, pattern: str, repl) -> str:
        nonlocal count
        spans = masked_spans(text)

        def guarded(m: re.Match) -> str:
            nonlocal count
            if any(a <= m.start() < b for a, b in spans):
                return m.group(0)
            count += 1
            return repl(m) if callable(repl) else repl

        return re.sub(pattern, guarded, text)

    def swap_pair(text: str, pair: Pair) -> str:
        old_p, old_n, new_p, new_n = pair.parts

        def code_repl(m: re.Match) -> str:
            digits = m.group(2)
            new_digits = f"{new_n:03d}" if digits != str(old_n) else str(new_n)
            return f"{new_p}{m.group(1)}{new_digits}"

        text = swap(text,
                    rf"(?<![A-Za-z0-9-]){re.escape(old_p)}([- ])"
                    rf"(0*{old_n})(?!\d)", code_repl)
        return swap(text,
                    rf"(?<=#){re.escape(old_p.lower())}-0*{old_n}(?!\d)",
                    f"{new_p.lower()}-{new_n}")

    # Composed pairs first: `LU-DP-013` must be rewritten whole before the
    # bare-code pattern reads `DP-013` out of the middle of it.
    for pair in plan.composed:
        text = swap_pair(text, pair)
    for pair in plan.mapping:
        text = swap_pair(text, pair)
    for old, new in plan.path_pairs:
        text = swap(text, re.escape(old), new)
    return text, count


def _stamp_formerly(path: Path, old_code: str) -> None:
    """Append `old_code` to the document's `formerly:` list, creating it
    after the opening `---` when absent. Appending, never replacing: a
    document moved twice carries both pasts."""
    text = path.read_text()
    if not text.startswith("---\n"):
        raise SystemExit(f"luria migrate: {path} has no frontmatter to stamp")
    m = re.search(r"^formerly:\n((?:- .*\n)*)", text, flags=re.MULTILINE)
    if m:
        path.write_text(text[:m.end()] + f"- {old_code}\n" + text[m.end():])
    else:
        head, rest = text.split("\n", 1)
        path.write_text(f"{head}\nformerly:\n- {old_code}\n{rest}")


def _git(args: list[str]) -> str:
    out = subprocess.run(["git", *args], cwd=current().root,
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"luria migrate: git {' '.join(args)} failed: "
                         f"{out.stderr.strip()}")
    return out.stdout.strip()


def apply(plan: Plan) -> tuple[int, int]:
    """Execute the plan against the working tree. Returns (files swept,
    rewrites). Everything here is a working-tree edit — committing is the
    caller's (or `--commit`'s) move, so the diff can be read first."""
    cfg = current()

    for old_path, new_path in plan.moves:
        _git(["mv", str(old_path), str(new_path)])
    for new_path, old_code in plan.stamps.items():
        _stamp_formerly(new_path, old_code)
    for source, new_path, old_code, new_code in plan.copies:
        # The fresh copy speaks as the new code; the source keeps saying the
        # old one — it is the tombstone, and its body is history.
        text = source.read_text().replace(old_code, new_code)
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text(text)
    for source, status in plan.tombstones:
        text = source.read_text()
        text = re.sub(r"^status: .*$", f"status: {status}", text,
                      count=1, flags=re.MULTILINE)
        source.write_text(text)
    for config_file, old_header, new_header in plan.section_renames:
        text = config_file.read_text()
        if old_header in text:
            config_file.write_text(text.replace(old_header, new_header))

    files = swept = 0
    if plan.mapping or plan.composed or plan.path_pairs:
        for path in _tracked_files():
            live = path
            for old_path, new_path in plan.moves:
                if path == old_path:
                    live = new_path
            if not live.exists():
                continue
            try:
                text = live.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            new, count = sweep_text(text, plan)
            if count:
                live.write_text(new)
                files += 1
                swept += count
    aliases_mod.reset()
    return files, swept


def describe(plan: Plan) -> list[str]:
    lines = [f"migration: {plan.title}"]
    for pair in plan.mapping:
        lines.append(f"  {pair.old} -> {pair.new}")
    for pair in plan.composed:
        lines.append(f"  {pair.old} -> {pair.new}  (composed)")
    for old, new in plan.path_pairs:
        lines.append(f"  {old} -> {new}  (path)")
    for old_path, new_path in plan.moves:
        lines.append(f"  git mv {current().rel(old_path)} "
                     f"{current().rel(new_path)}")
    for source, new_path, old_code, new_code in plan.copies:
        lines.append(f"  copy {current().rel(source)} -> "
                     f"{current().rel(new_path)}  ({old_code} superseded "
                     f"by {new_code})")
    for config_file, old_header, new_header in plan.section_renames:
        lines.append(f"  {current().rel(config_file)}: {old_header} -> "
                     f"{new_header}")
    return lines


def _blame_ignore(sha: str, title: str) -> None:
    path = current().root / BLAME_IGNORE
    stamp = f"# luria migrate: {title}\n{sha}\n"
    path.write_text((path.read_text() if path.exists() else
                     "# Commits git blame should read through.\n") + stamp)


def run(spec: str, dry_run: bool = False, commit: bool = False) -> None:
    """Execute the migration SPEC (a file in record/migrations.d/, named by
    path, filename or leading number). --dry-run prints the plan; --commit
    commits the result and appends it to .git-blame-ignore-revs."""
    spec_path = _spec_path(str(spec))
    parsed = tomllib.loads(spec_path.read_text())
    title = parsed.get("title") or spec_path.stem
    plan = build_plan(parsed, title)

    if dry_run:
        would = 0
        for path in _tracked_files():
            try:
                _, count = sweep_text(path.read_text(), plan)
            except (UnicodeDecodeError, OSError):
                continue
            would += 1 if count else 0
        for line in describe(plan) + [f"  would sweep {would} file(s)"]:
            print(line)
        return

    files, swept = apply(plan)
    print(f"migrated: {len(plan.moves)} move(s), {len(plan.copies)} "
          f"cop(y/ies), {swept} rewrite(s) in {files} file(s)")

    if commit:
        _git(["add", "-A"])
        _git(["commit", "-m", f"Migration: {title}\n\nExecuted by `luria "
              f"migrate` from {current().rel(spec_path)} (ADR-040)."])
        sha = _git(["rev-parse", "HEAD"])
        _blame_ignore(sha, title)
        _git(["add", BLAME_IGNORE])
        _git(["commit", "-m", f"Blame reads through the {title!r} migration"])
        print(f"committed {sha[:12]} and appended it to {BLAME_IGNORE}")
    else:
        print("next: `luria index`, `luria lint`, review the diff, then "
              "commit — and append the migration commit to "
              f"{BLAME_IGNORE} (or rerun with --commit)")


if __name__ == "__main__":
    import fire
    fire.Fire(run)
