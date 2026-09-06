# luria/templates.py
"""A scheme's form, checked against the scheme's contract (#169).

`_template.md` is exempt from every *document* check, and rightly so: its
codes are placeholders, its status is a prompt, and reporting them is a
finding about a form nobody filed. `Scheme.is_template` says as much —
"a form, not a document" — and `ref_status`, `site` and `lint` all skip it.

The cost of that exemption is that the template became the only file in the
record which states the schema and is never compared to it. It is also the
file every document is a copy of, so a drift between `luria.toml` and the
form does not produce one wrong document. It produces every document filed
afterwards, in the wrong shape, and the lint calls each of them clean —
because each of them *is* clean. Legal input in the wrong shape.

That is not hypothetical. A project decided its `source:` field could hold
several codes, changed `luria.toml`, and left the template saying
`source: LIT-000`. Three weeks and 34 documents later, 140 of 144 entries
were single-sourced, and the four exceptions were the ones a person had
edited by hand while writing the decision. The capability was live,
enforced, correct — and inert.

**Shape, never values.** A template's `LIT-000` must stay a placeholder that
resolves to nothing; checking it would re-import the exact finding the
exemption exists to suppress. What this checks is whether a document copied
from the form starts out in the shape the contract describes: a `many` field
scaffolded as a list, a scalar one as a scalar, a required one present at
all. Each of those is mechanically decidable and always wrong when it fires,
which is the bar for joining the lint rather than being a report.

**Required fields only, for absence.** A form prompts for what an entry must
carry; an optional field is the author's to add, and demanding every one in
the template would make each document carry keys it does not want. An
optional field that *is* scaffolded is checked for shape all the same —
absent is a choice, present-and-wrong is copied.

"Required" is read against the form's own frontmatter, so a conditional
requirement (`required_when`, #170) is judged by the status the form
scaffolds. A practice template that starts a document at `Proposed`, in a
scheme where a proposed practice must say what would settle it, should prompt
for that field — it is going to be required the moment the document exists.
"""

from __future__ import annotations

import re

from .adr_index import parse_frontmatter
from .config import current
from .contract import _cite, for_scheme

TEMPLATE_NAME = "_template.md"


def _line_of(text: str, field: str) -> int:
    """Where the field is written, so the finding is clickable."""
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(rf"^{re.escape(field)}\s*:", line):
            return number
    return 1


def rows() -> list[str]:
    """One line per template that contradicts its scheme's contract."""
    cfg = current()
    found: list[str] = []
    for scheme in cfg.schemes.values():
        path = scheme.dir / TEMPLATE_NAME
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        if not meta:
            # No frontmatter at all is the docs checks' finding, not a
            # shape disagreement; duplicating it would report one mistake
            # twice in two vocabularies.
            continue
        where = cfg.rel(path)
        for field in for_scheme(scheme).fields:
            if field.builtin:
                continue
            cite = _cite(field.because)
            if field.name not in meta:
                if field.demanded(meta):
                    found.append(
                        f"{where}:1: `{field.name}:` is required but not "
                        f"scaffolded — a document copied from this form starts "
                        f"in violation {cite}")
                continue
            line = _line_of(text, field.name)
            listed = isinstance(meta[field.name], list)
            if field.many and not listed:
                found.append(
                    f"{where}:{line}: `{field.name}:` is scaffolded as one "
                    f"value, but the contract declares it `many` — a document "
                    f"copied from this form starts single-valued {cite}")
            elif listed and not field.many:
                found.append(
                    f"{where}:{line}: `{field.name}:` is scaffolded as a list, "
                    f"but the contract declares it one value — a document "
                    f"copied from this form starts with a list where a code "
                    f"belongs {cite}")
    return sorted(found)
