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
    from = "OLD"
    to = "NEW"
    output = "docs/guiding-principles.md"   # optional: the view moves too
    remotes = ["LU"]                        # remotes that mirror THIS project
    configs = ["template/luria.toml"]       # extra config files to edit

    [[operations]]
    op = "move_doc"
    doc = "OLD-4"
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

# unresolved-ok-file: DP-017 — a demonstration code in the comments below,
# standing in for a moved document's old address

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import aliases as aliases_mod
from . import doc_refs, new as new_mod, remotes
from .config import current, is_temp_tail

MIGRATIONS_DIR = "record/migrations.d"
BLAME_IGNORE = ".git-blame-ignore-revs"


@dataclass(frozen=True)
class Pair:
    old: str                    # canonical old code, e.g. OLD-004
    new: str                    # canonical new code, e.g. NEW-004

    @property
    def old_parts(self) -> tuple[str, int]:
        """Prefix and number. The old side is always numeric: a document that
        never had a number has nothing to migrate away from."""
        return aliases_mod.split(self.old)

    @property
    def new_parts(self) -> tuple[str, str]:
        """Prefix and the LITERAL new tail — `004`, or `tmp47fje`.

        A string either way. The two spellings do not share a type: one is a
        number carrying a padding convention, the other is an opaque identity
        (ADR-049). An earlier `int | str` union pushed the ambiguity out to
        every call site, which then had to test the type to learn which it
        had — and the padding branch and the provisional branch are not the
        same question."""
        prefix, tail = self.new.rsplit("-", 1)
        return prefix, tail

    @property
    def new_is_provisional(self) -> bool:
        """A temporary code, awaiting `luria concretize`."""
        return is_temp_tail(self.new_parts[1])

    @property
    def new_anchor_tail(self) -> str:
        """How the tail is spelled inside an anchor: `#gp-4`, `#gp-tmp47fje`.

        Anchors never pad — the generator emits the bare number — so a
        numeric tail normalizes through `int` and a provisional one passes
        through untouched."""
        tail = self.new_parts[1]
        return tail if self.new_is_provisional else str(int(tail))


@dataclass
class Plan:
    title: str
    mapping: list[Pair] = field(default_factory=list)
    # Composed pairs for remotes that mirror this project: `LU-OLD-004` →
    # `LU-NEW-004`. Same Pair shape — `split` reads the number off the tail,
    # so `LU-OLD` is just a longer prefix.
    composed: list[Pair] = field(default_factory=list)
    path_pairs: list[tuple[str, str]] = field(default_factory=list)
    moves: list[tuple[Path, Path]] = field(default_factory=list)
    stamps: dict[Path, str] = field(default_factory=dict)  # new path → old code
    # Generated views whose address moves: the old file is removed and the
    # next `luria index` writes the new one — a generated file is never
    # renamed, it is re-derived.
    removals: list[Path] = field(default_factory=list)
    # (file, old section header, new section header)
    section_renames: list[tuple[Path, str, str]] = field(default_factory=list)
    # Config files that get the section-aware path pass instead of the
    # blanket path sweep — a remote's `document =` line spells *its* path.
    config_files: list[Path] = field(default_factory=list)
    claimed_remotes: list[str] = field(default_factory=list)
    # Supersede mode: (source path, new status line) + fresh copies to write.
    tombstones: list[tuple[Path, str]] = field(default_factory=list)
    copies: list[tuple[Path, Path, str, str]] = field(default_factory=list)
    # Temporary tails this plan has already minted, per target prefix, so a
    # second mint in the same run cannot repeat one — `_mint_tail` can only
    # see what is on disk, and nothing has been written yet.
    minted: dict[str, set[str]] = field(default_factory=dict)
    # New codes whose citations must be REBUILT rather than re-spelled. Every
    # `move_doc` qualifies, because a move always crosses schemes and a
    # scheme's address is more than its code:
    #
    #   same render mode  — the directory changes (`src.d/X.md` → `dst.d/Y.md`)
    #   different modes   — the whole shape changes (`page.md#anchor` ↔ `dir/Y.md`)
    #
    # Swapping the code inside the old link fixes the label and leaves the
    # target pointing at a file that does not exist. So the sweep strips these
    # links back to bare references and the fixer rebuilds them from the
    # resolver, which is the one place that knows how a scheme is addressed.
    relocated: set[str] = field(default_factory=set)
    # Old address fragment → the code that answers for it now. The address is
    # the anchor a document-rendered scheme gave the document (`#dp-17`) or the
    # filename an index-rendered one did (`DP-017.md`), so a citation is found
    # by where it POINTS rather than by how it is labelled.
    old_addresses: dict[str, str] = field(default_factory=dict)


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
    plan.claimed_remotes += [r.upper() for r in op.get("remotes", [])]
    for config_file in configs:
        if not config_file.exists():
            raise SystemExit(f"luria migrate: {config_file} not found")
        plan.config_files.append(config_file)
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
        plan.removals.append(scheme.output)
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
    # A moved document arrives under a TEMPORARY code, never a number
    # (ADR-049). Every operation in a spec plans against the tree as it is
    # now — nothing has moved yet — so "the next free number" is not a fact
    # here any more than it is on a branch: two moves into one scheme both
    # read the same highest number, and the second `git mv` would overwrite
    # the first. The concretizer assigns the real numbers afterwards, at the
    # serialization point, which is the only place that answer is true. It
    # also stamps `formerly:`, so the alias the move needs comes for free.
    seen = plan.minted.setdefault(target.prefix, set())
    while (tail := new_mod._mint_tail(target)) in seen:
        pass
    seen.add(tail)
    new_code = f"{target.prefix}-{tail}"
    new_path = target.dir / f"{new_code}.md"
    if op.get("strategy") == "supersede":
        plan.copies.append((path, new_path, old_code, new_code))
        plan.tombstones.append((path, f"Superseded — by {new_code}"))
        return
    plan.relocated.add(new_code)
    plan.old_addresses[
        f"#{old_prefix.lower()}-{number}" if source.render == "document"
        else path.name] = new_code
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


