"""`luria ack` — the acknowledgement written from the scan, not from recall (#308).

Every test here is a transcription error that actually shipped. The directives
are the escape hatch under `lint.fail_on`, which makes them the one place a
mistake is silent: a directive naming a code that does not exist suppresses
nothing and reports nothing, and one over a document still in force is a
finding the moment it lands. A day of filing work downstream produced four of
them, all between a report that had the right answer and a file edited by hand.

So the contract under test is not the typing saved. It is that the code comes
from `Scan`, and that the three states with no acknowledgement to write refuse
rather than write one.
"""
# unresolved-ok-file: ADR-777, ADR-919 — fixture codes, deliberately naming
# no document: an unresolved code is what half these tests are about
from pathlib import Path

from _config import merged
from _scheme import decision

from luria import ack, ref_status
from luria.config import current


def cited(project, body: str, name: str = "docs/notes.md") -> Path:
    page = project / name
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(body)
    return page


# ── What it writes ───────────────────────────────────────────────────────


def test_a_retired_citation_gets_inactive_ok(project):
    """The code and the directive name both come from the scan: the document
    is retired, so the word is `inactive-ok`, and nobody typed either."""
    decision(project, 12, "Superseded")
    page = cited(project, "# Notes\n\nStill leaning on ADR-012 here.\n")
    assert ack.write("ADR-012", "the decision this page replaced") == \
        ["docs/notes.md:3"]
    assert ("<!-- inactive-ok: ADR-012 — the decision this page replaced -->"
            in page.read_text())


def test_an_unresolved_code_gets_unresolved_ok(project):
    """Same check, opposite sign — and the sign is read off the scan rather
    than guessed. Getting it backwards writes a directive that is itself
    malformed, which is the second of the four failures #308 lists."""
    decision(project, 1, "Active")
    page = cited(project, "ported from elsewhere: ADR-777\n")
    ack.write("ADR-777", "another project's number")
    assert "<!-- unresolved-ok: ADR-777 — another project's number -->" \
        in page.read_text()


def test_the_directive_lands_above_the_citation(project):
    """Line scope, because an acknowledgement is a claim about *that*
    sentence. Written anywhere else it governs the wrong lines, and the
    scopes have no per-directive defaults to fall back on."""
    decision(project, 12, "Superseded")
    page = cited(project, "one\ntwo\nper ADR-012\nfour\n")
    ack.write("ADR-012", "deliberate")
    lines = page.read_text().splitlines()
    assert lines[2].startswith("<!-- inactive-ok:")
    assert lines[3] == "per ADR-012"


def test_a_python_site_gets_a_hash_comment(project):
    """A directive has to *open* a comment, so the marker is the file's, not
    markdown's. An HTML comment in a `.py` file parses as nothing."""
    decision(project, 12, "Superseded")
    (project / "luria.yaml").write_text(
        merged((project / "luria.yaml").read_text(),
               {"code": {"globs": ["*.py"]}}))
    from luria import config
    config.reset()
    page = cited(project, "def f():\n    return 'ADR-012'\n", name="m.py")
    ack.write("ADR-012", "what shipped")
    body = page.read_text().splitlines()
    assert body[1] == "    # inactive-ok: ADR-012 — what shipped", \
        "the comment marker is the file's, and the indent is the line's"


def test_every_unacknowledged_site_is_covered(project):
    """One run, every site — because the failure mode is a directive written
    at the site somebody remembered and not at the other three."""
    decision(project, 12, "Superseded")
    page = cited(project, "ADR-012 here\nand ADR-012 again\nand ADR-012\n")
    assert len(ack.write("ADR-012", "deliberate")) == 3
    assert page.read_text().count("inactive-ok") == 3
    docs = ref_status.load_docs()
    assert ref_status.flagged(ref_status.scan(docs=docs), docs) == [], \
        "and the finding is cleared"


def test_file_scope_writes_one_directive(project):
    """The blunt tool, for a page whose whole subject is the retired thing.
    Offered rather than guessed: the report knows a code is cited three times,
    and cannot know whether that makes the file the unit."""
    decision(project, 12, "Superseded")
    page = cited(project, "ADR-012\nand ADR-012\nand ADR-012\n")
    assert ack.write("ADR-012", "this page is that history", scope="file") == \
        ["docs/notes.md:1"]
    assert page.read_text().count("inactive-ok-file") == 1


