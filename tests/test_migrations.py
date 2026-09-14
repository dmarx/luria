"""The migrations ladder (ADR-040): rung 1 (old spellings resolve, warn, and
get modernized) and rung 2 (`luria migrate` executes a spec).

A migrated document carries `formerly:` in its frontmatter; everything else
is derived — the alias map, the `legacy-spellings` warning class, the fixer's
modernize pass. The guards here are fired on the failure they exist for
(DP-6): a reference written in last year's spelling, a fixture code that must
survive, a composed remote code that is another project's namespace, and a
journal link whose frame the sweep must not disturb (#57).

The fixture schemes are `FXL` and `FXM`, from the reserved fixture namespace
(ADR-093): a migration needs two prefixes, and neither may read as a
citation of a real document.
"""
from _config import merged
import json
import subprocess
from pathlib import Path

from luria import (aliases, concretize, config, doc_refs, lint, migrate,
                   ref_status)


def _record_project(tmp_path, monkeypatch):
    """A project whose FXM-004 used to be FXL-4 — the post-migration shape."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "luria.yaml").write_text(
        """
        issue_url: https://example.test/issues/{n}
        paths:
          design_principles: docs/guiding-principles.md
        schemes:
          FXM:
            dir: record/principles.d
            render: document
            output: docs/guiding-principles.md
        remotes:
          SG:
            repo: example/strata-g
        """
    )
    fxm_dir = tmp_path / "record" / "principles.d"
    fxm_dir.mkdir(parents=True)
    (fxm_dir / "FXM-004.md").write_text(
        "---\nstatus: Active\ntitle: 'A principle'\ntags:\n- record\n"
        "date: '2026-01-01'\nformerly:\n- FXL-4\n---\n\n"
        "# FXM-004: A principle\n\nBody.\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path


def test_the_alias_map_derives_from_formerly(tmp_path, monkeypatch):
    _record_project(tmp_path, monkeypatch)
    entries = aliases.alias_map()
    assert {k: v.code for k, v in entries.items()} == {"FXL-004": "FXM-004"}
    # A past spelling, so the fixer rewrites it away — the opposite of what
    # it does with a derived one (#219).
    assert entries["FXL-004"].kind == aliases.FORMERLY
    assert entries["FXL-004"].superseded


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)


def _premigration_project(tmp_path, monkeypatch):
    """A project the day before its FXL scheme becomes FXM — documents,
    citations in three frames, a fixture number, and two remotes: SG is
    another project (its namespace survives), LU mirrors this one (its
    composed codes follow the rename)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "luria.yaml").write_text(
        """
        issue_url: https://example.test/issues/{n}
        paths:
          design_principles: docs/design-principles.md
        schemes:
          FXL:
            dir: record/principles.d
            render: document
            output: docs/design-principles.md
        remotes:
          SG:
            repo: example/strata-g
            schemes:
              FXL:
                document: docs/design-principles.md
          LU:
            repo: example/this-project
            schemes:
              FXL:
                document: docs/design-principles.md
        """
    )
    (tmp_path / "docs" / "design-principles.md").write_text(
        "<!-- GENERATED -->\n\n# Principles\n\n"
        '<a name="fxl-4"></a>\n\n## 4. Fourth value\n')
    fxl_dir = tmp_path / "record" / "principles.d"
    fxl_dir.mkdir(parents=True)
    for n, title in ((1, "First value"), (4, "Fourth value")):
        (fxl_dir / f"FXL-{n:03d}.md").write_text(
            f"---\nstatus: Active\ntitle: '{title}'\ntags:\n- record\n"
            f"date: '2026-01-01'\n---\n\n# FXL-{n:03d}: {title}\n\n"
            f"Body citing FXL-1 sometimes.\n")
    (tmp_path / "docs" / "notes.md").write_text(
        "# Notes\n\n"
        "Bare FXL-4 and a link [FXL-4](design-principles.md#fxl-4).\n"
        "Fixture FXL-018 is nobody's document.\n"
        "Foreign SG-FXL-4 belongs to strata-g.\n"
        "Mirrored LU-FXL-004 follows this project.\n"
        "[theirs](https://example.test/sg/docs/design-principles.md#x)\n")
    entry_dir = tmp_path / "record" / "devlog.d" / "2026" / "08" / "01"
    entry_dir.mkdir(parents=True)
    (entry_dir / "120000.md").write_text(
        "---\ntitle: 'An entry'\ncreated: '2026-08-01T12:00:00'\ntags: []\n"
        "---\n\nBook-frame link: [FXL-4](../../record/../docs/"
        "design-principles.md#fxl-4).\n")
    mig_dir = tmp_path / "record" / "migrations.d"
    mig_dir.mkdir(parents=True)
    (mig_dir / "0001-fxl-to-fxm.yaml").write_text(
        """
        title: FXL becomes FXM
        issue: '#29'
        operations:
        - op: rename_scheme
          from: FXL
          to: FXM
          output: docs/guiding-principles.md
          remotes:
          - LU
        """)
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "before")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    aliases.reset()
    return tmp_path


