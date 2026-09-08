"""Every spelling a document answers to besides its code (ADR-040, #219).

Two kinds, and the difference is the whole of how the fixer behaves:

- **Formerly** — a spelling this document *used* to have, from `formerly:`
  frontmatter. A migrated or concretized document carries its past there,
  the only persistent bookkeeping a migration leaves in the record: config
  describes the present, documents carry their pasts. A reference written
  this way still resolves, draws a `legacy-spellings` warning, and
  `luria link --fix` **rewrites it away**. That loop is what makes a
  migration safe to land while branches are in flight.

- **Also known as** — a spelling derived right now from the document's own
  frontmatter, where the scheme declares a template:

      [luria.schemes.LIT]
      alias = "LIT-{authors[0]}-{year}-{number}"

  `LIT-Kingma-2014-041` resolves to `LIT-041`, and the fixer **leaves it
  alone**: recovering an identifier a reader can interpret is the point, and
  canonicalizing it on write would undo that on the first `--fix`.

The two are opposite instructions to the same fixer over one map, which is
why each entry carries its kind rather than the caller guessing from shape.

An alias is recomputed on every read and is therefore always true — until
someone writes one down. Correct an author and the old spelling stops
resolving, so `luria repair` moves the superseded spelling into `formerly:`,
where it becomes the other kind and keeps resolving forever.

Nothing here is hand-maintained: delete the field, or the template, and the
alias is gone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .adr_index import parse_frontmatter
from .config import Config, current

CODE_RE = re.compile(r"^([A-Za-z]{2,10})[- ]0*(\d{1,4})$")

# An alias tail is anything a template can render: words, digits, hyphens.
# Deliberately loose, because precision comes from the map rather than from
# the pattern — a widened shape that matched prose would be a disaster, and
# `legacy_spellings` already names the rule: a string that resolves to no
# document is not a reference. So this decides what to *look up*, never what
# to accept.
ALIAS_RE = re.compile(r"^([A-Za-z]{2,10})-([A-Za-z0-9][A-Za-z0-9.-]{0,80})$")

FORMERLY, ALSO_KNOWN_AS = "fka", "aka"

# Keyed on the Config instance: `config.reset()` mints a new one, so tests
# and long processes invalidate for free without a reset of their own.
_cache: tuple[Config, dict[str, "Alias"]] | None = None


@dataclass(frozen=True)
class Alias:
    """One spelling, what it resolves to, and which kind it is."""
    spelling: str
    code: str
    number: int
    kind: str

    @property
    def superseded(self) -> bool:
        """Whether `luria link --fix` rewrites this away. A past spelling is
        rewritten; a derived one is what the author meant to write."""
        return self.kind == FORMERLY


def canon(code: str) -> str | None:
    """`dp-4`, `DP 4` and `DP-004` are one spelling: `DP-004`."""
    m = CODE_RE.match(code.strip())
    return f"{m.group(1).upper()}-{int(m.group(2)):03d}" if m else None


def render(template: str, meta: dict, scheme, number: int) -> str | None:
    """One document's alias, or None when the template cannot be filled.

    `str.format` over the document's own frontmatter, plus the three values
    the scheme knows — the same template vocabulary a remote URI renders
    through, fed from a different source. A template naming a field this
    document lacks renders nothing rather than a half-spelling: a partial
    alias would resolve for some documents and not others, silently."""
    values = dict(meta)
    values.update(number=number, prefix=scheme.prefix,
                  code=scheme.code(number))
    try:
        out = template.format(**values).strip()
    except (KeyError, IndexError, AttributeError, TypeError):
        return None
    return out or None


def alias_map(cfg: Config | None = None) -> dict[str, Alias]:
    """Every spelling → what it resolves to, across every scheme.

    Derived fresh from the documents and cached per config. An entry that
    outlived the frontmatter it came from would be exactly the hand-kept
    ledger ADR-040 rejected — so nothing is stored, only projected.

    The cache is what makes derived aliases affordable: resolution used to
    scan every document on demand, which was fine while the only aliases
    were temporary codes nobody writes on purpose. A spelling people *choose*
    to cite makes that path hot (#219)."""
    global _cache
    cfg = cfg or current()
    if _cache is not None and _cache[0] is cfg:
        return _cache[1]
    out: dict[str, Alias] = {}
    for scheme in cfg.schemes.values():
        for number, path in scheme.documents().items():
            meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            code = scheme.code(number)
            if scheme.alias:
                spelling = render(scheme.alias, meta, scheme, number)
                # A derived spelling that collides with a real code loses to
                # it: a document's own name outranks another's nickname.
                if spelling and canon(spelling) is None:
                    out.setdefault(spelling, Alias(spelling, code, number,
                                                   ALSO_KNOWN_AS))
            for old in meta.get("formerly") or []:
                old_code = canon(str(old)) or str(old).strip()
                if old_code:
                    out[old_code] = Alias(old_code, code, number, FORMERLY)
    _cache = (cfg, out)
    return out


def reset() -> None:
    """Drop the cache — for the migration executor, which edits the very
    frontmatter this map is derived from."""
    global _cache
    _cache = None


def split(code: str) -> tuple[str, int]:
    prefix, number = code.rsplit("-", 1)
    return prefix, int(number)
