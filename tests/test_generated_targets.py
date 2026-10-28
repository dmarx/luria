# tests/test_generated_targets.py
"""`CLAUDE.md`'s "never edit a generated file" list is derived in its
template (ADR-130), from what the record's config says it renders. The
template is then a second derivation of what `luria index` writes, beside
the generator itself, so this guards the property and not the list (DP-003):
every file the index writes lies at or under a path the bootloader names.
"""

from __future__ import annotations

import re

from luria import adr_index, config, views


def named_paths() -> list[str]:
    text = views.render(config.current().views["bootloader"])
    section = text.split("**Never edit a generated file.**", 1)[1]
    section = section.split("\n- **", 1)[0]
    return re.findall(r"^  - .*: `([^`]+)`$", section, re.MULTILINE)


def test_the_bootloader_names_every_file_the_index_writes():
    cfg = config.current()
    named = [cfg.root / p for p in named_paths()]
    missing = [cfg.rel(out) for out in adr_index.outputs(nested=False)
               if not any(out == n or n in out.parents for n in named)]
    assert missing == []


def test_it_names_each_kind_of_view():
    named = named_paths()
    for path in ("docs/decisions", "docs/design-principles.md",
                 "docs/devlog", "CLAUDE.md", "docs/reports",
                 "docs/record.md", "docs/configuration.md"):
        assert path in named


def test_paths_and_scheme_render_kinds_reach_a_template():
    view = config.current().views["bootloader"]
    record = views._Record(view.output)
    kinds = {s.prefix: s.render for s in record.schemes()}
    assert kinds == {"ADR": "index", "DP": "document"}
    assert record.paths().record == "docs/record.md"
    assert [v.output for v in record.views()] == ["CLAUDE.md"]