def _locked_project(tmp_path, monkeypatch):
    """The pre-migration project plus a committed lockfile: pins and
    filename maps for both the mirrored LU remote and the foreign SG one."""
    root = _premigration_project(tmp_path, monkeypatch)
    lock = root / "remotes.lock.json"
    lock.write_text(json.dumps({
        "remotes": {"LU": {"FXL-004": "FXL-004.md"},
                    "SG": {"FXL-004": "fxl-004-a-slug.md"}},
        "pins": {"LU": {"FXL-004": {"endorsed": "sha256:bbb",
                                   "seen": "sha256:ccc"}},
                 "SG": {"FXL-004": {"endorsed": "sha256:aaa",
                                   "seen": "sha256:aaa"}}}},
        indent=2) + "\n")
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "lockfile")
    return root, lock


def test_endorsements_travel_with_a_claimed_rename(tmp_path, monkeypatch):
    """The endorsement is of CONTENT, which a rename does not change — so
    the mirrored LU pin is re-keyed with both hashes intact (drift state
    included: prune-and-re-endorse would have laundered the unreviewed
    `seen`). The foreign SG entries survive byte-for-byte: the lockfile is
    never swept as text, which is what protects `"FXL-004"` under `"SG"`
    from a mask that cannot see nested keys as another project's
    namespace (#135)."""
    root, lock = _locked_project(tmp_path, monkeypatch)
    migrate.run("0001")
    data = json.loads(lock.read_text())
    assert data["pins"]["LU"] == {"FXM-004": {"endorsed": "sha256:bbb",
                                             "seen": "sha256:ccc"}}
    assert data["pins"]["SG"] == {"FXL-004": {"endorsed": "sha256:aaa",
                                             "seen": "sha256:aaa"}}
    # The claimed remote's filename map spells the old world in keys AND
    # values — dropped for re-discovery, while the foreign map stands.
    assert "LU" not in data["remotes"]
    assert data["remotes"]["SG"] == {"FXL-004": "fxl-004-a-slug.md"}


def test_dry_run_plans_the_pin_move_and_keeps_the_lockfile(tmp_path,
                                                          monkeypatch,
                                                          capsys):
    root, lock = _locked_project(tmp_path, monkeypatch)
    before = lock.read_text()
    migrate.run("0001", dry_run=True)
    out = capsys.readouterr().out
    assert "LU pin FXL-004 -> FXM-004" in out and "endorsement travels" in out
    assert lock.read_text() == before


