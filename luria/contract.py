# luria/contract.py
"""The obligations a scheme places on one of its entries, compiled once.

`requires` says a field must be there. `references` says what it holds.
`tag_groups` says which tags may combine. Each arrived as its own lint pass
(ADR-040, ADR-054, ADR-060), each re-parsing every document's frontmatter and
each spelling its own provenance by hand in the message it printed. Three
passes is three places to ask "what does this scheme demand of an entry?" and
no place that answers the whole question.

This module is that place (#141). A scheme's declarations compile into one
`Contract`: the fields an entry must carry, what each must hold, and which of
its tags combine — every obligation naming where it was declared. The lint
runs one pass over it. Nothing is authored here; `luria.toml` is the only
source, and nothing a project declared before this existed reads differently.

Composition is intersection. `requires = ["source"]` and a `references` entry
for the same field are one obligation, not two: required and required is
required, and the reference supplies the type. ADR-060 noted the double
report as noise; compiling removes it. There is no precedence between
declarations and no need for one yet — a field is one key in one table, so
today's config cannot bind it to two schemes. When a second source of
obligations exists, a contradiction is a configuration error, never a winner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import TEMP_TAIL, TagGroup, current


@dataclass(frozen=True)
class Field:
    """One frontmatter field an entry must (or may) carry, and what it holds.

    `reference` is a scheme prefix when the field names a document, `None`
    when any truthy value satisfies it — the gap between the two is the one
    ADR-060 measured. `because` is every declaration that contributed, so a
    finding can say why rather than only what."""
    name: str
    required: bool = True
    reference: str | None = None
    because: tuple[str, ...] = ()


@dataclass(frozen=True)
class Contract:
    """What one scheme demands of each of its entries."""
    scheme: str
    fields: tuple[Field, ...] = ()
    groups: tuple[TagGroup, ...] = ()
    # Where this scheme's table lives, as a finding cites it — the prefix
    # every key path below starts from.
    where: str = "luria.toml"
    # The vocabulary file a derived tag group reads its members from
    # (`primary_for`, ADR-060), relative to the project; "" when none.
    vocabulary: str = ""

    @property
    def empty(self) -> bool:
        """True for every scheme that declares nothing — which is every
        scheme that predates the three tables, and the shipped ADR scheme."""
        return not self.fields and not self.groups


def for_scheme(scheme) -> Contract:
    """Everything `luria.toml` declares this scheme demands of an entry.

    Fields keep declaration order — `requires` first, then the references
    that did not merge into one — so findings read in the order the config
    was written."""
    where = f"luria.toml: schemes.{scheme.prefix}"
    vocabulary = ""
    if any(g.derived for g in scheme.tag_groups):
        vocabulary = str(current().rel(scheme.tags_yaml))
    fields: dict[str, Field] = {}
    for name in scheme.requires:
        fields[name] = Field(name, because=(f"{where}.requires",))
    for ref in scheme.references:
        prior = fields.get(ref.field)
        because = (f"{where}.references.{ref.field}",)
        if prior is not None:
            because = prior.because + because
        fields[ref.field] = Field(
            ref.field,
            required=ref.required or (prior is not None and prior.required),
            reference=ref.scheme, because=because)
    return Contract(scheme.prefix, tuple(fields.values()), scheme.tag_groups,
                    where="luria.toml", vocabulary=vocabulary)


def _cite(because: tuple[str, ...]) -> str:
    """`(luria.toml: schemes.SOTA.requires, schemes.SOTA.references.source)`
    — every declaration behind an obligation, grouped by the file it is in,
    so a reader is sent to the key and not just the file."""
    by_file: dict[str, list[str]] = {}
    for entry in because:
        file, _, key = entry.partition(": ")
        by_file.setdefault(file, []).append(key)
    return "(" + "; ".join(f"{file}: {', '.join(keys)}"
                           for file, keys in by_file.items()) + ")"


def group_because(contract: Contract, group: TagGroup) -> str:
    """Where a tag group was declared — and, when its membership is derived,
    where the members come from."""
    cite = f"{contract.where}: schemes.{contract.scheme}.tag_groups.{group.name}"
    if group.derived and contract.vocabulary:
        cite += f"; members from `{contract.vocabulary}` `primary_for`"
    return f"({cite})"


def explain(contract: Contract, field: Field) -> str:
    """Why a field is demanded, in the words the finding has always used,
    plus the key that said so.

    The provenance is read out of the obligation rather than spelled here,
    so the day one comes from somewhere other than `luria.toml` the finding
    says so without this function learning about it."""
    if field.reference is None:
        return f"the {contract.scheme} scheme requires it {_cite(field.because)}"
    return (f"the {contract.scheme} scheme declares it a {field.reference} "
            f"reference {_cite(field.because)}")


def describe(contract: Contract) -> list[str]:
    """The whole contract, one line per obligation, each naming where it was
    declared — the same words a finding cites, from the same place (DP-4).
    What `docs/record.md` prints under "what an entry must carry"."""
    lines = []
    for field in contract.fields:
        what = "required" if field.required else "optional"
        if field.reference is not None:
            what += f", a `{field.reference}` code"
            if not field.required:
                what += " when present"
        lines.append(f"`{field.name}` — {what} {_cite(field.because)}")
    for group in contract.groups:
        members = ", ".join(f"`{t}`" for t in sorted(group.tags))
        rule = {"exactly-one": "exactly one of", "at-most-one": "at most one of",
                "any": "any of"}[group.require]
        what = f"{rule} {members}"
        if group.excluded_by:
            banned = ", ".join(f"`{t}`" for t in sorted(group.excluded_by))
            what += f"; none of them alongside {banned}"
        lines.append(f"`{group.name}` — {what} {group_because(contract, group)}")
    return lines


# A reference field is data, not prose, so it holds a bare code — but the
# fixer rewrites prose fields in place and a hand-edited file can carry a
# link, so read the code out of either shape rather than demanding one.
_REF_CODE_RE = re.compile(
    r"([A-Z]{2,}(?:-[A-Z]+)*-(?:\d{1,4}|" + TEMP_TAIL + r"))")


def reference_code(value: str) -> str | None:
    m = _REF_CODE_RE.search(value.strip())
    return m.group(1) if m else None


def resolvable(prefix: str) -> set[str]:
    """Every code a reference into `prefix` may name: the numbered documents
    and the temporary ones awaiting concretization (ADR-049)."""
    scheme = current().schemes[prefix]
    return ({scheme.code(n) for n in scheme.documents()}
            | {f"{prefix}-{tail}" for tail in scheme.temp_documents()})


def violations(contract: Contract, rel: str, meta: dict,
               known: dict[str, set[str]]) -> list[str]:
    """One document against its scheme's contract, one line per breach.

    `known` maps a target prefix to its resolvable codes; the caller loads
    each once per run rather than once per document."""
    out: list[str] = []
    for field in contract.fields:
        raw = meta.get(field.name)
        if not raw:
            if field.required:
                out.append(f"{rel}: no `{field.name}:` in frontmatter — "
                           f"{explain(contract, field)}")
            continue
        target = field.reference
        if target is None:
            continue
        code = reference_code(str(raw))
        if code is None:
            out.append(
                f"{rel}: `{field.name}: {raw}` is not a code — the "
                f"{contract.scheme} scheme declares this field a "
                f"{target} reference {_cite(field.because)}")
        elif not code.startswith(f"{target}-"):
            out.append(
                f"{rel}: `{field.name}: {code}` is not a {target} code — a "
                f"{contract.scheme} document's `{field.name}` names a "
                f"{target} document {_cite(field.because)}")
        elif code not in known[target]:
            out.append(f"{rel}: `{field.name}: {code}` resolves to no "
                       f"{target} document")
    tags = {str(t) for t in (meta.get("tags") or [])}
    for group in contract.groups:
        present = sorted(tags & group.tags)
        shown = ", ".join(sorted(group.tags))
        cite = group_because(contract, group)
        if group.require == "exactly-one" and len(present) != 1:
            out.append(f"{rel}: `{group.name}` wants exactly one of {shown} "
                       f"— has {', '.join(present) or 'none'} {cite}")
        elif group.require == "at-most-one" and len(present) > 1:
            out.append(f"{rel}: `{group.name}` wants at most one of {shown} "
                       f"— has {', '.join(present)} {cite}")
        if present and (clash := sorted(tags & group.excluded_by)):
            out.append(f"{rel}: {', '.join(clash)} excludes `{group.name}`, "
                       f"but the document also has {', '.join(present)} {cite}")
    return out
