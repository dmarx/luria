# tests/test_generated_targets.py
"""What luria generates, named once (DP-004): `Config.generated()` lists the
targets with a reader's label, `is_generated` asks it, and a template can
print it, so a bootloader's "never edit these" cannot drift from what the
generator actually writes (DP-003).
"""

from __future__ import annotations

from luria import adr_index, config, views


def covered(cfg, path) -> bool:
    return any(t.covers(path) for t in cfg.generated())


def test_every_file_the_index_writes_is_a_named_target():
    # The property, not the list (DP-003): whatever `luria index` renders,
    # some target names it. A nested record's views are its own config's to
    # name (ADR-078), so each record is asked under its own.
    from luria.config import rooted
    cfg = config.current()
    missing = [cfg.rel(p) for p in adr_index.outputs(nested=False)
               if not covered(cfg, p)]
    for record in cfg.nested_records():
        with rooted(record):
            inner = config.current()
            missing += [inner.rel(p) for p in adr_index.outputs(nested=False)
                        if not covered(inner, p)]
    assert missing == []


def test_every_file_the_index_writes_in_a_fixture_is_named(project):
    cfg = config.current()
    missing = [cfg.rel(p) for p in adr_index.outputs() if not covered(cfg, p)]
    assert missing == []


def test_is_generated_is_the_targets_question():
    cfg = config.current()
    for path in adr_index.outputs(nested=False):
        assert cfg.is_generated(path) == covered(cfg, path)
    source = cfg.root / "record/decisions.d/ADR-001.md"
    assert not cfg.is_generated(source) and not covered(cfg, source)


def test_each_target_has_a_label_and_a_path():
    cfg = config.current()
    found = {cfg.rel(t.shown): t.label for t in cfg.generated()}
    assert "docs/decisions" in found
    assert "docs/design-principles.md" in found
    assert "docs/reports" in found
    assert "docs/record.md" in found
    assert all(found.values())


def test_a_template_can_list_them():
    cfg = config.current()
    view = cfg.views["bootloader"]
    text = views.render(view)
    assert "`docs/design-principles.md`" in text
    assert "`docs/record.md`" in text
    assert "`CLAUDE.md`" in text      # the bootloader names itself