def test_dry_run_prints_the_plan_and_changes_nothing(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    before = {p: p.read_text() for p in root.rglob("*.md")}
    migrate.run("0001", dry_run=True)
    out = capsys.readouterr().out
    assert "FXL-001 -> FXM-001" in out and "FXL-004 -> FXM-004" in out
    assert "LU-FXL-004 -> LU-FXM-004" in out
    assert "design-principles.md -> guiding-principles.md" in out
    assert {p: p.read_text() for p in root.rglob("*.md")} == before


def test_rename_scheme_end_to_end(tmp_path, monkeypatch, capsys):
    root = _premigration_project(tmp_path, monkeypatch)
    migrate.run("0001")

    fxl_dir = root / "record" / "principles.d"
    assert not (fxl_dir / "FXL-004.md").exists()
    moved = (fxl_dir / "FXM-004.md").read_text()
    assert "formerly:\n- FXL-4\n" in moved, "identity stamped"
    assert "# FXM-004: Fourth value" in moved, "own heading swept"
    assert "citing FXM-1 sometimes" in moved, "cross-citations swept"

    config_text = (root / "luria.yaml").read_text()
    assert "\n  FXM:\n" in config_text
    assert "\n  FXL:\n" not in config_text
    assert "design_principles: docs/guiding-principles.md" in config_text
    assert "output: docs/guiding-principles.md" in config_text
    # The mirror under `remotes.LU.schemes` follows the rename; the one under
    # another project's remote does not.
    assert "        FXM:\n" in config_text, "mirror follows"
    assert config_text.count("document: docs/guiding-principles.md") == 1
    assert "        FXL:\n" in config_text, "theirs stays"
    assert 'document = "docs/design-principles.md"' in config_text, \
        "SG's own path untouched by the section-aware pass"

    assert not (root / "docs" / "design-principles.md").exists(), \
        "a generated view is removed, not renamed — the next index rebuilds it"

    notes = (root / "docs" / "notes.md").read_text()
    assert "Bare FXM-4 and a link [FXM-4](guiding-principles.md#fxm-4)." in notes
    assert "Fixture FXL-018 is nobody's document." in notes, "not in the mapping"
    assert "Foreign SG-FXL-4 belongs to strata-g." in notes, "their namespace"
    assert "Mirrored LU-FXM-004 follows this project." in notes
    assert "https://example.test/sg/docs/design-principles.md#x" in notes, \
        "a foreign URL never follows a local path pair"

    entry = next((root / "record" / "devlog.d").rglob("1*.md")).read_text()
    assert "[FXM-4](../../record/../docs/guiding-principles.md#fxm-4)" in entry, \
        "history swept, and the link's frame untouched (#57)"

    spec = (root / "record" / "migrations.d" / "0001-fxl-to-fxm.yaml").read_text()
    assert 'from = "FXL"' in spec, "the spec remembers the old spelling"

    # Full circle into rung 1: the fresh config resolves old spellings.
    config.reset()
    aliases.reset()
    assert {k: v.code for k, v in aliases.alias_map().items()} == {
        "FXL-001": "FXM-001", "FXL-004": "FXM-004"}


def test_a_rename_mirrors_each_citation_s_padding(tmp_path, monkeypatch):
    """`FXL-004` stays padded, `FXL-4` stays bare, and the anchor stays bare.

    The tail is one string with two spellings in play at once — the padded
    filename form and the bare prose form — so a rewrite has to answer
    "padded?" per citation rather than once per pair. Pinned because the
    provisional-tail work touched exactly this branch."""
    root = _premigration_project(tmp_path, monkeypatch)
    page = root / "docs" / "padding.md"
    page.write_text("Padded FXL-004, bare FXL-4, anchor "
                    "[x](design-principles.md#fxl-4).\n")
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "padding")
    migrate.run("0001")
    out = page.read_text()
    assert "Padded FXM-004" in out, out
    assert "bare FXM-4," in out, out
    assert "#fxm-4)" in out, out


