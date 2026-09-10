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

from . import derive
from .config import (TEMP_TAIL, FieldGroup, RequiredWhen, TagGroup,
                     current)


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
    # A list of values rather than one. A reference or a vocabulary can say
    # so; a plain `requires` field is satisfied by any truthy value,
    # whatever shape it has.
    many: bool = False
    # A controlled vocabulary the field draws from (ADR-076), with its
    # values in file order and the effective value of an absent field.
    # `reference` and `vocabulary` are the two typed cases of what a field
    # holds; neither set is `Any`.
    vocabulary: str | None = None
    values: tuple[str, ...] = ()
    default: tuple[str, ...] | None = None
    # Standard for every scheme rather than declared by one — `superseded_by`
    # (ADR-071). Checked like any other; not a declaration, so it stays
    # out of `Contract.empty`.
    builtin: bool = False
    # When the requirement applies, if not always (`RequiredWhen`, #170).
    # `required` stays the unconditional flag; this is the other way a field
    # can be demanded, and the two are exclusive by construction in config.
    required_when: object | None = None
    because: tuple[str, ...] = ()




@dataclass(frozen=True)
class Contract:
    """What one scheme demands of each of its entries."""
    scheme: str
    fields: tuple[Field, ...] = ()
    groups: tuple[TagGroup, ...] = ()
    # Several fields of which an entry must carry some — a need with a name
    # that any of them satisfies.
    field_groups: tuple[FieldGroup, ...] = ()
    # Where this scheme's table lives, as a finding cites it — the prefix
    # every key path below starts from.
    where: str = "luria.toml"
    # The vocabulary file a derived tag group reads its members from
    # (`primary_for`, ADR-060), relative to the project; "" when none.
    vocabulary: str = ""
    # Fields computed from another field (`derive.Derived`, #216). Resolved
    # onto the document before every other check, so a derived field is
    # checked exactly like a written one — including against its vocabulary,
    # which is what makes "the first tag is a real topic" cost no new code.
    derived: tuple = ()

    def derivation(self, name: str):
        """The rule computing `name`, or None when it is written (#216).

        Read by everything that must tell a computed field from a written one:
        the scaffold, which has no flag to offer for one, and the record page,
        which says where the value comes from rather than what shape it is."""
        return next((r for r in self.derived if r.field == name), None)

    def demands(self, field: Field, meta: dict) -> bool:
        """Whether this document must carry the field. Consulted everywhere
        `required` used to be read directly, so a conditional requirement
        cannot be honoured by one check and ignored by the next — which is
        the failure mode this module was written to end.

        A method on the contract rather than on the field, because deciding
        whether a condition holds needs the *effective* value of the field it
        names, and only the compiled contract knows how to resolve that."""
        if field.required:
            return True
        when = field.required_when
        if when is None:
            return False
        return any(str(v) in when.values for v in self.reading(when.on, meta))

    def reading(self, name: str, meta: dict) -> list:
        """What a field is read as on one document — the same resolution the
        checks and the record page use, so a condition sees the value the
        rest of the machinery sees.

        Three cases, and the first two are why this cannot read raw
        frontmatter. A `status:` carrying a qualifying note is still that
        status and the note is its own field (ADR-072), so
        `Proposed — pending a replication` reads as `Proposed`. A vocabulary
        field with a `default` is never absent (ADR-076), so a document that
        omits it reads as the default — and reading raw made a condition on
        such a field never hold, for precisely the documents it was written
        about. Everything else is what the document says: a list reads as its
        elements, and an absent field reads as nothing, which is "the
        condition does not hold" rather than an error (the missing-field
        finding is the document check's, not this one's)."""
        if name == "status":
            from .statuses import of
            return [of(meta).value]
        spec = next((f for f in self.fields if f.name == name), None)
        raw = meta.get(name)
        if spec is not None and spec.vocabulary is not None:
            return effective_values(spec, raw) or []
        if raw is None or raw == "":
            return []
        return list(raw) if isinstance(raw, list) else [raw]

    @property
    def empty(self) -> bool:
        """True for every scheme that declares nothing — which is every
        scheme that predates the three tables, and the shipped ADR scheme."""
        return (not any(not f.builtin for f in self.fields)
                and not self.groups and not self.field_groups)


