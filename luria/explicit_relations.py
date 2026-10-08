# luria/explicit_relations.py
"""`luria upgrade explicit-relations`: write down the relations older
versions supplied without a declaration (the ADR on explicit relations).

Before it, two relations existed on every scheme whether `luria.yaml` said
so or not:

- **the successor**: `contract.built_in` synthesized a reference named by
  `successor` (default `superseded_by`) into any scheme, required while a
  document's status was `retires_on` (default `Superseded`) and forbidden
  while it was `active`;
- **`influenced_by`**: read as a list of codes on every scheme by the typed
  graph, `luria relate`, `luria new`, the site and the index's "shaped by"
  line.

Now configuration is the only source of relation semantics, so a record
that leaned on either has to say so. This reads the old config — the
roles stripped, since an old config may name a `successor` it never
declared — and every document, then writes into the raw config:

- the roles explicitly (`active`, `retires_on`, `successor`, and
  `influence` where `influenced_by` is used);
- the successor reference, for each scheme whose documents use it or whose
  status vocabulary has the retiring word, with the old conditions;
- `influenced_by`, for each scheme whose documents use it;
- each reference's targets: the narrowest set its existing values support
  — the schemes and remotes they name — or the scheme itself when no
  document has written one yet, said so in the output.

A declaration already present is left as written. A value that names no
declared scheme or remote, or is not a code at all, is refused rather than
guessed at, naming the documents. The result is loaded with the new model
before anything is written.

This is a migration, not a compatibility layer: nothing at run time reads
the old shape.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import writes, yaml_edit
from .config import CONFIG_NAME

OLD_SUCCESSOR, OLD_RETIRES_ON, OLD_ACTIVE = "superseded_by", "Superseded", "Active"
INFLUENCED_BY = "influenced_by"
ROLES = ("successor", "retires_on", "influence")


def successor_reference(targets: list[str], active: str, retires_on: str,
                        words: tuple[str, ...]) -> dict:
    """The declaration `contract.built_in` used to synthesize, written down:
    several codes, never always required, required while retiring and
    forbidden while in force — each condition only where the vocabulary
    holds its word, since a condition that can never hold is refused."""
    spec: dict = {"scheme": targets[0] if len(targets) == 1 else list(targets),
                  "many": True, "required": False}
    if retires_on in words:
        spec["required_when"] = {"status": [retires_on]}
    if active and active != retires_on and active in words:
        spec["forbidden_when"] = {"status": [active]}
    return spec


@dataclass
class Plan:
    """What the upgrade would write, what it noticed, and what stops it."""
    text: str = ""
    changed: bool = False
    notes: list[str] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)


def _values(raw) -> list[str]:
    if raw in (None, "", []):
        return []
    return [str(v).strip() for v in (raw if isinstance(raw, list) else [raw])
            if str(v).strip()]


def _targets(cfg, prefix: str, field_name: str, docs) -> tuple[list[str], list[str]]:
    """The narrowest target set the written values support, and the
    documents whose values support none."""
    from . import remotes as remotes_mod
    from .contract import reference_code
    found: list[str] = []
    bad: list[str] = []
    for doc in docs:
        for value in _values(doc.meta.get(field_name)):
            code = reference_code(value)
            parsed = remotes_mod.parse_code(code) if code else None
            if parsed is not None:
                target = parsed[0].prefix
            elif code and (head := code.rsplit("-", 1)[0]) in cfg.schemes:
                target = head
            else:
                bad.append(f"{cfg.rel(doc.path)}: `{field_name}: {value}`")
                continue
            if target not in found:
                found.append(target)
    # The scheme's own prefix first when present, then the rest in order of
    # first use: the reading order a person would write.
    first_use = {t: i for i, t in enumerate(found)}
    return sorted(found, key=lambda t: (t != prefix, first_use[t])), bad


def plan(root: Path) -> Plan:
    """The upgraded config text for the record at `root`, or why not."""
    from . import config as config_mod
    from .adr_index import load_scheme
    from .statuses import vocabulary
    path = root / CONFIG_NAME
    out = Plan()
    if not path.exists():
        out.refusals.append(f"no {CONFIG_NAME} at {root}")
        return out
    text = path.read_text(encoding="utf-8")
    data = yaml_edit.load(text) or {}
    schemes_raw = data.get("schemes")
    if not schemes_raw:
        # No scheme family declared: the defaults apply, and they declare
        # their relations explicitly now.
        out.text = text
        return out
    # The old config, as the new loader can read it: roles that may name an
    # undeclared reference are stripped, in memory only.
    stripped = copy.deepcopy(yaml_edit.load(text))
    for spec in (stripped.get("schemes") or {}).values():
        for role in ROLES:
            (spec or {}).pop(role, None)
    try:
        config_mod.load(root, text=yaml_edit.dump(stripped))
    except ValueError as exc:
        out.refusals.append(f"the config does not load even with its roles "
                            f"set aside: {exc}")
        return out
    with config_mod.rooted(root, text=yaml_edit.dump(stripped)) as cfg:
        for prefix, spec in schemes_raw.items():
            scheme = cfg.schemes[str(prefix).upper()]
            _scheme(cfg, scheme, spec, load_scheme(scheme),
                    vocabulary(scheme), out)
    if out.refusals or not out.changed:
        out.text = text
        return out
    out.text = _inserted(text, data)
    if _plain(yaml_edit.load(out.text)) != _plain(data):
        out.refusals.append(
            "the additions could not be placed in the file's own text "
            "without changing something else — nothing written; declare "
            "them by hand from `--dry-run`'s notes")
        out.text = text
        return out
    try:
        with config_mod.rooted(root, text=out.text):
            pass
    except ValueError as exc:
        out.refusals.append(f"the upgraded config would not load: {exc}")
    return out


def _scheme(cfg, scheme, spec, docs, words: tuple[str, ...], out: Plan) -> None:
    prefix = scheme.prefix
    references = spec.get("references")
    declared = set(references or {})
    successor = str(spec.get("successor") or OLD_SUCCESSOR)
    retires_on = str(spec.get("retires_on") or OLD_RETIRES_ON)
    active = str(spec.get("active") or OLD_ACTIVE)

    def ensure_references():
        nonlocal references
        if references is None:
            yaml_edit.set_block(spec, "references", {})
            references = spec["references"]
        return references

    # The successor: relied on when a document names one, or when the
    # vocabulary holds the word that used to demand one.
    uses = any(_values(d.meta.get(successor)) for d in docs)
    if successor in declared or uses or retires_on in words:
        for key, value in (("active", active), ("retires_on", retires_on),
                           ("successor", successor)):
            if spec.get(key) != value:
                spec[key] = value
                out.changed = True
        if successor not in declared:
            targets, bad = _targets(cfg, prefix, successor, docs)
            if bad:
                out.refusals += [f"{b} — not a code of a scheme or remote "
                                 f"this record declares" for b in bad]
                return
            if not targets:
                targets = [prefix]
                out.notes.append(
                    f"{prefix}.{successor}: no document names a successor "
                    f"yet, so it is declared as {prefix} — add schemes or "
                    f"remotes to `scheme:` if replacements may live elsewhere")
            else:
                out.notes.append(f"{prefix}.{successor}: declared as "
                                 f"{', '.join(targets)}, from the values "
                                 f"written")
            ensure_references()[successor] = successor_reference(
                targets, active, retires_on, words)
            out.changed = True
    # `influenced_by`: declared only where a document uses it.
    if any(_values(d.meta.get(INFLUENCED_BY)) for d in docs):
        if INFLUENCED_BY not in declared:
            targets, bad = _targets(cfg, prefix, INFLUENCED_BY, docs)
            if bad:
                out.refusals += [f"{b} — not a code of a scheme or remote "
                                 f"this record declares" for b in bad]
                return
            ensure_references()[INFLUENCED_BY] = {
                "scheme": targets[0] if len(targets) == 1 else targets,
                "many": True, "required": False}
            out.notes.append(f"{prefix}.{INFLUENCED_BY}: declared as "
                             f"{', '.join(targets)}, from the values written")
            out.changed = True
        if not spec.get("influence"):
            spec["influence"] = INFLUENCED_BY
            out.changed = True


def _plain(data):
    """A loaded document as plain dicts and lists, for comparing meaning."""
    return json.loads(json.dumps(data, default=str))


def _inserted(text: str, data) -> str:
    """`text` with every key the upgrade added to `data` written in at the end
    of its parent's block, and nothing else touched.

    Re-emitting the whole document would rewrap long strings and requote
    values the person wrote (`yaml_edit` emits one shape, and a record need
    not be written in it), so a migration that only adds keys adds lines.
    Two levels receive additions: a scheme (its roles, or a `references:`
    table it lacked) and an existing `references:` table (a new entry)."""
    original = yaml_edit.load(text)
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    placed = []                               # (line, depth, rendered text)
    old_schemes = original.get("schemes") or {}
    for prefix, spec in (data.get("schemes") or {}).items():
        before = old_schemes.get(prefix) or {}
        parents = [(("schemes", str(prefix)),
                    {k: v for k, v in spec.items() if k not in before})]
        if "references" in before:
            old_refs = before.get("references") or {}
            parents.append(((("schemes", str(prefix), "references")),
                            {k: v for k, v in (spec.get("references") or {}).items()
                             if k not in old_refs}))
        for path, added in parents:
            if not added:
                continue
            start, end = yaml_edit.span(original, path)
            end = len(lines) if end is None else end
            # Comments and blank lines just above the next entry are that
            # entry's, so the block ends before them.
            while end - 1 > start and (not lines[end - 1].strip() or
                                       lines[end - 1].lstrip().startswith("#")):
                end -= 1
            column = min(col for here, _, col in yaml_edit.keys(original)
                         if here[:-1] == path)
            block = yaml_edit.dump(_plain(added))
            indent = " " * column
            rendered = "".join(indent + line if line.strip() else line
                               for line in block.splitlines(keepends=True))
            placed.append((end, len(path), rendered))
    # Bottom-up, so earlier line numbers stay true; at one line, the
    # shallower block first, so a deeper one lands above it — inside the
    # table it belongs to.
    for end, _, rendered in sorted(placed, key=lambda p: (-p[0], p[1])):
        lines.insert(end, rendered)
    return "".join(lines)


def pending(root: Path) -> bool:
    """Whether the record at `root` still has something to write down."""
    try:
        found = plan(root)
    except Exception:
        return False
    return found.changed and not found.refusals


def run(root: Path, dry_run: bool) -> None:
    found = plan(root)
    for note in found.notes:
        print(f"  {note}")
    if found.refusals:
        raise SystemExit(
            "luria upgrade explicit-relations: refused, nothing written —\n  "
            + "\n  ".join(found.refusals))
    if not found.changed:
        print("explicit-relations: nothing to do — every relation this record "
              "uses is declared")
        return
    if dry_run:
        print(f"  would write {CONFIG_NAME}")
        return
    writes.write_text(root / CONFIG_NAME, found.text)
    print(f"  wrote {CONFIG_NAME}")