def test_move_doc_lands_provisional_then_concretizes(tmp_path, monkeypatch):
    """A move arrives under a TEMPORARY code and is numbered afterwards.

    "The next free number" is no more a fact inside a migration than it is on
    a branch: every operation plans against the tree as it is now. So the move
    mints a temp code (ADR-049) and the concretizer — which runs where merges
    serialize — assigns the real one. The document ends up carrying BOTH
    aliases: the code it migrated from, and the temporary code it wore in
    between."""
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(merged(
        (root / "luria.yaml").read_text(),
        """
          schemes:
            VAL:
              dir: record/values.d
          """))
    (root / "record" / "values.d").mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / "record" / "migrations.d" / "0002-promote.yaml"
    mig.write_text("""
                   title: FXL-4 becomes a value
                   operations:
                   - op: move_doc
                     doc: FXL-4
                     to: VAL
                   """)
    migrate.run("0002")

    landed = list((root / "record" / "values.d").glob("VAL-tmp*.md"))
    assert len(landed) == 1, "the move lands provisional, never numbered"
    assert "formerly:\n- FXL-4\n" in landed[0].read_text()
    assert not (root / "record" / "principles.d" / "FXL-004.md").exists()
    # FXL renders as a document and VAL as an index, so the citation's SHAPE
    # changed: `page.md#anchor` → `dir/CODE.md`. The sweep drops the stale
    # link and the fixer rebuilds it from the resolver.
    notes = (root / "docs" / "notes.md").read_text()
    assert "(../record/values.d/VAL-tmp" in notes, notes
    assert "design-principles.md#val" not in notes, "no link to the old view"

    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "migrated")
    config.reset()
    aliases.reset()
    concretize.run()

    final = (root / "record" / "values.d" / "VAL-001.md").read_text()
    assert "- FXL-4" in final and "- VAL-tmp" in final, \
        "both the migrated-from code and the provisional one stay resolvable"
    notes = (root / "docs" / "notes.md").read_text()
    assert "[VAL-001](../record/values.d/VAL-001.md)" in notes, notes
    assert "val-tmp" not in notes, "no provisional spelling survives the sweep"
    assert "Fixture FXL-018" in notes, "a fixture number is not in the mapping"


def test_two_moves_into_one_scheme_do_not_collide(tmp_path, monkeypatch):
    """Two moves into one scheme, in one spec, must not claim one identity.

    With numbers they did: both read the same highest number and the second
    `git mv` overwrote the first — a document destroyed, and the dry-run
    printed two lines saying so in plain sight. Temporary codes make the
    collision structurally impossible rather than arithmetically avoided."""
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(merged(
        (root / "luria.yaml").read_text(),
        """
          schemes:
            VAL:
              dir: record/values.d
          """))
    (root / "record" / "values.d").mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / "record" / "migrations.d" / "0002-promote-both.yaml"
    mig.write_text("""
                   title: Both principles become values
                   operations:
                   - op: move_doc
                     doc: FXL-1
                     to: VAL
                   - op: move_doc
                     doc: FXL-4
                     to: VAL
                   """)
    migrate.run("0002")

    landed = sorted((root / "record" / "values.d").glob("VAL-tmp*.md"))
    assert len(landed) == 2, [p.name for p in landed]
    assert not list((root / "record" / "principles.d").glob("FXL-*.md"))

    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "migrated")
    config.reset()
    aliases.reset()
    concretize.run()
    numbered = sorted(p.name for p in
                      (root / "record" / "values.d").glob("VAL-0*.md"))
    assert numbered == ["VAL-001.md", "VAL-002.md"], numbered


def test_move_doc_supersede_copies_and_tombstones(tmp_path, monkeypatch):
    """Supersede copies rather than moves, and rewrites nothing.

    The tombstone names the provisional code; the concretizer rewrites it to
    the assigned number along with every other occurrence, so the status line
    ends up pointing at the real one without the migration having to know it."""
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(merged(
        (root / "luria.yaml").read_text(),
        """
          schemes:
            VAL:
              dir: record/values.d
          """))
    (root / "record" / "values.d").mkdir(parents=True)
    config.reset()
    aliases.reset()
    mig = root / "record" / "migrations.d" / "0002-supersede.yaml"
    mig.write_text("""
                   title: FXL-4 superseded by a value
                   operations:
                   - op: move_doc
                     doc: FXL-4
                     to: VAL
                     strategy: supersede
                   """)
    migrate.run("0002")
    old = (root / "record" / "principles.d" / "FXL-004.md").read_text()
    assert "status: Superseded\nsuperseded_by:\n- VAL-tmp" in old
    assert len(list((root / "record" / "values.d").glob("VAL-tmp*.md"))) == 1
    assert "Bare FXL-4" in (root / "docs" / "notes.md").read_text(), \
        "supersede mode rewrites nothing"

    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "superseded")
    config.reset()
    aliases.reset()
    concretize.run()
    old = (root / "record" / "principles.d" / "FXL-004.md").read_text()
    assert "status: Superseded\nsuperseded_by:\n- VAL-001" in old
    assert "Bare FXL-4" in (root / "docs" / "notes.md").read_text()