# A reference into any local scheme: the successor a superseded document
# names may live in another scheme, and a remote code passes as a citation
# the remote machinery verifies.
ANY_SCHEME = "*"

# The fields every scheme has. `superseded_by` holds one code or a list —
# the successor is structure, written and checked as a reference, and the
# typed edge the index and the site render (ADR-071).
#
# ADR-071's other half — a Superseded document *names* its successor — was a
# hand-written branch in `lint.check_frontmatter` for as long as there was no
# way to declare it. `required_when` is that way (#170), so the rule is stated
# here instead of implemented twice: one implementation (DP-4), and the
# built-in gets this module's finding wording, `because:` provenance and
# record-page line for nothing.
def built_in(scheme) -> tuple[Field, ...]:
    """The fields a scheme gets without asking — today, the one naming what
    replaced a retired document.

    A **default**, not a law (ADR-085). The field's name and the status
    that demands it come from the scheme (`successor` and `retires_on`,
    themselves defaulting to `superseded_by` and `Superseded`), and a scheme
    declaring the field in its own `references` table replaces this outright
    — `for_scheme` merges these last, with `setdefault`.

    `active` set that precedent long ago: which word means *in force* was
    always the project's to choose. What generic code needs is the role, not
    the word."""
    return (Field(scheme.successor, required=False, reference=ANY_SCHEME,
                  many=True, builtin=True,
                  required_when=RequiredWhen("status", (scheme.retires_on,)),
                  because=(f"built in: `{scheme.successor}` (ADR-071)",)),)


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
            reference=ref.scheme, many=ref.many,
            required_when=ref.required_when, because=because)
    from .vocabularies import declared
    for vocab in scheme.vocabularies:
        prior = fields.get(vocab.field)
        because = (f"{where}.fields.{vocab.field}",
                   f"{current().rel(vocab.file)}: values")
        if prior is not None:
            because = prior.because + because
        fields[vocab.field] = Field(
            vocab.field,
            required=vocab.required or (prior is not None and prior.required),
            many=vocab.many, vocabulary=vocab.name,
            values=tuple(declared(vocab.file)), default=vocab.default,
            required_when=vocab.required_when, because=because)
    for plain in scheme.plain_fields:
        prior = fields.get(plain.field)
        because = (f"{where}.fields.{plain.field}",)
        if prior is not None:
            because = prior.because + because
        fields[plain.field] = Field(
            plain.field,
            required=plain.required or (prior is not None and prior.required),
            many=plain.many or (prior is not None and prior.many),
            reference=prior.reference if prior is not None else None,
            required_when=plain.required_when, because=because)
    for field in built_in(scheme):
        fields.setdefault(field.name, field)
    return Contract(scheme.prefix, tuple(fields.values()), scheme.tag_groups,
                    field_groups=scheme.field_groups,
                    where="luria.toml", vocabulary=vocabulary,
                    derived=scheme.derived)


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


def field_group_because(contract: Contract, group: FieldGroup) -> str:
    return (f"({contract.where}: schemes.{contract.scheme}.field_groups."
            f"{group.name})")


_FIELD_RULE_WORDS = {"at-least-one": "at least one of",
                     "exactly-one": "exactly one of",
                     "at-most-one": "at most one of"}


def group_because(contract: Contract, group: TagGroup) -> str:
    """Where a tag group was declared — and, when its membership is derived,
    where the members come from."""
    cite = f"{contract.where}: schemes.{contract.scheme}.tag_groups.{group.name}"
    if group.derived and contract.vocabulary:
        cite += f"; members from `{contract.vocabulary}` `primary_for`"
    return f"({cite})"


def _condition(field: Field, meta: dict | None) -> str:
    """Why a conditional requirement fired, in the document's own words:
    the field that decided and the value it held. A finding that recites only
    the rule leaves the reader to work out which of their fields turned it
    on."""
    when = field.required_when
    if when is None:
        return ""
    if meta and (held := meta.get(when.on)) is not None:
        return f", because `{when.on}: {held}`"
    return f", when `{when.on}` is {', '.join(when.values)}"


