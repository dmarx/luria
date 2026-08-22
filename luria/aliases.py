from __future__ import annotations
import re
from .adr_index import parse_frontmatter
from .config import Config, current
CODE_RE = re.compile('^([A-Za-z]{2,10})[- ]0*(\\d{1,4})$')
_cache: tuple[Config, dict[str, str]] | None = None

def canon(code: str) -> str | None:
    m = CODE_RE.match(code.strip())
    return f'{m.group(1).upper()}-{int(m.group(2)):03d}' if m else None

def alias_map(cfg: Config | None=None) -> dict[str, str]:
    global _cache
    cfg = cfg or current()
    if _cache is not None and _cache[0] is cfg:
        return _cache[1]
    out: dict[str, str] = {}
    for scheme in cfg.schemes.values():
        for number, path in scheme.documents().items():
            meta, _ = parse_frontmatter(path.read_text())
            for old in meta.get('formerly') or []:
                old_code = canon(str(old))
                if old_code is not None:
                    out[old_code] = scheme.code(number)
    _cache = (cfg, out)
    return out

def reset() -> None:
    global _cache
    _cache = None

def split(code: str) -> tuple[str, int]:
    prefix, number = code.rsplit('-', 1)
    return (prefix, int(number))
