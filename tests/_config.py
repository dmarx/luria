# tests/_config.py
"""Compose a test config out of fragments.

Config was TOML, and TOML tables concatenate: a fixture built its document by
gluing a base and an extra table together with an f-string. YAML mappings do
not concatenate — two fragments both declaring `schemes:` is a duplicate key,
not a merge — so composition became structural instead of textual when the
config moved (ADR-098).

That is the better shape anyway: a test that says which keys it is adding is
saying something a reader can check, where `BASE + extra` said only that some
text arrived.
"""
from __future__ import annotations

import yaml


def _deep(into: dict, extra: dict) -> dict:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(into.get(key), dict):
            _deep(into[key], value)
        else:
            into[key] = value
    return into


def merged(*parts: str | dict) -> str:
    """One YAML document from several fragments, later parts winning."""
    out: dict = {}
    for part in parts:
        if not part:
            continue
        loaded = yaml.safe_load(part) if isinstance(part, str) else part
        if loaded is None:
            continue
        if not isinstance(loaded, dict):
            raise TypeError(
                f"a config fragment has to be a mapping, not "
                f"{type(loaded).__name__}: {part!r}")
        _deep(out, loaded)
    return yaml.dump(out, sort_keys=False, allow_unicode=True, width=200)