def test_an_expiry_rides_along(project):
    """`until` is a modifier the directive grammar already reads; writing it
    by hand is another chance to write a date that cannot be parsed, which
    leaves the directive live forever and is its own finding."""
    decision(project, 12, "Superseded")
    page = cited(project, "per ADR-012\n")
    ack.write("ADR-012", "revisit when the API settles", until="2026-12-01")
    assert ("inactive-ok: ADR-012 until 2026-12-01 — revisit when the API "
            "settles") in page.read_text()


# ── What it refuses ──────────────────────────────────────────────────────


def test_it_refuses_over_a_document_in_force(project):
    """Failure 3 of the four: a directive stale on arrival. The command knows
    the current status, so it declines instead of writing one and letting the
    next lint report it."""
    decision(project, 12, "Active")
    page = cited(project, "per ADR-012\n")
    before = page.read_text()
    _, _, refusal = ack.plan("ADR-012")
    assert "is Active" in refusal and "stale-directives" in refusal
    assert page.read_text() == before, "and writes nothing"


def test_it_refuses_a_code_nothing_cites(project):
    """Failure 2 and 4: a code crossed between two schemes, and a number
    written before it was allocated. Both name something the scan has never
    seen, and both used to land silently inside an HTML comment."""
    decision(project, 1, "Active")
    cited(project, "nothing here\n")
    _, _, refusal = ack.plan("ADR-919")
    assert "not cited anywhere" in refusal


def test_it_refuses_when_everything_is_already_acknowledged(project):
    """A second directive over an acknowledged citation governs nothing, and
    `stale-directives` would then report the one nobody needed."""
    decision(project, 12, "Superseded")
    cited(project, "<!-- inactive-ok: ADR-012 — deliberate -->\nper ADR-012\n")
    _, _, refusal = ack.plan("ADR-012")
    assert "already acknowledged" in refusal


def test_a_reason_is_required(project, capsys):
    """The one thing only a person can supply. A generated reason vouches for
    nothing, which is the failure the directives exist to prevent — so there
    is no bulk mode and `luria repair` does not do this."""
    decision(project, 12, "Superseded")
    page = cited(project, "per ADR-012\n")
    before = page.read_text()
    try:
        ack.run("ADR-012")
    except SystemExit as e:
        assert "--reason is required" in str(e)
    else:
        raise AssertionError("it wrote one without a reason")
    assert page.read_text() == before


def test_an_unknown_scope_says_so(project):
    """A dial set to a notch that does not exist has to say so rather than
    fall back to a default the caller did not ask for."""
    decision(project, 12, "Superseded")
    cited(project, "per ADR-012\n")
    try:
        ack.write("ADR-012", "deliberate", scope="page")
    except SystemExit as e:
        assert "unknown scope" in str(e)
    else:
        raise AssertionError("it accepted a scope it does not have")


# ── The survey ───────────────────────────────────────────────────────────


def test_the_survey_writes_nothing(project, capsys):
    """Called with no code it is a report. The whole premise is that this is
    read before anything is written, so reading it must not write."""
    decision(project, 12, "Superseded")
    page = cited(project, "per ADR-012\n")
    before = page.read_text()
    ack.run()
    out = capsys.readouterr().out
    assert "ADR-012 — cited but not in force" in out
    assert "docs/notes.md:1" in out
    assert page.read_text() == before


def test_the_survey_says_so_when_there_is_nothing(project, capsys):
    """The all-clear is most of a report's value, and silence is not one."""
    decision(project, 1, "Active")
    cited(project, "per ADR-001\n")
    ack.run()
    assert "nothing to acknowledge" in capsys.readouterr().out


def test_file_scope_lands_below_frontmatter(project):
    """A `<!-- -->` above the opening `---` is not a comment, it is the
    document's first line — and the frontmatter every generated view reads is
    gone. The scope is the whole file either way, so the directive drops one
    block and loses nothing."""
    decision(project, 12, "Superseded")
    page = cited(project,
                 "---\ntitle: 'A page'\n---\n\nper ADR-012 and ADR-012\n")
    ack.write("ADR-012", "this page is that history", scope="file")
    rows = page.read_text().splitlines()
    assert rows[:3] == ["---", "title: 'A page'", "---"]
    assert rows[3].startswith("<!-- inactive-ok-file:")