URL_RE = re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s<>)\]\"']+", re.IGNORECASE)


def sweep_text(text: str, plan: Plan, paths: bool = True,
               source: Path = doc_refs.ANY_MD) -> tuple[str, int]:
    """Every mapped spelling in one text, rewritten. Masks only what the
    mapping doesn't own: composed remote codes (another project's namespace)
    that the spec didn't explicitly claim via `remotes = [...]`, URLs for
    the path pairs (a foreign repo can host a file by the same name), and
    every `formerly:` block."""
    count = 0
    claimed = {p.old for p in plan.composed}

    def masked_spans(text: str, mask_urls: bool = False) -> list[tuple[int, int]]:
        spans = [(r.start, r.end) for r in remotes.references(text)
                 if r.composed not in claimed]
        # `formerly:` lists are the one place old spellings are the point —
        # they are the record's memory of this very operation, and of every
        # one before it. A later migration sweeping an earlier migration's
        # trail would corrupt exactly what makes aliases derivable.
        spans += [m.span() for m in doc_refs.FORMERLY_RE.finditer(text)]
        if mask_urls:
            spans += [m.span() for m in URL_RE.finditer(text)]
        return spans

    def swap(text: str, pattern: str, repl, mask_urls: bool = False) -> str:
        nonlocal count
        spans = masked_spans(text, mask_urls)

        def guarded(m: re.Match) -> str:
            nonlocal count
            if any(a <= m.start() < b for a, b in spans):
                return m.group(0)
            count += 1
            return repl(m) if callable(repl) else repl

        return re.sub(pattern, guarded, text)

    def swap_pair(text: str, pair: Pair) -> str:
        old_p, old_n = pair.old_parts
        new_p, new_tail = pair.new_parts

        def code_repl(m: re.Match) -> str:
            sep, digits = m.group(1), m.group(2)
            if pair.new_is_provisional:
                # A temporary tail has no padded form to preserve; the
                # concretizer rewrites it to a number later, everywhere.
                return f"{new_p}{sep}{new_tail}"
            # Otherwise mirror the spelling the citation used: a padded
            # reference stays padded, a bare one stays bare.
            number = int(new_tail)
            spelled = f"{number:03d}" if digits != str(old_n) else str(number)
            return f"{new_p}{sep}{spelled}"

        text = swap(text,
                    rf"(?<![A-Za-z0-9-]){re.escape(old_p)}([- ])"
                    rf"(0*{old_n})(?!\d)", code_repl)
        if pair.new in plan.relocated:
            # The document MOVED, so its address is rebuilt below rather than
            # re-spelled here. Rewriting the anchor now would bury the old
            # address under the new code and leave nothing to match on.
            return text
        # The two spellings of a machinery-authored anchor: the `#gp-4` a
        # link target carries, and the `name="gp-4"` the render emits.
        text = swap(text,
                    rf"(?<=#){re.escape(old_p.lower())}-0*{old_n}(?!\d)",
                    f"{new_p.lower()}-{pair.new_anchor_tail}")
        return swap(text,
                    rf"(?<=name=\"){re.escape(old_p.lower())}-0*{old_n}(?=\")",
                    f"{new_p.lower()}-{pair.new_anchor_tail}")

    def unlink_relocated(text: str) -> str:
        """Any link AT a moved document's old address loses its target.

        Matched on the ADDRESS, not the label: a citation may be worded
        (`[design-principles #17](../design-principles.md#dp-17)`) rather than
        spelled as the code, and those are exactly the ones a code-shaped
        pattern walks past — leaving a live link to a document that moved.

        The whole citation — label included — becomes the NEW CODE, bare, and
        the fixer links it. Keeping the old label was the first attempt and it
        undid itself: `[design-principles #17](…#dp-17)` stripped to
        `design-principles #17`, whose bare `#17` the resolver reads as a
        design-principle reference and re-linked straight back to the anchor
        that had just been vacated. A stale label is not worth preserving at
        the cost of resurrecting the address it names."""
        for old_addr, new_code in sorted(plan.old_addresses.items()):
            text = swap(
                text,
                rf"\[[^\]]*\]\([^)]*{re.escape(old_addr)}\)",
                new_code)
        return text

    def respell_relocated(text: str) -> str:
        """A citation WORDED rather than spelled — `design-principles #17` in
        a code comment — names a moved document as surely as `DP-017` does,
        and both the code swap and the address swap walk straight past it: it
        contains no code, and (unlinked) it points at no address.

        The recognizer is the one the fixer already uses, so the two can't
        disagree about what counts as a reference — `find_refs` is what turns
        `design-principles #17` into a link in the first place. Only
        *relocated* documents are respelled, and only the prose spellings: a
        citation that already spells the code belongs to `swap_pair`, which
        knows how to mirror padding."""
        targets: dict[tuple[str, int], Pair] = {
            (pair.old_parts[0].upper(), pair.old_parts[1]): pair
            for pair in plan.mapping if pair.new in plan.relocated}
        if not targets:
            return text
        out, cursor = [], 0
        for ref in doc_refs.find_refs(text, source):
            if ref.kind != "scheme" or ref.code:
                continue
            pair = targets.get((ref.prefix.upper(), ref.num))
            if pair is None:
                continue
            prefix, number = pair.old_parts
            if re.fullmatch(rf"{re.escape(prefix)}[- ]0*{number}",
                            ref.text, re.IGNORECASE):
                continue                 # a code spelling; swap_pair's job
            out.append(text[cursor:ref.start])
            out.append(pair.new)
            cursor = ref.end
            nonlocal count
            count += 1
        out.append(text[cursor:])
        return "".join(out)

    # Before any swapping: a moved document's citations are matched by the
    # address they point at, and the code swap rewrites codes inside link
    # targets too — so running this later would leave nothing to match.
    text = unlink_relocated(text)
    text = respell_relocated(text)

    # Composed pairs first: `LU-OLD-013` must be rewritten whole before the
    # bare-code pattern reads `OLD-013` out of the middle of it.
    for pair in plan.composed:
        text = swap_pair(text, pair)
    for pair in plan.mapping:
        text = swap_pair(text, pair)
    if paths:
        for old, new in plan.path_pairs:
            text = swap(text, re.escape(old), new, mask_urls=True)
    return text, count


SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")


def config_paths_pass(text: str, plan: Plan) -> str:
    """Path pairs in a config file, section-aware: a remote's `document =`
    line spells *that project's* path, which only moves if the spec claimed
    the remote via `remotes = [...]`. Everything outside unclaimed remote
    sections — the scheme's `output`, the `[luria.paths]` values, comments —
    follows the rename."""
    out = []
    section = ""
    for line in text.splitlines(keepends=True):
        if m := SECTION_RE.match(line):
            section = m.group(1)
        frozen = False
        if m2 := re.match(r"(?:luria\.)?remotes\.([A-Za-z0-9]+)", section):
            frozen = m2.group(1).upper() not in plan.claimed_remotes
        if not frozen:
            for old, new in plan.path_pairs:
                line = line.replace(old, new)
        out.append(line)
    return "".join(out)


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
    for config_file in plan.config_files:
        config_file.write_text(
            config_paths_pass(config_file.read_text(), plan))
    for stale_view in plan.removals:
        if stale_view.exists():
            _git(["rm", "-q", str(stale_view)])

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
            # `unlinted-file` declares every reference in the file a quote,
            # not a claim (#37) — and a quote is a specimen the sweep must
            # not modernize. The migration test suite is the proof case: it
            # is *made of* deliberate old spellings.
            if doc_refs.unlinted(live, text):
                continue
            new, count = sweep_text(text, plan,
                                    paths=live not in plan.config_files,
                                    source=live)
            if count:
                live.write_text(new)
                files += 1
                swept += count
    aliases_mod.reset()

    # Rebuild the links the sweep dropped to bare references. Deliberately
    # AFTER the moves and the alias reset, so the resolver sees the tree as it
    # now is: a cross-render move changes how a document is addressed, and the
    # resolver is the one place that knows how. Doing it here rather than
    # leaving it to a follow-up `luria link --fix` keeps the migration's
    # output clean on its own terms — a run that ends with dangling bare refs
    # is a run that half-finished.
    #
    # Over `doc_files()`, which is `luria link`'s own file set — NOT the
    # tracked files the sweep walks. The two passes ask different questions.
    # The sweep asks "does this text spell a code that moved?", which a source
    # file answers as truthfully as a document does. Linking asks "should this
    # reference be a hyperlink?", and for a `.ts` comment or a workflow YAML
    # the answer is no: they are exempt from the hyperlink lint because code
    # is quoted, not asserted. Running the fixer wider than the linter checks
    # is how one migration rewrote 469 files nobody had asked it to touch,
    # burying two moved documents in a diff of markdown links inside Python
    # comments (#90).
    if plan.relocated:
        adrs, anchors = doc_refs.adr_paths(), doc_refs.dp_anchors()
        for path in doc_refs.doc_files():
            if not path.exists():
                continue
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if doc_refs.unlinted(path, text):
                continue
            linked, n = doc_refs.linkify(text, path, adrs, anchors)
            if n:
                path.write_text(linked)
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
                _, count = sweep_text(path.read_text(), plan,
                                      source=path)
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