def explain(contract: Contract, field: Field, meta: dict | None = None) -> str:
    """Why a field is demanded, in the words the finding has always used,
    plus the key that said so.

    The provenance is read out of the obligation rather than spelled here,
    so the day one comes from somewhere other than `luria.toml` the finding
    says so without this function learning about it."""
    why = _condition(field, meta)
    if field.vocabulary is not None:
        return (f"the {contract.scheme} scheme declares it a `{field.vocabulary}` "
                f"value{why} {_cite(field.because)}")
    if field.reference is None:
        return (f"the {contract.scheme} scheme requires it{why} "
                f"{_cite(field.because)}")
    what = ("names a document in any scheme" if field.reference == ANY_SCHEME
            else f"declares it a {field.reference} reference")
    lead = ("" if field.reference == ANY_SCHEME
            else f"the {contract.scheme} scheme ")
    if field.reference == ANY_SCHEME:
        return f"`{field.name}` {what}{why} {_cite(field.because)}"
    return f"{lead}{what}{why} {_cite(field.because)}"


def describe(contract: Contract) -> list[str]:
    """The whole contract, one line per obligation, each naming where it was
    declared — the same words a finding cites, from the same place (DP-4).
    What `docs/record.md` prints under "what an entry must carry"."""
    lines = []
    for field in contract.fields:
        # Built-ins stay out: this describes what a scheme declares *beyond*
        # the standard fields, and the page says so in as many words. The
        # built-in conditional is real and worth a reader's attention, so
        # `record_doc` states it once alongside the standard fields rather
        # than repeating it under every scheme as though it were declared
        # there (review of #172).
        if field.builtin:
            continue
        if (rule := contract.derivation(field.name)) is not None:
            # `spec` rather than `template`: a followed derivation reads
            # another document, and a record page saying only `{published}`
            # would not say whose (#233).
            what = f"derived — `{rule.spec}`, never written"
            if field.vocabulary is not None:
                what += (", and one of "
                         + ", ".join(f"`{v}`" for v in field.values))
            lines.append(f"`{field.name}` — {what} {_cite(field.because)}")
            continue
        if field.vocabulary is not None:
            members = ", ".join(f"`{v}`" for v in field.values)
            what = ("required, " if field.required
                    else (f"required when `{field.required_when.on}` is "
                          + ", ".join(f"`{v}`" for v in field.required_when.values)
                          + ", ") if field.required_when is not None
                    else "" if field.default else "optional, ")
            what += ("one or more of " if field.many else "one of ") + members
            if field.default:
                what += "; absent means " + ", ".join(f"`{d}`" for d in field.default)
            lines.append(f"`{field.name}` — {what} {_cite(field.because)}")
            continue
        what = ("required" if field.required else
                (f"required when `{field.required_when.on}` is "
                 + ", ".join(f"`{v}`" for v in field.required_when.values))
                if field.required_when is not None else "optional")
        if field.reference is not None:
            what += (f", one or more `{field.reference}` codes" if field.many
                     else f", a `{field.reference}` code")
            if not field.required:
                what += " when present"
        lines.append(f"`{field.name}` — {what} {_cite(field.because)}")
    for group in contract.field_groups:
        members = ", ".join(f"`{f}`" for f in group.fields)
        lines.append(f"`{group.name}` — {_FIELD_RULE_WORDS[group.require]} "
                     f"{members} {field_group_because(contract, group)}")
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
    """The code a reference field holds: a scheme code, or a remote one.

    Remotes are read first, through the one reader of their anatomy. A uid
    remote's tail is opaque — `ARXIV-2110.08058`, `DOI:10.1145/3600006` —
    and the scheme-shaped pattern, tried alone, read `ARXIV-2110` out of
    the first and nothing out of the second, so a `superseded_by:` naming a
    paper failed as "names no scheme or remote" while the same code in
    prose resolved. Any truthy value was never the contract; a remote code
    always was (`_any_scheme_violations`)."""
    text = value.strip()
    from . import remotes
    if current().remotes:
        refs = remotes.references(text)
        if refs:
            return refs[0].composed
    m = _REF_CODE_RE.search(text)
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


def effective_values(field: Field, raw) -> list | None:
    """What a field is read as: its written values, or the default when it
    is absent. The source is never touched — a default is a convention the
    config states, not a fact the tree does (ADR-076)."""
    values = values_of(field, raw)
    if values is None:
        return None
    if not values and field.default is not None:
        return list(field.default)
    return values


def local_scheme(code: str) -> str | None:
    """The configured scheme a code belongs to, or None for a remote code
    or a prefix nothing declares."""
    prefix = code.rsplit("-", 1)[0]
    return prefix if prefix in current().schemes else None


