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
    # A list of codes rather than one. Only a reference can say so; a
    # plain `requires` field is satisfied by any truthy value, whatever
    # shape it has.
    many: bool = False
    # Standard for every scheme rather than declared by one — `superseded_by`
    # (ADR-tmpxmnac). Checked like any other; not a declaration, so it stays
    # out of `Contract.empty`.
    builtin: bool = False
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
        return not any(not f.builtin for f in self.fields) and not self.groups


# A reference into any local scheme: the successor a superseded document
# names may live in another scheme, and a remote code passes as a citation
# the remote machinery verifies.
ANY_SCHEME = "*"

# The fields every scheme has. `superseded_by` holds one code or a list —
# the successor is structure, written and checked as a reference, and the
# typed edge the index and the site render (ADR-tmpxmnac).
BUILT_IN = (
    Field("superseded_by", required=False, reference=ANY_SCHEME, many=True,
          builtin=True, because=("built in: `superseded_by` (ADR-tmpxmnac)",)),
)


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
            reference=ref.scheme, many=ref.many, because=because)
    for field in BUILT_IN:
        fields.setdefault(field.name, field)
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
        if field.builtin:
            continue
        what = "required" if field.required else "optional"
        if field.reference is not None:
            what += (f", one or more `{field.reference}` codes" if field.many
                     else f", a `{field.reference}` code")
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


def values_of(field: Field, raw) -> list | None:
    """The values a reference field holds, one per element, or None when
    the shape contradicts the declaration.

    A plural field takes a list or a single value (a list of one, which is
    unambiguous). A scalar field given a list is None: the tool would have
    to guess which element was meant, and guessing is what stringifying
    the list and reading its first code used to do, silently."""
    if isinstance(raw, list):
        if not field.many:
            return None
        return [v for v in raw if v not in (None, "")]
    return [] if raw in (None, "") else [raw]


def local_scheme(code: str) -> str | None:
    """The configured scheme a code belongs to, or None for a remote code
    or a prefix nothing declares."""
    prefix = code.rsplit("-", 1)[0]
    return prefix if prefix in current().schemes else None


def is_remote(code: str) -> bool:
    from . import remotes
    return remotes.parse_code(code) is not None


def _any_scheme_violations(contract: Contract, field: Field, rel: str, raw,
                           known: dict[str, set[str]]) -> list[str]:
    """A built-in reference into any scheme: one code or a list, each a
    code that resolves in the scheme it names, or a remote code."""
    out = []
    for value in values_of(field, raw) or []:
        code = reference_code(str(value))
        if code is None:
            out.append(f"{rel}: `{field.name}: {value}` is not a code — "
                       f"`{field.name}` names a document {_cite(field.because)}")
        elif is_remote(code):
            continue
        elif (home := local_scheme(code)) is None:
            out.append(f"{rel}: `{field.name}: {code}` names no scheme or "
                       f"remote this record declares")
        elif code not in known.setdefault(home, resolvable(home)):
            out.append(f"{rel}: `{field.name}: {code}` resolves to no "
                       f"{home} document")
    return out


def violations(contract: Contract, rel: str, meta: dict,
               known: dict[str, set[str]]) -> list[str]:
    """One document against its scheme's contract, one line per breach.

    `known` maps a target prefix to its resolvable codes; the caller loads
    each once per run rather than once per document."""
    out: list[str] = []
    for field in contract.fields:
        raw = meta.get(field.name)
        target = field.reference
        if target is None:
            if not raw and field.required:
                out.append(f"{rel}: no `{field.name}:` in frontmatter — "
                           f"{explain(contract, field)}")
            continue
        if target == ANY_SCHEME:
            out.extend(_any_scheme_violations(contract, field, rel, raw, known))
            continue
        values = values_of(field, raw)
        if values is None:
            out.append(
                f"{rel}: `{field.name}:` holds {len(raw)} values, but the "
                f"{contract.scheme} scheme declares it one {target} "
                f"reference {_cite(field.because)} — set `many = true` "
                f"there if it should hold several")
            continue
        if not values:
            if field.required:
                out.append(f"{rel}: no `{field.name}:` in frontmatter — "
                           f"{explain(contract, field)}")
            continue
        for value in values:
            code = reference_code(str(value))
            if code is None:
                out.append(
                    f"{rel}: `{field.name}: {value}` is not a code — the "
                    f"{contract.scheme} scheme declares this field a "
                    f"{target} reference {_cite(field.because)}")
            elif not code.startswith(f"{target}-"):
                out.append(
                    f"{rel}: `{field.name}: {code}` is not a {target} code — "
                    f"a {contract.scheme} document's `{field.name}` names a "
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
