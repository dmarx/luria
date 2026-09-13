"""A key in the schema is a promise; something has to keep it.

`docs/configuration.md` is generated from the dataclasses, so adding a field
to `Site` publishes a documented, defaulted, parsed setting with no further
work — including, if nobody notices, one that nothing reads. That is worse
than an undocumented feature: the reference tells a reader to set `graph`,
`luria.toml` accepts it, `config.load` parses it into a `Path`, and the site
comes out exactly as it would have without it. Nothing fails, so nothing
says so.

It happened here. #245's branch carried `graph`, `graph_height` and
`graph_depth` across from the stack that implements them, and main shipped
the whole surface — DEFAULTS entry, dataclass field, docstring, `_site()`
reader, reference row — with no `luria/site_graph.py` behind it.

The check is deliberately crude: a field is *consumed* if some module other
than `config.py` mentions it on a receiver named `site`, which is how every
real reader spells it (`site.icon`, `cfg.site.publish`,
`current().site.base_url`). Crude is the point — it is the cheapest thing
that would have caught the mistake, and a reader sophisticated enough to
follow a dynamic lookup would also be sophisticated enough to miss this.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from luria.config import Site

LURIA = Path(__file__).resolve().parent.parent / "luria"


def _consumers() -> dict[str, list[str]]:
    """Each `Site` field → the modules that read it off a `site` receiver."""
    sources = {p.name: p.read_text(encoding="utf-8")
               for p in LURIA.rglob("*.py") if p.name != "config.py"}
    return {f.name: sorted(name for name, text in sources.items()
                           if re.search(rf"\bsite\.{f.name}\b", text))
            for f in dataclasses.fields(Site)}


def test_every_site_setting_is_read_by_something():
    found = _consumers()
    unread = sorted(name for name, mods in found.items() if not mods)
    assert not unread, (
        f"[luria.site] {', '.join(unread)} appear(s) in the schema and the "
        "generated reference, but no module reads it. Either wire the "
        "setting up or take it out — a documented key that does nothing is "
        "a promise the tool does not keep.")


def test_the_check_can_tell_a_read_field_from_an_unread_one():
    """The positive control. `_consumers()` returning "everything is fine"
    because its pattern matches nothing is the failure mode that would make
    the test above worthless, so prove the instrument moves: a field that is
    genuinely read is found, and an invented one is not."""
    found = _consumers()
    assert found["base_url"], "base_url is read all over the tree and was not found"
    assert "site.py" in found["icon"], found["icon"]

    sources = {p.name: p.read_text(encoding="utf-8")
               for p in LURIA.rglob("*.py") if p.name != "config.py"}
    invented = [name for name, text in sources.items()
                if re.search(r"\bsite\.nothing_reads_this\b", text)]
    assert invented == [], "the pattern matched a field that does not exist"
