"""The migrations ladder (ADR-040), rung 1: old spellings resolve, warn, and
get modernized.

A migrated document carries `formerly:` in its frontmatter; everything else
is derived — the alias map, the `legacy-spellings` warning class, the fixer's
modernize pass. The guards here are fired on the failure they exist for
(DP-6): a reference written in last year's spelling, a fixture code that must
survive, a composed remote code that is another project's namespace.
"""
from pathlib import Path

from luria import aliases, config, doc_refs, lint, ref_status


def _record_project(tmp_path, monkeypatch):
    """A project whose GP-004 used to be DP-4 — the post-migration shape."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\ndesign_principles = "docs/guiding-principles.md"\n'
        '[luria.schemes.GP]\ndir = "record/principles.d"\n'
        'render = "document"\noutput = "docs/guiding-principles.md"\n'
        '[luria.remotes.SG]\nrepo = "example/strata-g"\n'
    )
    gp_dir = tmp_path / "record" / "principles.d"
    gp_dir.mkdir(parents=True)
    (gp_dir / "GP-004.md").write_text(
        "---\nstatus: Active\ntitle: 'A principle'\ntags:\n- record\n"
        "date: '2026-01-01'\nformerly:\n- DP-4\n---\n\n"
        "# GP-004: A principle\n\nBody.\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path


def test_the_alias_map_derives_from_formerly(tmp_path, monkeypatch):
    _record_project(tmp_path, monkeypatch)
    assert aliases.alias_map() == {"DP-004": "GP-004"}


def test_an_old_spelling_is_legacy_not_dangling(tmp_path, monkeypatch):
    root = _record_project(tmp_path, monkeypatch)
    page = root / "docs" / "notes.md"
    page.write_text("# Notes\n\nDecided per DP-4, which still holds.\n")
    result = ref_status.scan(files=[page])
    assert "DP-004" in result.legacy
    assert "DP-004" not in result.dangling
    lines = ref_status.legacy_lines(result)
    assert lines and "DP-004 is now GP-004" in lines[0]


def test_a_spelling_with_no_alias_stays_dangling(tmp_path, monkeypatch):
    """Mapping-driven means exactly that: DP-018 has no `formerly:` answering
    for it, so it is a dangling code, same as before migrations existed."""
    root = _record_project(tmp_path, monkeypatch)
    page = root / "docs" / "notes.md"
    page.write_text("# Notes\n\nThe fixture DP-018 resolves to nothing.\n")
    result = ref_status.scan(files=[page])
    assert "DP-018" in result.dangling
    assert not result.legacy


def test_unresolved_ok_acknowledges_a_kept_spelling(tmp_path, monkeypatch):
    """A quotation of the old spelling is deliberate; the directive that says
    so both silences the warning and stays counted as used."""
    root = _record_project(tmp_path, monkeypatch)
    page = root / "docs" / "notes.md"
    page.write_text(
        "# Notes\n\n<!-- unresolved-ok: DP-4 — quoting the pre-migration "
        "spelling -->\nThe rename turned DP-4 into what it is now.\n")
    result = ref_status.scan(files=[page])
    assert ref_status.legacy_lines(result) == []
    sites = result.legacy["DP-004"]
    assert all(c.excused_by is not None for c in sites)
    assert not ref_status.stale_annotations(result)


def test_modernize_rewrites_only_what_the_map_names(tmp_path, monkeypatch):
    root = _record_project(tmp_path, monkeypatch)
    page = root / "docs" / "notes.md"
    text = (
        "# Notes\n\n"
        "Bare: DP-4 and padded DP-004 and the anchor #dp-4.\n"
        "A wikilink [[DP-4|the old name]] modernizes too.\n"
        "Not in the map: DP-018 stays.\n"
        "Another project's SG-DP-4 is theirs.\n"
        "A quotation `DP-4` is a specimen, not a claim.\n"
        "<!-- unresolved-ok: DP-4 — the sentence below quotes the old name -->\n"
        "The code DP-4 was retired by the rename.\n")
    new, count = doc_refs.modernize(text, page)
    assert "Bare: GP-4 and padded GP-004 and the anchor #gp-4." in new
    assert "[[GP-4|the old name]]" in new
    assert "DP-018 stays" in new
    assert "SG-DP-4 is theirs" in new
    assert "`DP-4` is a specimen" in new
    assert "The code DP-4 was retired" in new, "excused line kept"
    assert "unresolved-ok: DP-4" in new, "the directive itself kept"
    assert count == 4


def test_a_wikilink_in_the_old_spelling_still_resolves(tmp_path, monkeypatch):
    root = _record_project(tmp_path, monkeypatch)
    target = doc_refs.wikilink_target("DP-4", root / "docs" / "notes.md")
    assert target == "guiding-principles.md#gp-4"


def test_the_fixer_modernizes_end_to_end(tmp_path, monkeypatch):
    root = _record_project(tmp_path, monkeypatch)
    page = root / "docs" / "notes.md"
    page.write_text("# Notes\n\nStill cites [[DP-4]] the old way.\n")
    new, count = doc_refs.linkify(page.read_text(), page)
    assert "[GP-4](guiding-principles.md#gp-4)" in new
    assert count >= 2, "one spelling upgrade, one wikilink expansion"


def test_legacy_spellings_is_a_failable_class(tmp_path, monkeypatch):
    root = _record_project(tmp_path, monkeypatch)
    page = root / "docs" / "notes.md"
    page.write_text("# Notes\n\nDecided per DP-4.\n")
    assert "legacy-spellings" in lint.FAILABLE
    sections = dict((name, lines) for name, _, lines in lint.status_sections())
    assert any("DP-004 is now GP-004" in line
               for line in sections.get("legacy-spellings", []))


def test_a_scheme_can_require_fields(tmp_path, monkeypatch):
    """The cross-scheme move enabler (ADR-040): the machinery moves the file,
    and the missing field fails lint until a human vouches for it."""
    root = _record_project(tmp_path, monkeypatch)
    (root / "luria.toml").write_text(
        (root / "luria.toml").read_text().replace(
            'render = "document"', 'requires = ["approvers"]\nrender = "document"'))
    config.reset()
    aliases.reset()
    errors: list[str] = []
    lint.check_frontmatter(errors)
    assert any("no `approvers:`" in e and "GP scheme requires" in e
               for e in errors)
    gp = root / "record" / "principles.d" / "GP-004.md"
    gp.write_text(gp.read_text().replace(
        "formerly:\n- DP-4\n", "formerly:\n- DP-4\napprovers:\n- someone\n"))
    errors = []
    lint.check_frontmatter(errors)
    assert errors == []