def test_new_migration_scaffolds_a_numbered_spec(tmp_path, monkeypatch):
    _premigration_project(tmp_path, monkeypatch)
    from luria import new
    path = new.new_entry("migration", {"title": "A second move"}, None)
    assert path.name == "0002-a-second-move.yaml"
    assert 'title = "A second move"' in path.read_text()


def test_the_sweep_honors_unlinted_file(tmp_path, monkeypatch, capsys):
    """A file that declares its references quotes (`unlinted-file`, #37) is
    a page of specimens — the sweep leaves every spelling in it alone."""
    root = _premigration_project(tmp_path, monkeypatch)
    specimen = root / "docs" / "specimens.md"
    specimen.write_text(
        "<!-- unlinted-file: — every code here is a specimen -->\n\n"
        "# Specimens\n\nThe old spelling FXL-4 preserved verbatim.\n")
    _git(root, "add", "-A")
    migrate.run("0001")
    assert "The old spelling FXL-4 preserved verbatim." in specimen.read_text()


def test_provisional_is_decided_in_one_place(tmp_path, monkeypatch):
    """`Pair.new_is_provisional` must ask the canonical predicate.

    The cheap version — `not tail.isdigit()` — looks equivalent and answers a
    different question: "this is not a number", which a malformed tail also
    satisfies. Pinned by asserting the two disagree exactly where they should."""
    from luria.config import is_temp_tail
    assert is_temp_tail("tmp47fje") and not is_temp_tail("004")
    assert not is_temp_tail("nonsense"), "not-a-number is not the same test"
    assert migrate.Pair("FXL-004", "VAL-tmp47fje").new_is_provisional
    assert not migrate.Pair("FXL-004", "VAL-007").new_is_provisional
    assert not migrate.Pair("FXL-004", "VAL-nonsense").new_is_provisional


def test_a_same_render_move_keeps_its_links_untouched(tmp_path, monkeypatch):
    """The unlink pass must fire ONLY when the shape actually changes.

    Two index-rendered schemes address a document the same way, so a move
    between them is a pure spelling swap — dropping and rebuilding those links
    would be churn, and would quietly relink bare references the author left
    bare on purpose elsewhere in the file."""
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(merged(
        (root / "luria.yaml").read_text(),
        """
          schemes:
            SRC:
              dir: record/src.d
            DST:
              dir: record/dst.d
          """))
    (root / "record" / "src.d").mkdir(parents=True)
    (root / "record" / "dst.d").mkdir(parents=True)
    (root / "record" / "src.d" / "SRC-001.md").write_text(
        "---\nstatus: Active\ntitle: 'A thing'\ntags:\n- record\n"
        "date: '2026-01-01'\n---\n\n# SRC-001: A thing\n\nBody.\n")
    page = root / "docs" / "shapes.md"
    page.write_text("See [SRC-001](../record/src.d/SRC-001.md).\n")
    config.reset()
    aliases.reset()
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "shapes")
    mig = root / "record" / "migrations.d" / "0002-same-shape.yaml"
    mig.write_text("""
                   title: SRC-1 becomes a DST
                   operations:
                   - op: move_doc
                     doc: SRC-1
                     to: DST
                   """)
    migrate.run("0002")
    out = page.read_text()
    assert "(../record/dst.d/DST-tmp" in out, out
    assert "src.d" not in out, "the path follows the move"


def test_a_worded_citation_of_a_moved_document_is_rebuilt(tmp_path,
                                                          monkeypatch):
    """A citation labelled in prose, not spelled as the code, still follows.

    `[design-principles #17](../design-principles.md#fxl-17)` is a live link to
    an anchor the move just vacated, and a code-shaped pattern walks straight
    past it. Worse, stripping it to its LABEL resurrects the problem: the bare
    `#17` left behind is itself a design-principle reference, which the fixer
    re-links to the address that was just vacated. The whole citation has to
    become the new code."""
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(merged(
        (root / "luria.yaml").read_text(),
        """
          schemes:
            VAL:
              dir: record/values.d
          """))
    (root / "record" / "values.d").mkdir(parents=True)
    page = root / "docs" / "worded.md"
    page.write_text(
        "The fix ([design-principles #4](design-principles.md#fxl-4)) held.\n")
    config.reset()
    aliases.reset()
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "worded")
    mig = root / "record" / "migrations.d" / "0002-worded.yaml"
    mig.write_text("""
                   title: FXL-4 becomes a value
                   operations:
                   - op: move_doc
                     doc: FXL-4
                     to: VAL
                   """)
    migrate.run("0002")
    out = page.read_text()
    assert "design-principles.md#fxl-4" not in out, out
    assert "#fxl-4" not in out, "the vacated anchor must not survive anywhere"
    assert "VAL-tmp" in out, out


