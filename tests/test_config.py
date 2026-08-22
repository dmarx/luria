from luria import config

def load_text(tmp_path, text):
    return config.load(tmp_path, text=text)

def test_a_declared_family_replaces_the_default(tmp_path):
    cfg = load_text(tmp_path, '[luria.schemes.RFC]\ndir = "rfcs"\n')
    assert set(cfg.schemes) == {'RFC'}, 'declaring RFC removed the ADR default'

def test_an_undeclared_family_keeps_the_default(tmp_path):
    cfg = load_text(tmp_path, '[luria]\nissue_url = ""\n')
    assert set(cfg.schemes) == {'ADR'}
    assert set(cfg.journals) == {'devlog'}

def test_a_declared_scheme_key_is_unset_by_omission(tmp_path):
    cfg = load_text(tmp_path, '[luria.schemes.ADR]\ndir = "decisions"\n')
    assert cfg.schemes['ADR'].output is None
    assert cfg.schemes['ADR'].view == cfg.schemes['ADR'].dir

def test_settings_tables_still_merge_per_key(tmp_path):
    cfg = load_text(tmp_path, '[luria.paths]\ndocs = "documentation"\n')
    assert cfg.docs == tmp_path / 'documentation'
    assert cfg.reports == tmp_path / 'docs' / 'reports', 'reports kept default'

def test_declaring_journals_does_not_touch_schemes(tmp_path):
    cfg = load_text(tmp_path, '[luria.journals.log]\ndir = "log.d"\noutput = "docs/log"\n')
    assert set(cfg.journals) == {'log'}
    assert set(cfg.schemes) == {'ADR'}
