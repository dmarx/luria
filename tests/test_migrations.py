"""The migrations ladder (ADR-040): rung 1 (old spellings resolve, warn, and
get modernized) and rung 2 (`luria migrate` executes a spec).

A migrated document carries `formerly:` in its frontmatter; everything else
is derived — the alias map, the `legacy-spellings` warning class, the fixer's
modernize pass. The guards here are fired on the failure they exist for
(DP-6): a reference written in last year's spelling, a fixture code that must
survive, a composed remote code that is another project's namespace, and a
journal link whose frame the sweep must not disturb (#57).
"""
# unlinted-file: — migration fixtures; every code spelling in this suite is a
# deliberate specimen of a pre- or post-migration state, not a claim about
# this repository's documents. The sweep honors this for the same reason the
# scanners do: a quote is not an address.
import subprocess
from pathlib import Path

from luria import aliases, config, doc_refs, lint, migrate, ref_status


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


# ── Rung 2: `luria migrate` ──────────────────────────────────────────────


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)


def _premigration_project(tmp_path, monkeypatch):
    """A project the day before its DP scheme becomes GP — documents,
    citations in three frames, a fixture number, and two remotes: SG is
    another project (its namespace survives), LU mirrors this one (its
    composed codes follow the rename)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\ndesign_principles = "docs/design-principles.md"\n'
        '[luria.schemes.DP]\ndir = "record/principles.d"\n'
        'render = "document"\noutput = "docs/design-principles.md"\n'
        '[luria.remotes.SG]\nrepo = "example/strata-g"\n'
        '[luria.remotes.SG.schemes.DP]\n'
        'document = "docs/design-principles.md"\n'
        '[luria.remotes.LU]\nrepo = "example/this-project"\n'
        '[luria.remotes.LU.schemes.DP]\n'
        'document = "docs/design-principles.md"\n'
    )
    (tmp_path / "docs" / "design-principles.md").write_text(
        "<!-- GENERATED -->\n\n# Principles\n\n"
        '<a name="dp-4"></a>\n\n## 4. Fourth value\n')
    dp_dir = tmp_path / "record" / "principles.d"
    dp_dir.mkdir(parents=True)
    for n, title in ((1, "First value"), (4, "Fourth value")):
        (dp_dir / f"DP-{n:03d}.md").write_text(
            f"---\nstatus: Active\ntitle: '{title}'\ntags:\n- record\n"
            f"date: '2026-01-01'\n---\n\n# DP-{n:03d}: {title}\n\n"
            f"Body citing DP-1 sometimes.\n")
    (tmp_path / "docs" / "notes.md").write_text(
        "# Notes\n\n"
        "Bare DP-4 and a link [DP-4](design-principles.md#dp-4).\n"
        "Fixture DP-018 is nobody's document.\n"
        "Foreign SG-DP-4 belongs to strata-g.\n"
        "Mirrored LU-DP-004 follows this project.\n"
        "[theirs](https://example.test/sg/docs/design-principles.md#x)\n")
    entry_dir = tmp_path / "record" / "devlog.d" / "2026" / "08" / "01"
    entry_dir.mkdir(parents=True)
    (entry_dir / "120000.md").write_text(
        "---\ntitle: 'An entry'\ncreated: '2026-08-01T12:00:00'\ntags: []\n"
        "---\n\nBook-frame link: [DP-4](../../record/../docs/"
        "design-principles.md#dp-4).\n")
    mig_dir = tmp_path / "record" / "migrations.d"
    mig_dir.mkdir(parents=True)
    (mig_dir / "0001-dp-to-gp.toml").write_text(
        'title = "DP becomes GP"\nissue = "#29"\n\n'
        '[[operations]]\nop = "rename_scheme"\nfrom = "DP"\nto = "GP"\n'
        'output = "docs/guiding-principles.md"\nremotes = ["LU"]\n')
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "before")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path


def test_dry_run_prints_the_plan_and_changes_nothing(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    before = {p: p.read_text() for p in root.rglob("*.md")}
    migrate.run("0001", dry_run=True)
    out = capsys.readouterr().out
    assert "DP-001 -> GP-001" in out and "DP-004 -> GP-004" in out
    assert "LU-DP-004 -> LU-GP-004" in out
    assert "design-principles.md -> guiding-principles.md" in out
    assert {p: p.read_text() for p in root.rglob("*.md")} == before


def test_rename_scheme_end_to_end(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    migrate.run("0001")

    dp_dir = root / "record" / "principles.d"
    assert not (dp_dir / "DP-004.md").exists()
    moved = (dp_dir / "GP-004.md").read_text()
    assert "formerly:\n- DP-4\n" in moved, "identity stamped"
    assert "# GP-004: Fourth value" in moved, "own heading swept"
    assert "citing GP-1 sometimes" in moved, "cross-citations swept"

    config_text = (root / "luria.toml").read_text()
    assert "[luria.schemes.GP]" in config_text
    assert "[luria.schemes.DP]" not in config_text
    assert 'design_principles = "docs/guiding-principles.md"' in config_text
    assert 'output = "docs/guiding-principles.md"' in config_text
    assert "[luria.remotes.LU.schemes.GP]" in config_text, "mirror follows"
    assert config_text.count('document = "docs/guiding-principles.md"') == 1
    assert "[luria.remotes.SG.schemes.DP]" in config_text, "theirs stays"
    assert 'document = "docs/design-principles.md"' in config_text, \
        "SG's own path untouched by the section-aware pass"

    assert not (root / "docs" / "design-principles.md").exists(), \
        "a generated view is removed, not renamed — the next index rebuilds it"

    notes = (root / "docs" / "notes.md").read_text()
    assert "Bare GP-4 and a link [GP-4](guiding-principles.md#gp-4)." in notes
    assert "Fixture DP-018 is nobody's document." in notes, "not in the mapping"
    assert "Foreign SG-DP-4 belongs to strata-g." in notes, "their namespace"
    assert "Mirrored LU-GP-004 follows this project." in notes
    assert "https://example.test/sg/docs/design-principles.md#x" in notes, \
        "a foreign URL never follows a local path pair"

    entry = next((root / "record" / "devlog.d").rglob("1*.md")).read_text()
    assert "[GP-4](../../record/../docs/guiding-principles.md#gp-4)" in entry, \
        "history swept, and the link's frame untouched (#57)"

    spec = (root / "record" / "migrations.d" / "0001-dp-to-gp.toml").read_text()
    assert 'from = "DP"' in spec, "the spec remembers the old spelling"

    # Full circle into rung 1: the fresh config resolves old spellings.
    config.reset()
    aliases.reset()
    assert aliases.alias_map() == {"DP-001": "GP-001", "DP-004": "GP-004"}


def test_move_doc_renumbers_and_stamps(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.toml").write_text(
        (root / "luria.toml").read_text()
        + '[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / "record" / "values.d").mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / "record" / "migrations.d" / "0002-promote.toml"
    mig.write_text('title = "DP-4 becomes a value"\n\n'
                   '[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\n')
    migrate.run("0002")
    moved = (root / "record" / "values.d" / "VAL-001.md").read_text()
    assert "formerly:\n- DP-4\n" in moved
    assert not (root / "record" / "principles.d" / "DP-004.md").exists()
    notes = (root / "docs" / "notes.md").read_text()
    assert "Bare VAL-1" in notes
    assert "Fixture DP-018" in notes


def test_move_doc_supersede_copies_and_tombstones(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.toml").write_text(
        (root / "luria.toml").read_text()
        + '[luria.schemes.VAL]\ndir = "record/values.d"\n')
    (root / "record" / "values.d").mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / "record" / "migrations.d" / "0002-supersede.toml"
    mig.write_text('title = "DP-4 superseded by a value"\n\n'
                   '[[operations]]\nop = "move_doc"\ndoc = "DP-4"\nto = "VAL"\n'
                   'strategy = "supersede"\n')
    migrate.run("0002")
    old = (root / "record" / "principles.d" / "DP-004.md").read_text()
    assert "status: Superseded — by VAL-001" in old
    assert (root / "record" / "values.d" / "VAL-001.md").exists()
    notes = (root / "docs" / "notes.md").read_text()
    assert "Bare DP-4" in notes, "supersede mode rewrites nothing"


def test_new_migration_scaffolds_a_numbered_spec(tmp_path, monkeypatch):
    _premigration_project(tmp_path, monkeypatch)
    from luria import new
    path = new.new_entry("migration", {"title": "A second move"}, None)
    assert path.name == "0002-a-second-move.toml"
    assert 'title = "A second move"' in path.read_text()


def test_the_sweep_honors_unlinted_file(tmp_path, monkeypatch, capsys):
    """A file that declares its references quotes (`unlinted-file`, #37) is
    a page of specimens — the sweep leaves every spelling in it alone."""
    root = _premigration_project(tmp_path, monkeypatch)
    specimen = root / "docs" / "specimens.md"
    specimen.write_text(
        "<!-- unlinted-file: — every code here is a specimen -->\n\n"
        "# Specimens\n\nThe old spelling DP-4 preserved verbatim.\n")
    _git(root, "add", "-A")
    migrate.run("0001")
    assert "The old spelling DP-4 preserved verbatim." in specimen.read_text()