def _worded_move_project(tmp_path, monkeypatch):
    """The premigration project plus a SOURCE FILE that cites FXL-4 two ways —
    by code and in prose — and a spec that moves FXL-4 into an index-rendered
    scheme."""
    root = _premigration_project(tmp_path, monkeypatch)
    (root / "luria.yaml").write_text(merged(
        (root / "luria.yaml").read_text(),
        """
          code:
            globs:
            - src/*.py
          schemes:
            VAL:
              dir: record/values.d
          """))
    (root / "record" / "values.d").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "src" / "engine.py").write_text(
        "# Selection rides undo by decision (design-principles #4), not by\n"
        "# accident. FXL-4 is the claim; FXL-1 is a different one.\n"
        "SELECTION_RIDES_UNDO = True\n")
    config.reset()
    aliases.reset()
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "-qm", "src")
    (root / "record" / "migrations.d" / "0002-worded-code.yaml").write_text(
        """
        title: FXL-4 becomes a value
        operations:
        - op: move_doc
          doc: FXL-4
          to: VAL
        """)
    return root


def test_the_relink_pass_stops_where_the_hyperlink_lint_stops(tmp_path,
                                                              monkeypatch):
    """Rebuilding links must not reach files the linter never checks.

    The sweep walks every tracked file, because "does this text spell a code
    that moved?" is a question a `.py` comment answers as truthfully as a
    document does. Linking is a different question — code is quoted, not
    asserted, so a source file is exempt from the hyperlink lint — and running
    the fixer wider than the linter checks turned one two-document move into a
    469-file diff of markdown links inside Python comments."""
    root = _worded_move_project(tmp_path, monkeypatch)
    migrate.run("0002")
    src = (root / "src" / "engine.py").read_text()
    assert "](" not in src, f"no markdown links in a source file:\n{src}"
    # FXL-1 did not move, and stays exactly as the author left it.
    assert "FXL-1 is a different one" in src, src


def test_a_worded_citation_in_code_follows_the_move(tmp_path, monkeypatch):
    """A prose-spelled citation names the document as surely as the code does.

    `design-principles #4` in a comment carries no code for the code swap to
    catch and, unlinked, no address for the address swap to catch. It is
    recognized by the same scanner that would have turned it into a link in a
    document, so the sweep can respell it — and must, or the move leaves a
    citation pointing at a document that is no longer there."""
    root = _worded_move_project(tmp_path, monkeypatch)
    migrate.run("0002")
    src = (root / "src" / "engine.py").read_text()
    assert "design-principles #4" not in src, src
    assert "#4" not in src, "the vacated anchor number must not survive"
    assert src.count("VAL-tmp") == 2, f"both spellings respelled:\n{src}"
    assert "FXL-1 is a different one" in src, "an unmoved code is left alone"


def test_a_formerly_stamp_is_not_a_dangling_citation(tmp_path, monkeypatch):
    """The alias a move writes must not be reported as a broken reference.

    `formerly: FXL-004` names a code that resolves to no document *because the
    alias exists* — that is what the stamp is for. Counting it made every
    migration hand back one fresh "resolves to no document" warning per moved
    document, pointing at the files the migration had just written."""
    root = _worded_move_project(tmp_path, monkeypatch)
    migrate.run("0002")
    config.reset()
    aliases.reset()
    moved = next((root / "record" / "values.d").glob("VAL-*.md"))
    assert "formerly:" in moved.read_text(), moved.read_text()
    assert "FXL-004" not in ref_status.scan().dangling, \
        "the stamp is a declaration, not a citation"