def is_remote(code: str) -> bool:
    from . import remotes
    return remotes.parse_code(code) is not None


def _any_scheme_violations(contract: Contract, field: Field, rel: str, raw,
                           known: dict[str, set[str]],
                           meta: dict | None = None) -> list[str]:
    """A built-in reference into any scheme: one code or a list, each a
    code that resolves in the scheme it names, or a remote code — and
    present at all when the contract demands it."""
    out = []
    values = values_of(field, raw) or []
    if not values and contract.demands(field, meta or {}):
        return [f"{rel}: no `{field.name}:` in frontmatter — "
                f"{explain(contract, field, meta)}"]
    for value in values:
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
               known: dict[str, set[str]], resolve=None) -> list[str]:
    """One document against its scheme's contract, one line per breach.

    `known` maps a target prefix to its resolvable codes; the caller loads
    each once per run rather than once per document. `resolve` is how a
    `from` derivation reads the document it follows (#233), and for the same
    reason belongs to the run: one shared reader, not one per document.

    A derived field (#216) is read off the document before anything else runs,
    so every check below sees one field whether it was computed or written —
    with one exception, taken first: writing a derived field down is itself
    the finding."""
    out: list[str] = []
    for name in derive.written(meta, contract.derived):
        rule = next(r for r in contract.derived if r.field == name)
        out.append(
            f"{rel}: `{name}:` is written in frontmatter, but "
            f"{contract.scheme} derives it (`{rule.spec}`) — the value has "
            f"one source and this is not it; drop the line and order "
            f"the fields it reads to say it")
    meta = derive.applied(meta, contract.derived, resolve)
    for field in contract.fields:
        raw = meta.get(field.name)
        if field.vocabulary is not None:
            out.extend(_vocabulary_violations(contract, field, rel, raw, meta))
            continue
        target = field.reference
        if target is None:
            if not raw and contract.demands(field, meta):
                out.append(f"{rel}: no `{field.name}:` in frontmatter — "
                           f"{explain(contract, field, meta)}")
            continue
        if target == ANY_SCHEME:
            out.extend(_any_scheme_violations(contract, field, rel, raw, known,
                                              meta))
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
            if contract.demands(field, meta):
                out.append(f"{rel}: no `{field.name}:` in frontmatter — "
                           f"{explain(contract, field, meta)}")
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
    for group in contract.field_groups:
        present = [f for f in group.fields if meta.get(f) not in (None, "", [])]
        shown = ", ".join(f"`{f}:`" for f in group.fields)
        has = ", ".join(f"`{f}:`" for f in present)
        cite = field_group_because(contract, group)
        if group.require == "at-least-one" and not present:
            out.append(f"{rel}: no `{group.name}` — one of {shown} — the "
                       f"{contract.scheme} scheme requires it {cite}")
        elif group.require == "exactly-one" and len(present) != 1:
            out.append(f"{rel}: `{group.name}` wants exactly one of {shown} "
                       f"— has {has or 'none'} {cite}")
        elif group.require == "at-most-one" and len(present) > 1:
            out.append(f"{rel}: `{group.name}` wants at most one of {shown} "
                       f"— has {has} {cite}")
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


def _vocabulary_violations(contract: Contract, field: Field, rel: str,
                           raw, meta: dict | None = None) -> list[str]:
    """A vocabulary field against its declaration: the shape, the presence,
    and every value against the closed set — naming the file, since that is
    where a missing value gets added."""
    values = values_of(field, raw)
    if values is None:
        return [f"{rel}: `{field.name}:` holds {len(raw)} values, but the "
                f"{contract.scheme} scheme declares it one `{field.vocabulary}` "
                f"value {_cite(field.because)} — set `many = true` there if "
                f"it should hold several"]
    if not values:
        if contract.demands(field, meta or {}) and field.default is None:
            return [f"{rel}: no `{field.name}:` in frontmatter — "
                    f"{explain(contract, field, meta)}"]
        return []
    file = next((b.split(": ", 1)[0] for b in field.because
                 if b.endswith(": values")), "")
    return [f"{rel}: `{field.name}: {value}` is not in the `{field.vocabulary}` "
            f"vocabulary ({file}) — the values are {', '.join(field.values)}"
            for value in values if str(value) not in field.values]
