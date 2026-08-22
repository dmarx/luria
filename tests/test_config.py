"""The two merge rules, split by what a table is (ADR-047).

A settings table merges per key — setting `docs` must not clear `reports`. A
family table is replaced whole when declared — its entries are named by the
project, and "you get the ones you wrote" is the only reading under which a
family can shrink. Every case here parses config text directly through
`config.load(text=...)`, the same path `luria init --config` plans from.
"""
from luria import config


def load_text(tmp_path, text):
    return config.load(tmp_path, text=text)


def test_a_declared_family_replaces_the_default(tmp_path):
    cfg = load_text(tmp_path, '[luria.schemes.RFC]\ndir = "rfcs"\n')
    assert set(cfg.schemes) == {"RFC"}, "declaring RFC removed the ADR default"


def test_an_undeclared_family_keeps_the_default(tmp_path):
    cfg = load_text(tmp_path, '[luria]\nissue_url = ""\n')
    assert set(cfg.schemes) == {"ADR"}
    assert set(cfg.journals) == {"devlog"}


def test_a_declared_scheme_key_is_unset_by_omission(tmp_path):
    """The sharp edge the old rule had: `output` inherited `docs/decisions`
    from the default ADR entry, so the documented way to keep an existing
    layout silently relocated the index."""
    cfg = load_text(tmp_path, '[luria.schemes.ADR]\ndir = "decisions"\n')
    assert cfg.schemes["ADR"].output is None
    assert cfg.schemes["ADR"].view == cfg.schemes["ADR"].dir


def test_settings_tables_still_merge_per_key(tmp_path):
    """`paths` is Luria's vocabulary, not the project's — setting one key must
    not clear the others, or every partial override becomes a broken config."""
    cfg = load_text(tmp_path, '[luria.paths]\ndocs = "documentation"\n')
    assert cfg.docs == tmp_path / "documentation"
    assert cfg.reports == tmp_path / "docs" / "reports", "reports kept default"


def test_declaring_journals_does_not_touch_schemes(tmp_path):
    """Replacement is per family: each table is judged on its own presence."""
    cfg = load_text(tmp_path, '[luria.journals.log]\n'
                              'dir = "log.d"\noutput = "docs/log"\n')
    assert set(cfg.journals) == {"log"}
    assert set(cfg.schemes) == {"ADR"}
