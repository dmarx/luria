# luria/view_document.py
"""A record document as a view's template reads it (ADR-tmpi08sj).

Split from `views.py`, which renders a view; this is what a template holds
in its hand while it does: a document whose attributes are its scheme's
fields, and the record of where in the template each one was read.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import jinja2

from .new import UNIVERSAL as SCAFFOLDED

if TYPE_CHECKING:
    from .views import _Record

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")



class _Refused(Exception):
    """A record lookup that failed inside a template. Raised as itself so
    `_located` can tell a lookup failure from a bug in luria."""


class Document:
    """One record document, as a template reads it.

    Its attributes are its scheme's fields, not a list kept here: whatever
    the contract declares (`requires`, `references`, `fields`, derived
    fields), the keys every scheme carries (`title`, `status`, `summary`),
    and anything else its frontmatter holds. Each is read the way the
    contract reads it, so a template sees what the lint and the index see:

    - `status` is its value, without a qualifying note;
    - a vocabulary field left unwritten is its default;
    - a reference field holds documents, so `c.rests_on[0].title` works,
      and a code this record cannot resolve stays a code;
    - a prose field (`summary`, `status_note`, `origin`) is rebased to the
      output's frame;
    - a declared field left unwritten is empty, `[]` when it holds a list.

    A name the scheme does not have is undefined: an error when it is used,
    but `is defined` and `| default` work on it. Item access reads the same
    fields, which is how a field that shares a name with `code`, `body`,
    `part` or `fields` is reached."""

    def __init__(self, adr, record: "_Record"):
        from .adr_index import read_document
        self._adr = adr
        self._record = record
        self._contract = record.contract(adr.scheme)
        self.code = adr.code
        _, body = read_document(adr.path)
        self._lines = _without_title(body).splitlines()

    def _rebased(self, text: str) -> str:
        from .adr_index import rebase_links
        return rebase_links(text, self._record.prefix(self._adr.path))

    def fields(self) -> list[str]:
        """Every field name this document answers to, declared ones first."""
        declared = [f.name for f in self._contract.fields]
        derived = [r.field for r in self._contract.derived]
        return list(dict.fromkeys((*UNIVERSAL, *declared, *derived,
                                   *self._adr.meta)))

    def _field(self, name: str):
        """The field's value, recorded as read where the template read it."""
        kind = "transcluded" if name in TRANSCLUDED_FIELDS else "read"
        value = self._value(name)
        self._record.saw(self, kind, value)
        return value

    def _value(self, name: str):
        from .contract import codes_of, effective_values
        from .doc_refs import PROSE_KEYS
        meta = self._adr.meta
        if name == "status":
            return self._adr.status_value
        if name == "title":
            return self._adr.title
        if name not in self.fields():
            raise KeyError(name)
        spec = next((f for f in self._contract.fields if f.name == name), None)
        raw = meta.get(name)
        if spec is not None and spec.reference is not None:
            found = [self._record.resolve(c) for c in codes_of(spec, raw)]
            return found if spec.many else (found[0] if found else None)
        if spec is not None and spec.vocabulary is not None:
            values = effective_values(spec, raw) or []
            return values if spec.many else (values[0] if values else None)
        if name in PROSE_KEYS:
            return None if raw is None else self._rebased(str(raw).strip())
        if raw is None and spec is not None and spec.many:
            return []
        return raw

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._field(name)
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, name: str):
        return self._field(name)

    @property
    def body(self) -> str:
        text = self._rebased("\n".join(self._lines).strip())
        self._record.saw(self, "transcluded", text)
        return text

    def part(self, heading: str) -> str:
        """The section under `heading`, without the heading line, up to the
        next heading at its level or above. Its subsections come with it."""
        found = _section(self._lines, heading)
        if found is None:
            raise _Refused(f"No such part: {self.code} has no heading "
                           f"{heading!r}")
        text = self._rebased("\n".join(found).strip())
        self._record.saw(self, "transcluded", text)
        return text

    def __str__(self) -> str:
        self._record.saw(self, "read", self.code)
        return self.code


# The keys every scheme's documents carry whether or not the scheme declares
# them, which are the ones `luria new` takes for every scheme. `body` is the
# document's text, not a frontmatter key, and is a member of its own.
UNIVERSAL = tuple(k for k in SCAFFOLDED if k != "body")

# A read of these is the document's assertion carried into the output, which
# is what makes it a transclusion; reading a title, a status or a reference
# names the document without asserting what it says. `status_note` is prose
# but not the claim: it is the record saying why the claim stands as it does.
TRANSCLUDED_FIELDS = ("summary", "origin")


@dataclass(frozen=True)
class Site:
    """Where in a template a document was read, and how."""
    template: str           # the file the read is in, an `include` included
    line: int
    kind: str               # "read" or "transcluded"


@dataclass(frozen=True)
class Read:
    """Everything one render read of one document."""
    code: str
    status: str
    retired: bool           # its status is its scheme's `retires_on`
    successors: tuple[str, ...]
    sites: tuple[Site, ...]
    # A hash of every value the render read from this document, in the
    # order it read them: what a pinned view endorses (`view_pins`).
    digest: str = ""


def stable(value) -> str:
    """`value` as text that is the same in every process: a document is its
    code, never the object's address, and a list is its elements."""
    if isinstance(value, Document):
        return value.code
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(stable(v) for v in value) + "]"
    return repr(value)


def _site() -> tuple[str, int]:
    """The template file and line the innermost template frame is on.

    Jinja compiles a template to Python whose globals carry the template,
    and the template maps a compiled line back to its source line: the same
    mapping its tracebacks use. An `include`d file is a template of its own,
    so a read inside one is sited there."""
    frame = sys._getframe(1)
    while frame is not None:
        template = frame.f_globals.get("__jinja_template__")
        if template is not None:
            return (template.name or "",
                    template.get_corresponding_lineno(frame.f_lineno))
        frame = frame.f_back
    return "", 0


class _Undefined(jinja2.StrictUndefined):
    """Strict, and specific about a document: names the fields it has."""

    @property
    def _undefined_message(self) -> str:
        obj = self._undefined_obj
        if isinstance(obj, Document) and self._undefined_hint is None:
            return (f"{obj.code} has no field {self._undefined_name!r} "
                    f"(fields: {', '.join(obj.fields())})")
        return super()._undefined_message


def _without_title(body: str) -> str:
    """The body below its `# CODE: title` heading. A template transcludes a
    body under a heading of its own, and the title is `.title`."""
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if line.strip():
            if line.startswith("# "):
                return "\n".join(lines[i + 1:])
            break
    return body


def _section(lines: list[str], heading: str) -> list[str] | None:
    """The lines under the first heading titled `heading`, outside fences."""
    fenced = False
    start, level = None, 0
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if fenced or not (m := HEADING_RE.match(line)):
            continue
        depth = len(m.group(1))
        if start is None:
            if m.group(2) == heading:
                start, level = i + 1, depth
        elif depth <= level:
            return lines[start:i]
    return None if start is None else lines[start:]
