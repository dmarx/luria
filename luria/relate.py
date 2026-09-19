#!/usr/bin/env python3
"""`luria relate SOURCE FIELD TARGET` — write a relation into an existing
document's frontmatter (#304).

    luria relate ADR-245 influenced_by ADR-231
    luria relate SOTA-113 extends SOTA-105
    luria relate --draft drafts.json     # every entry of the file's `relations`

A relation between two documents that already exist is an edit to one of
their frontmatters, and until now nothing but an editor could make it. The
canvas half of this (strata-g's Draw tool, dropping one filed document onto
another) hands the relation over as data — source, field, target, by code —
and this is the command that files it. Same posture as `luria new --draft`:
the tool authors intent, luria authors the file.

What is accepted is what the record can check. The field is one the
document's scheme reads as a reference — `influenced_by`, the successor
field, or a field the scheme declares in `references:` — and the target is a
code that resolves. A prose mention (`cites`) is not a field, and an
unresolvable code is refused rather than written, because a relation nobody
can follow is exactly the finding the lint exists to raise.

The edit is `field_edit`'s: one line, the form's comments untouched. A
declared converse stays `luria repair`'s to complete, as it is for every
other one-sided relation; the command says so when it applies.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .adr_index import parse_frontmatter
from .config import current
from .contract import ANY_SCHEME, Field, for_scheme, is_remote, local_scheme
from .field_edit import add_to_field
from .referents import path_of

# Standard frontmatter every scheme reads as a relation without declaring
# it (edges.py): a list of the documents this one follows from.
INFLUENCED_BY = "influenced_by"


@dataclass(frozen=True)
class Related:
    path: Path
    field: str
    target: str
    # "added" when the file changed, "present" when the relation was
    # already written — a second run is a report, not a duplicate.
    outcome: str
    # What the reader should know next: a converse to complete, a status
    # the successor field implies. Empty when there is nothing to say.
    notes: tuple[str, ...] = ()


def relatable_fields(scheme) -> dict[str, Field]:
    """The fields of this scheme a relation can be written into: every
    contract field that names a document, plus `influenced_by`, which the
    index and the typed-edge module read on every scheme without a
    declaration."""
    fields = {f.name: f for f in for_scheme(scheme).fields if f.reference is not None}
    fields.setdefault(INFLUENCED_BY, Field(INFLUENCED_BY, required=False,
                                           reference=ANY_SCHEME, many=True))
    return fields


def _scheme_of(code: str):
    prefix = local_scheme(code)
    return current().schemes.get(prefix) if prefix else None


def _check_target(field: Field, target: str, where: str) -> None:
    """A target the record can follow, or an exit that says why not."""
    if is_remote(target):
        if field.reference == ANY_SCHEME:
            return  # a citation the remote machinery verifies (ADR-016)
        sys.exit(f"{where}: {field.name} names a {field.reference} document, "
                 f"and {target} is a remote code")
    if field.reference != ANY_SCHEME and not target.startswith(f"{field.reference}-"):
        sys.exit(f"{where}: {field.name} names a {field.reference} document, "
                 f"not {target}")
    if _scheme_of(target) is None or path_of(target) is None:
        sys.exit(f"{where}: {target} resolves to no document in this record")


def _listed(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value]
    return [str(value).strip()]


def relate(source: str, field: str, target: str) -> Related:
    """Write `target` into `field` of the document `source` names."""
    source, field, target = source.strip(), field.strip(), target.strip()
    where = f"luria relate {source} {field} {target}"
    path = path_of(source)
    scheme = _scheme_of(source)
    if path is None or scheme is None:
        sys.exit(f"{where}: {source} resolves to no document in this record")
    fields = relatable_fields(scheme)
    if field not in fields:
        sys.exit(f"{where}: {field!r} is not a relation of {scheme.prefix} "
                 f"(this scheme relates through: {', '.join(sorted(fields))})")
    spec = fields[field]
    if target == source:
        sys.exit(f"{where}: a document cannot relate to itself")
    _check_target(spec, target, where)

    text = path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(text)
    held = _listed(meta.get(field))
    notes = []
    if field == scheme.successor and str(meta.get("status", "")).strip() != scheme.retires_on:
        notes.append(f"status is {str(meta.get('status', '')).strip()!r}, and "
                     f"{field} is what a {scheme.retires_on} document names — "
                     f"set the status, or the lint will ask")
    converse = next((r.converse for r in scheme.references
                     if r.field == field and getattr(r, "converse", "")), "")
    if converse and converse != field:
        notes.append(f"`luria repair` writes the converse ({converse}) on {target}")

    if target in held:
        return Related(path, field, target, "present", tuple(notes))
    if not spec.many and held:
        sys.exit(f"{where}: {field} holds one document and already names "
                 f"{held[0]}; edit the file to replace it")
    if spec.many:
        text = add_to_field(text, field, target)
    else:
        from .new import _sub_line
        text = _sub_line(text, field, target)
    path.write_text(text, encoding="utf-8")
    return Related(path, field, target, "added", tuple(notes))


def _read_relations(draft: str) -> list[dict]:
    import json
    try:
        data = json.loads(Path(draft).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"luria relate: no such file {draft!r}")
    except json.JSONDecodeError as e:
        sys.exit(f"luria relate: {draft} is not JSON ({e})")
    relations = data.get("relations") if isinstance(data, dict) else None
    if not isinstance(relations, list):
        sys.exit(f"luria relate: {draft} carries no `relations` list")
    for i, r in enumerate(relations, 1):
        if not isinstance(r, dict) or not all(isinstance(r.get(k), str) and r[k]
                                              for k in ("source", "field", "target")):
            sys.exit(f"luria relate: relation {i} in {draft} needs source, "
                     "field and target")
    return relations


def _say(done: Related) -> None:
    rel = current().rel(done.path)
    verb = "+=" if done.outcome == "added" else "already names"
    print(f"{rel}: {done.field} {verb} {done.target}")
    for note in done.notes:
        print(f"  {note}")


def run(source: str = None, field: str = None, target: str = None,
        draft: str = None) -> None:
    """Write a relation into an existing document: `luria relate SOURCE
    FIELD TARGET`, or every entry of a drafts file's `relations` list with
    `--draft FILE`. One line per relation says what was written; a relation
    already present is reported, never duplicated."""
    if draft is not None:
        if source or field or target:
            sys.exit("luria relate: --draft takes its relations from the file")
        for r in _read_relations(draft):
            _say(relate(r["source"], r["field"], r["target"]))
        return
    if not (source and field and target):
        sys.exit("luria relate: SOURCE FIELD TARGET are all required "
                 "(or --draft FILE)")
    _say(relate(source, field, target))


if __name__ == "__main__":
    import fire
    fire.Fire(run)
