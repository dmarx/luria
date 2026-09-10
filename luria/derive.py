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

**One template vocabulary, two variable sources (#219).** The spelling is
`str.format` — the engine `Remote.uri` already renders URLs through, fed here
from a document's frontmatter instead of from a remote and a code. So there
is one template language in luria, not a second grammar per feature, and
`{tags[0]}`, `{first_author}`, `{published:.4}` all mean what they mean
everywhere else.

**Across a reference (#233).** A second declaration says which document to
render against:

    [luria.schemes.SOTA.fields.published]
    derive = "{published}"
    from   = "source[0]"

The template is unchanged — `{published}` still means what it means
everywhere — and only the *values* it renders against move, to the frontmatter
of the document `source[0]` names. That keeps the promise above: one template
language, and the new capability is a second variable source rather than a
second grammar.

**One hop, and it reads written frontmatter.** The target's own derivations
are not resolved first. So a cycle is impossible by construction rather than
by detection, and there is no order in which schemes must be evaluated. The
cost is that derivations do not chain; the case that motivated this does not
need them to, and a chain is a decision to take when something does.

**A lone field returns the value, not a string.** `"{tags[0]}"` yields the
tag itself, so it stays identical to the vocabulary member a check compares
it against and to the value another document's tag list intersects with.
Anything with literal text around it — `"LIT-{first_author}-{number}"` — is
a string, because that is what it was written to build. The rule is the
template's shape rather than a flag, so nothing has to be declared twice.
"""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class Follow:
    """Which referenced document a derivation reads: `source[0]`, `paper`.

    `index` is None for a scalar reference and an integer for one element of
    a plural one. There is no "every element" spelling: a field holds one
    value, so collecting across a list would need somewhere to put the
    others."""
    field: str
    index: int | None = None

    def __str__(self) -> str:
        return self.field if self.index is None else f"{self.field}[{self.index}]"

    def code(self, meta: dict) -> str | None:
        """The code this document points at, or None when it points nowhere."""
        raw = meta.get(self.field)
        if self.index is None:
            if isinstance(raw, list):
                return None      # a list where the declaration said one
            return str(raw).strip() or None if raw else None
        if not isinstance(raw, list):
            raw = [raw] if raw else []
        if self.index >= len(raw):
            return None
        got = raw[self.index]
        return str(got).strip() or None if got else None


@dataclass(frozen=True)
class Derived:
    """One derivation: `field` is what it defines, `template` how, and
    `follow` which document — None for this one (#216), a reference to
    render against for another (#233)."""
    field: str
    template: str
    follow: Follow | None = None

    @property
    def spec(self) -> str:
        """The declaration as written, for messages that name it."""
        if self.follow is None:
            return self.template
        return f"{self.template}` from `{self.follow}"

    @property
    def sources(self) -> tuple[str, ...]:
        """The frontmatter fields this template reads, for the eager check."""
        return names_in(self.template)


def names_in(template: str) -> tuple[str, ...]:
    """The field names a template reads, without the indexing or the format
    spec — `"LIT-{authors[0]}-{published:.4}"` names `authors` and
    `published`. What the eager check needs in order to say whether a scheme
    can hold them."""
    import string
    out = []
    for _, field, _, _ in string.Formatter().parse(template):
        if field:
            root = field.split(".")[0].split("[")[0].strip()
            if root and not root.isdigit() and root not in out:
                out.append(root)
    return tuple(out)


def lone_field(template: str) -> bool:
    """Whether the template is exactly one replacement field and nothing else.

    That is the case where the value survives as itself rather than as its
    rendering, which is what keeps a derived field comparable to the
    vocabulary it is checked against."""
    import string
    parts = list(string.Formatter().parse(template))
    return (len(parts) == 1 and parts[0][0] == "" and parts[0][1] is not None
            and not parts[0][2])


def render(template: str, values: dict):
    """A template against one document's values, or None when it cannot fill.

    None rather than a partial rendering: a half-filled spelling would
    resolve for some documents and not others, with nothing saying which."""
    try:
        if lone_field(template):
            import string
            name = list(string.Formatter().parse(template))[0][1]
            got = string.Formatter().get_field(name, (), values)[0]
            return got if got not in (None, "") else None
        out = template.format(**values).strip()
    except (KeyError, IndexError, AttributeError, TypeError, ValueError):
        return None
    return out or None


def parse_follow(where: str, raw) -> Follow:
    """A `from = "source[0]"` declaration, or a ValueError naming the fault.

    Shape only. Whether the name is a reference the scheme declares, and
    whether it holds one value or several, needs the whole scheme."""
    import re
    text = str(raw).strip()
    if not text:
        raise ValueError(f"{where}: `from` is empty")
    m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?", text)
    if not m:
        raise ValueError(
            f"{where}: `from = {text!r}` is not a reference — write the field "
            f"name, and an index when it holds several (`source[0]`)")
    return Follow(field=m.group(1),
                  index=None if m.group(2) is None else int(m.group(2)))


def parse(where: str, field: str, raw, follow=None) -> Derived:
    """One `derive = "{template}"` declaration, or a ValueError naming what
    was wrong with it. Shape only — whether the names are fields the scheme
    can hold needs the whole scheme, so that is checked there.

    `follow` is the parsed `from`, when the template renders against a
    referenced document rather than this one (#233)."""
    text = str(raw).strip()
    if not text:
        raise ValueError(f"{where}: `derive` is empty")
    try:
        text.format_map(_Probe())
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{where}: `derive = {text!r}` is not a template "
                         f"`str.format` can render ({exc})") from exc
    read = names_in(text)
    if not read:
        raise ValueError(
            f"{where}: `derive = {text!r}` reads no field, so every document "
            f"would get the same value — which is a default, not a derivation")
    # Self-reference is a cycle within one document and an ordinary read
    # across two — `published` from its source's `published` is the whole
    # point of `from`, and is what this rule must not catch.
    if follow is None and field in read:
        raise ValueError(
            f"{where}: `{field}` derives from itself, which resolves to "
            f"nothing")
    if follow is not None and follow.field in read:
        raise ValueError(
            f"{where}: the template reads `{follow.field}`, which is the "
            f"reference it follows — that is this document's field, not the "
            f"referenced document's, and reading it here says nothing")
    return Derived(field=str(field), template=text, follow=follow)


class _Probe(dict):
    """Answers to any name, so a template's shape can be checked without a
    document — indexing and attributes included, since `{authors[0]}` and
    `{date.year}` are ordinary spellings."""

    def __missing__(self, key):
        return self

    def __getitem__(self, key):
        return self

    def __getattr__(self, name):
        return self

    def __format__(self, spec):
        return ""


# inactive-ok-block: ADR-087 — Proposed, from the same plan; cited for the
# capability it added, not as settled evidence
def value(meta: dict, rule: Derived, resolve=None):
    """The derived value for one document, or None when the template cannot
    be filled.

    Absence is not an error here. A document with no `tags:` has no primary
    topic to compute, and saying so is the tags field's job — reporting it
    twice would name the wrong line as the fix. The same holds across a
    reference: pointing at nothing, at a code that resolves to nothing, or at
    a document that does not carry the field all derive nothing, because each
    already has a check whose finding names the right line.

    Without `from`, only the document's own frontmatter is in scope, and that
    is enough for `{number}` too, now that identity is a field a document
    carries rather than a filename it is parsed out of (ADR-087) — a
    capability this step inherits rather than adds.

    With `from`, `resolve` maps a code to that document's *written*
    frontmatter. A caller that cannot resolve (none was supplied) derives
    nothing rather than guessing."""
    if rule.follow is None:
        return render(rule.template, meta)
    if resolve is None:
        return None
    code = rule.follow.code(meta)
    if code is None:
        return None
    target = resolve(code)
    if not target:
        return None
    return render(rule.template, target)


def written(meta: dict, rules) -> list[str]:
    """The derived fields this document wrote for itself — the finding, since
    a derived field has one source and frontmatter is not it."""
    return [r.field for r in rules if meta.get(r.field) not in (None, "", [])]


def applied(meta: dict, rules, resolve=None) -> dict:
    """`meta` with every derivation resolved onto it.

    A copy: the caller's dict is what the document says, and several checks
    still need to tell the two apart.

    `resolve` is what a `from` derivation reads the other document through;
    every rule sees the document's *written* frontmatter, never a partially
    derived one, so the order rules are applied in cannot matter."""
    if not rules:
        return meta
    out = dict(meta)
    for rule in rules:
        got = value(meta, rule, resolve)
        if got is None:
            out.pop(rule.field, None)
        else:
            out[rule.field] = got
    return out
