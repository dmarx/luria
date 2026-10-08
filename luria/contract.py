# luria/contract.py
"""The obligations a scheme places on one of its entries, compiled once.

`requires` says a field must be there. `references` says what it holds.
`fields.<field>.groups` says which of a field's values may combine. Each
arrived as its own lint pass
(ADR-040, ADR-054, ADR-060), each re-parsing every document's frontmatter and
each spelling its own provenance by hand in the message it printed. Three
passes is three places to ask "what does this scheme demand of an entry?" and
no place that answers the whole question.

This module is that place (#141). A scheme's declarations compile into one
`Contract`: the fields an entry must carry, what each must hold, and which of
its tags combine — every obligation naming where it was declared. The lint
runs one pass over it. Nothing is authored here; `luria.yaml` is the only
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
from .config import spelled as _spelled


@dataclass(frozen=True)
class Field:
    """One frontmatter field an entry must (or may) carry, and what it holds.

    `reference` is the scheme prefixes a code may belong to when the field
    names a document — one, or several for a relation spanning families
    (#160) — and `None` when any truthy value satisfies it; the gap between
    the two is the one ADR-060 measured. `because` is every declaration that
    contributed, so a finding can say why rather than only what."""
    name: str
    required: bool = True
    reference: tuple[str, ...] | None = None
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
    # Whether a value outside `values` is a finding. False is what `tags`
    # needed: the declaration supplies order, label and blurb, and using a
    # new value stays an edit to a document (ADR-098).
    closed: bool = True
    # When the requirement applies, if not always (`RequiredWhen`, #170).
    # `required` stays the unconditional flag; this is the other way a field
    # can be demanded, and the two are exclusive by construction in config.
    required_when: object | None = None
    # When the field may not be written at all — the same condition, the
    # opposite sense (ADR-125, #191).
    forbidden_when: object | None = None
    # The vocabulary's own prose, printed after a closed-set violation
    # (ADR-108, #273). Carried on the field because that is what a check has in hand;
    # declared on the vocabulary, because that is what it is about.
    alert: str = ""
    # What the field is FOR, carried from whichever table typed it — a
    # vocabulary, a relation or a plain field (ADR-109, #279). `alert` is what it says
    # when a rule fires; this is what it says at rest, and `describe` prints
    # it so `docs/record.md` can explain a field rather than only constrain
    # one.
    blurb: str = ""
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
    where: str = "luria.yaml"
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

    def forbids(self, field: Field, meta: dict) -> bool:
        """Whether this document may not carry the field — read through the
        same effective values `demands` reads, so a status carrying a note is
        still that status (ADR-125)."""
        when = field.forbidden_when
        return when is not None and any(
            str(v) in when.values for v in self.reading(when.on, meta))

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
        return not self.fields and not self.groups and not self.field_groups


def targets(field: Field) -> tuple[str, ...]:
    """The local schemes a reference field's codes may belong to — empty for
    a field that names no document. A field may also name remotes
    (`scheme: [LIT, ARXIV]`); those are `remotes_of`, never resolved here."""
    if field.reference is None:
        return ()
    remotes = current().remotes
    return tuple(t for t in field.reference if t not in remotes)


def remotes_of(field: Field) -> tuple[str, ...]:
    """The remotes a reference field's codes may belong to: a citation the
    remote machinery verifies (ADR-016), declared as a target like a scheme
    so a successor that is a published paper is said, not assumed."""
    if field.reference is None:
        return ()
    remotes = current().remotes
    return tuple(t for t in field.reference if t in remotes)


def names_remote(field: Field, code: str) -> bool:
    """Whether `code` is a remote code of a remote this field names."""
    from . import remotes
    parsed = remotes.parse_code(code)
    return parsed is not None and parsed[0].prefix in remotes_of(field)


def target_of(field: Field, code: str) -> str | None:
    """Which of the field's declared schemes `code` belongs to, or None. Read
    off the code's own prefix, so `LIT-001` is never mistaken for a code of
    a scheme whose prefix merely starts the same way."""
    return next((t for t in targets(field) if code.startswith(f"{t}-")), None)


def spelled(field: Field) -> str:
    """What a field may hold, as a finding says it: `LIT`, `LIT or ARXIV`."""
    return _spelled(field.reference or ())

def for_scheme(scheme) -> Contract:
    """Everything `luria.yaml` declares this scheme demands of an entry.

    Fields keep declaration order — `requires` first, then the references
    that did not merge into one — so findings read in the order the config
    was written."""
    where = f"luria.yaml: schemes.{scheme.prefix}"
    vocabulary = ""
    if any(g.derived for g in scheme.tag_groups):
        vocabulary = f"vocabulary {scheme.tags_vocab!r}"
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
            reference=tuple(ref.scheme), many=ref.many,
            required_when=ref.required_when,
            forbidden_when=ref.forbidden_when, blurb=ref.blurb,
            because=because)
    from .vocabularies import declared
    for vocab in scheme.vocabularies:
        prior = fields.get(vocab.field)
        because = (f"{where}.fields.{vocab.field}",
                   f"vocabulary {vocab.name!r}: values")
        if prior is not None:
            because = prior.because + because
        fields[vocab.field] = Field(
            vocab.field,
            required=vocab.required or (prior is not None and prior.required),
            many=vocab.many, vocabulary=vocab.name, closed=vocab.closed,
            values=tuple(declared(vocab.values_by_name)), default=vocab.default,
            required_when=vocab.required_when,
            forbidden_when=vocab.forbidden_when, alert=vocab.alert,
            blurb=vocab.blurb, because=because)
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
            required_when=plain.required_when,
            forbidden_when=plain.forbidden_when, blurb=plain.blurb,
            because=because)
    return Contract(scheme.prefix, tuple(fields.values()), scheme.tag_groups,
                    field_groups=scheme.field_groups,
                    where="luria.yaml", vocabulary=vocabulary,
                    derived=scheme.derived)


def _cite(because: tuple[str, ...]) -> str:
    """`(luria.yaml: schemes.SOTA.requires, schemes.SOTA.references.source)`
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
    cite = (f"{contract.where}: schemes.{contract.scheme}.fields."
            f"{group.field}.groups.{group.name}")
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


def forbidden(contract: Contract, field: Field, meta: dict) -> str:
    """Why a field may not be here, in the document's own words — the value
    that turned the rule on — plus the key that said so."""
    when = field.forbidden_when
    # What the rule read, not the raw line: a default fills an absent field.
    shown = ", ".join(str(v) for v in contract.reading(when.on, meta))
    cite = _cite(field.because)
    return (f"the {contract.scheme} scheme forbids it while `{when.on}` is "
            f"{', '.join(f'`{v}`' for v in when.values)}, and this document "
            f"says `{when.on}: {shown}` {cite}")


def _forbids(field: Field) -> str:
    """The `describe` clause for a forbidden field, or ""."""
    when = field.forbidden_when
    if when is None:
        return ""
    return (f"; forbidden when `{when.on}` is "
            + ", ".join(f"`{v}`" for v in when.values))


def explain(contract: Contract, field: Field, meta: dict | None = None) -> str:
    """Why a field is demanded, in the words the finding has always used,
    plus the key that said so.

    The provenance is read out of the obligation rather than spelled here,
    so the day one comes from somewhere other than `luria.yaml` the finding
    says so without this function learning about it."""
    why = _condition(field, meta)
    if field.vocabulary is not None:
        return (f"the {contract.scheme} scheme declares it a `{field.vocabulary}` "
                f"value{why} {_cite(field.because)}")
    if field.reference is None:
        return (f"the {contract.scheme} scheme requires it{why} "
                f"{_cite(field.because)}")
    return (f"the {contract.scheme} scheme declares it a {spelled(field)} "
            f"reference{why} {_cite(field.because)}")


def describe(contract: Contract) -> list[str]:
    """The whole contract, one line per obligation, each naming where it was
    declared — the same words a finding cites, from the same place (DP-4).
    What `docs/record.md` prints under "what an entry must carry".

    A field or group that declares a `blurb` has it appended (#279). After
    the citation rather than before, because the constraint is what the line
    is for and the explanation is why anyone would accept it — and because
    that keeps every line the same shape whether or not one was written."""
    lines = []

    def say(line: str, blurb: str) -> None:
        lines.append(f"{line} — *{blurb}*" if blurb else line)
    for field in contract.fields:
        if (rule := contract.derivation(field.name)) is not None:
            # `spec` rather than `template`: a followed derivation reads
            # another document, and a record page saying only `{published}`
            # would not say whose (#233).
            what = f"derived — `{rule.spec}`, never written"
            if field.vocabulary is not None:
                what += (", and one of "
                         + ", ".join(f"`{v}`" for v in field.values))
            say(f"`{field.name}` — {what} {_cite(field.because)}", field.blurb)
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
            what += _forbids(field)
            say(f"`{field.name}` — {what} {_cite(field.because)}", field.blurb)
            continue
        what = ("required" if field.required else
                (f"required when `{field.required_when.on}` is "
                 + ", ".join(f"`{v}`" for v in field.required_when.values))
                if field.required_when is not None else "optional")
        if field.reference is not None:
            shown = " or ".join(f"`{t}`" for t in targets(field)) or "`*`"
            what += (f", one or more {shown} codes" if field.many
                     else f", a {shown} code")
            if not field.required:
                what += " when present"
        what += _forbids(field)
        say(f"`{field.name}` — {what} {_cite(field.because)}", field.blurb)
    for group in contract.field_groups:
        members = ", ".join(f"`{f}`" for f in group.fields)
        say(f"`{group.name}` — {_FIELD_RULE_WORDS[group.require]} "
            f"{members} {field_group_because(contract, group)}", group.blurb)
    for group in contract.groups:
        members = ", ".join(f"`{t}`" for t in sorted(group.tags))
        rule = {"exactly-one": "exactly one of", "at-most-one": "at most one of",
                "any": "any of"}[group.require]
        what = f"{rule} {members}"
        if group.excluded_by:
            banned = ", ".join(f"`{t}`" for t in sorted(group.excluded_by))
            what += f"; none of them alongside {banned}"
        say(f"`{group.name}` — {what} {group_because(contract, group)}",
            group.blurb)
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
    # A scheme's derived alias names its document as surely as the code does
    # (#219): `area: AREA-runtime` is the readable spelling of `AREA-001`,
    # and a reference field is where a readable spelling reads best.
    if any(s.alias for s in current().schemes.values()):
        from .aliases import derived_code
        if (code := derived_code(text)) is not None:
            return code
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


def codes_of(field: Field, raw) -> list[str]:
    """The codes a reference field holds, each resolved: a derived alias to
    the code it names, anything else as written. Every walk over a relation
    reads through this, so a document citing `AREA-runtime` and one citing
    `AREA-001` are joined to the same node."""
    out = []
    for value in values_of(field, raw) or []:
        text = str(value).strip()
        out.append(reference_code(text) or text)
    return out


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
    the finding (ADR-089)."""
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
        # Present where it is forbidden is the whole finding: the field's
        # shape is beside the point when it should not be there at all.
        if raw not in (None, "", []) and contract.forbids(field, meta):
            out.append(f"{rel}: `{field.name}:` is written, but "
                       f"{forbidden(contract, field, meta)}")
            continue
        if field.vocabulary is not None:
            out.extend(_vocabulary_violations(contract, field, rel, raw, meta))
            continue
        target = field.reference
        if target is None:
            if not raw and contract.demands(field, meta):
                out.append(f"{rel}: no `{field.name}:` in frontmatter — "
                           f"{explain(contract, field, meta)}")
            continue
        target = spelled(field)
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
            elif names_remote(field, code):
                continue        # a citation the remote machinery verifies
            elif (home := target_of(field, code)) is None:
                out.append(
                    f"{rel}: `{field.name}: {code}` is not a {target} code — "
                    f"a {contract.scheme} document's `{field.name}` names a "
                    f"{target} document {_cite(field.because)}")
            elif code not in known.setdefault(home, resolvable(home)):
                out.append(f"{rel}: `{field.name}: {code}` resolves to no "
                           f"{home} document")
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
    for group in contract.groups:
        # The group's own field, not a key called `tags`: a group constrains
        # a subset of one field's vocabulary and now says which
        # (ADR-098).
        tags = {str(t) for t in (meta.get(group.field) or [])}
        present = sorted(tags & group.tags)
        shown = ", ".join(sorted(group.tags))
        cite = group_because(contract, group)
        tail = f"\n    ↳ {group.alert}" if group.alert else ""
        if group.require == "exactly-one" and len(present) != 1:
            out.append(f"{rel}: `{group.name}` wants exactly one of {shown} "
                       f"— has {', '.join(present) or 'none'} {cite}{tail}")
        elif group.require == "at-most-one" and len(present) > 1:
            out.append(f"{rel}: `{group.name}` wants at most one of {shown} "
                       f"— has {', '.join(present)} {cite}{tail}")
        if present and (clash := sorted(tags & group.excluded_by)):
            out.append(f"{rel}: {', '.join(clash)} excludes `{group.name}`, "
                       f"but the document also has {', '.join(present)} "
                       f"{cite}{tail}")
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
    if not field.closed:
        # An open vocabulary declares what it has an opinion about and
        # accepts the rest. Checking it would forbid the one case the flag
        # exists for (ADR-098).
        return []
    file = next((b.split(": ", 1)[0] for b in field.because
                 if b.endswith(": values")), "")
    tail = f"\n    ↳ {field.alert}" if field.alert else ""
    return [f"{rel}: `{field.name}: {value}` is not in the `{field.vocabulary}` "
            f"vocabulary ({file}) — the values are {', '.join(field.values)}"
            f"{tail}"
            for value in values if str(value) not in field.values]
