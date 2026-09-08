# luria/derive.py
"""A field computed from another field, declared rather than written (#216).

    [luria.schemes.SOTA.fields.primary_topic]
    derive     = "first:tags"
    vocabulary = "tags"

`primary_topic` is then an ordinary field everywhere a field is read — the
invariant a chain asserts, a facet, a report column — and it is never written
down, so it cannot drift from the thing it restates.

**The motivating shape.** "Primary topic" is usually not a field at all but a
`tag_group` with `require = "exactly-one"`: a constraint on a *set*. Asking a
document for its primary means intersecting its tags with the group's and
hoping one value falls out, which is why that model is order-blind — and why
holding two vocabulary topics reads as a violation rather than as a statement.
Deriving the primary from position says the same thing without forbidding the
second topic, and picks up an ordering convention the vocabulary files already
had ("in the order the index shows them").

**Read-only, and deliberately unlike ADR-066.** A remote's URI takes an
explicit declaration over a derivation, because a template is a genuine second
source for something luria cannot otherwise know. A written `primary_topic:`
is not that: it is the same fact as `tags[0]`, stored twice and free to
disagree. So writing a derived field is a finding, not an override.

**A closed set of takes, not an expression language.** `first` and `last` over
a list. The source must be list-valued — `first:` of a scalar is the scalar,
which is a rename wearing a derivation's clothes. Everything past this waits
for a case that needs it.
"""

from __future__ import annotations

from dataclasses import dataclass

# The takes, and what each one reads off a list. Closed: a spelling outside
# this map is refused where the config is read, not discovered as a field that
# silently never resolves.
TAKES = {
    "first": lambda values: values[0],
    "last": lambda values: values[-1],
}


@dataclass(frozen=True)
class Derived:
    """One derivation: `field` is what it defines, off `source`, by `take`."""
    field: str
    take: str
    source: str

    @property
    def spec(self) -> str:
        """The declaration as written, for messages that name it."""
        return f"{self.take}:{self.source}"


def parse(where: str, field: str, raw) -> Derived:
    """One `derive = "take:source"` declaration, or a ValueError naming the
    spelling that was wrong. Shape only — whether `source` is a field the
    scheme can hold needs the whole scheme, so it is checked there."""
    text = str(raw).strip()
    take, sep, source = text.partition(":")
    take, source = take.strip(), source.strip()
    if not sep or not take or not source:
        raise ValueError(
            f"{where}: `derive = {text!r}` is not a derivation — the shape is "
            f'"take:field", as in "first:tags"')
    if take not in TAKES:
        raise ValueError(
            f"{where}: `derive` takes {take!r}, which is not one of "
            f"{', '.join(sorted(TAKES))}")
    if source == field:
        raise ValueError(
            f"{where}: `{field}` derives from itself, which resolves to "
            f"nothing")
    return Derived(field=str(field), take=take, source=source)


def value(meta: dict, rule: Derived):
    """The derived value for one document, or None when the source holds
    nothing.

    Absence is not an error here. A document with no `tags:` has no primary
    topic to compute, and saying so is the tags field's job — reporting it
    twice would name the wrong line as the fix."""
    raw = meta.get(rule.source)
    values = raw if isinstance(raw, list) else ([] if raw in (None, "") else [raw])
    values = [v for v in values if v not in (None, "")]
    return TAKES[rule.take](values) if values else None


def written(meta: dict, rules) -> list[str]:
    """The derived fields this document wrote for itself — the finding, since
    a derived field has one source and frontmatter is not it."""
    return [r.field for r in rules if meta.get(r.field) not in (None, "", [])]


def applied(meta: dict, rules) -> dict:
    """`meta` with every derivation resolved onto it.

    A copy: the caller's dict is what the document says, and several checks
    still need to tell the two apart."""
    if not rules:
        return meta
    out = dict(meta)
    for rule in rules:
        got = value(meta, rule)
        if got is None:
            out.pop(rule.field, None)
        else:
            out[rule.field] = got
    return out
