"""The code a scheme document's `# CODE: title` heading carries.

The heading repeats two things the document already states: its title
(`title:`, which `lint.check_title` holds the words to) and its code, which
is the filename (ADR-013). The title check strips the code off before
comparing, so until this module the code half was guarded by nothing — and
Nucleation's NOTE-1341 carried a temporary code that named no document in its
heading through concretization, the only file in that record left so.

One reader, used by the lint that reports a heading naming another code and
by `luria concretize`, which writes the code it assigns into the heading
(DP-4).
"""

from __future__ import annotations

import re
from pathlib import Path

from .adr_index import TITLE_RE

_SEP = r"\s*(?::|—|-)"


def _body_start(text: str) -> int:
    """Offset of the body: past the frontmatter, the same split as
    `adr_index.parse_frontmatter`, so a `#` comment in the YAML is never
    mistaken for the heading."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 3)
        if end != -1:
            return end + 5
    return 0


def _heading(body: str) -> re.Match | None:
    """The first `#` line of the body — the line `check_title` reads."""
    return re.search(r"^#.*$", body, flags=re.MULTILINE)


def written_code(scheme, body: str) -> str | None:
    """The code the heading carries as written, or None for a heading with
    no code slot (`# Title`), or no heading at all.

    The scheme's own prefix is tried first, so a prefix with a hyphen in it
    (`FX-ADR`) is read whole rather than cut at its first hyphen by the
    generic shape."""
    line = _heading(body)
    if line is None:
        return None
    own = re.match(rf"^#\s*({re.escape(scheme.prefix)}-[A-Za-z0-9]+){_SEP}",
                   line.group(0))
    if own:
        return own.group(1)
    other = TITLE_RE.match(line.group(0))
    if other:
        return re.match(r"^#\s*([A-Z]+-[A-Za-z0-9]+)", line.group(0)).group(1)
    return None


def own_code(scheme, path: Path) -> str:
    """The document's own code: its temporary code if it has one, else the
    code of its number (the frontmatter's, else the filename's)."""
    tail = scheme.temp_of(path)
    if tail is not None:
        return f"{scheme.prefix}-{tail}"
    return scheme.code(scheme.number_of(path))


def _is_own(scheme, path: Path, code: str) -> bool:
    """`code` names this document. A number is compared as a number, so a
    heading written `ADR-13` on `ADR-013.md` is the same code spelled
    without its padding, not another one."""
    if code == own_code(scheme, path):
        return True
    m = re.fullmatch(rf"{re.escape(scheme.prefix)}-(\d+)", code)
    return (m is not None and scheme.temp_of(path) is None
            and int(m.group(1)) == scheme.number_of(path))


def foreign_code(scheme, path: Path, body: str) -> str | None:
    """The code the heading carries when it is not this document's own."""
    code = written_code(scheme, body)
    if code is None or _is_own(scheme, path, code):
        return None
    return code


def with_code(scheme, text: str, code: str) -> tuple[str, str | None]:
    """`text` with its heading's code replaced by `code`, and the code the
    heading carried before (None when there was no code slot to write — a
    `# Title` heading is left as its author wrote it)."""
    start = _body_start(text)
    body = text[start:]
    was = written_code(scheme, body)
    if was is None or was == code:
        return text, was
    line = _heading(body)
    fixed = line.group(0).replace(was, code, 1)
    return (text[:start] + body[:line.start()] + fixed + body[line.end():],
            was)
