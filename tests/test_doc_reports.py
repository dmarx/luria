"""The status reports, rendered as committed views
([ADR-035](../record/decisions.d/ADR-035.md), #35).

These are the only place the status warnings are read in full, and nothing
consumes them programmatically — so what is worth pinning is that the numbers
in them agree with the checks they come from, and with each other. Two counts
that disagree without saying why is the bug that prompted them.

Since #35 they are views `luria index` commits, which adds two properties: a
report must be a **pure function of the record** (anything clock-derived goes
stale at midnight and fails the staleness check with no record change behind
it), and everything it names must be a **link** (the reader arrived from a
badge, not from a grep prompt).

Pure-function-of-the-record is pinned by what it *forbids* — the "N days"
column — not by "today's date appears nowhere": a decision filed and still
`Proposed` today legitimately puts today's date in the report, so that
blunter assertion fails on a correct report exactly once per decision.
"""
import shutil
import subprocess
from pathlib import Path

import pytest
from _scheme import decision

from luria import adr_index, adr_pending, config, lint, ref_status, reports

REPO = Path(__file__).resolve().parents[1]


def test_writes_both_reports(tmp_path):
    written = reports.write(tmp_path)
    assert [p.name for p in written] == ["pending-decisions.md",
                                         "reference-status.md"]
    assert all(p.read_text().startswith("# ") for p in written)


def test_generated_stamp_says_not_to_edit(tmp_path):
    for path in reports.write(tmp_path):
        assert "built, not edited" in path.read_text()


def test_reference_report_links_every_site(project):
    """The console summary caps at five sites per document; the report is
    where the rest lives, so it must not cap — and each site is a link to the
    citing file (#35)."""
    decision(project, 12, "Superseded")
    (project / "notes.md").write_text(
        "\n".join(f"line {n} cites ADR-012" for n in range(1, 9)) + "\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()

    text = reports.reference_status()
    docs = ref_status.load_docs()
    for _, loud, _ in ref_status.flagged(ref_status.scan(docs=docs), docs):
        assert len(loud) == 8
        for site in loud:
            assert f"[`{site}`](../../notes.md)" in text


def test_reference_report_links_the_flagged_document(project):
    decision(project, 12, "Superseded")
    (project / "notes.md").write_text("cites ADR-012\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()

    text = reports.reference_status()
    from luria.config import current
    import os.path
    rel = os.path.relpath(current().schemes["ADR"].dir / "ADR-012.md",
                          current().reports)
    assert f"### [ADR-012]({rel}) — Superseded" in text


def test_reference_report_counts_match_the_scan():
    docs = ref_status.load_docs()
    result = ref_status.scan(docs=docs)
    rows = ref_status.flagged(result, docs)
    excused = ref_status.acknowledged_count(result, docs)
    text = reports.reference_status()
    assert (f"**{reports._n(len(rows), 'document')} cited without "
            "acknowledgement.**") in text
    assert f"Not listed: {reports._n(excused, 'citation')} someone" in text


def test_the_report_never_calls_a_proposed_document_retired(project):
    """The clarification #63 asked for: a Proposed document was listed under
    a page titled "Retired documents", and Proposed is the opposite of
    retired — it hasn't been in force yet. The umbrella is "not in force",
    and the section says which side of that a status falls on."""
    decision(project, 12, "Proposed")
    (project / "notes.md").write_text("cites ADR-012\n")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = ""\n[luria.code]\nglobs = ["notes.md"]\n')
    from luria import config
    config.reset()
    text = reports.reference_status()
    assert "Retired" not in text
    assert "## Documents cited while not in force" in text
    assert "— Proposed" in text


def test_pending_report_links_every_row_to_its_decision(project):
    decision(project, 2, "Proposed")
    text = reports.pending_decisions()
    for r in adr_pending.pending():
        from luria.config import current
        assert f"[ADR-{r.number:03d}](../../{current().rel(r.path)})" in text


def test_pending_report_states_age_as_a_date(project):
    """"Open since 2026-01-01" is a fact about the record; "N days" is a fact
    about today, and a committed view can't carry one (#35)."""
    decision(project, 2, "Proposed")
    text = reports.pending_decisions()
    assert "| 2026-01-01 | Proposed |" in text
    assert "days" not in text


def test_the_two_reports_explain_why_their_counts_differ():
    """The bug that prompted the reports: one said 8 and the other 9, with
    nothing explaining that they measure different things."""
    text = reports.pending_decisions()
    assert "is not an off-by-one" in text
    assert "nothing cites it, or every citation carries an" in text


def test_outputs_land_in_the_configured_reports_dir():
    from luria.config import current
    assert set(reports.outputs()) == {
        current().reports / "reference-status.md",
        current().reports / "pending-decisions.md",
    }


def test_reports_are_deterministic():
    a = reports.reference_status(), reports.pending_decisions()
    b = reports.reference_status(), reports.pending_decisions()
    assert a == b


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def test_a_gitignored_report_dir_is_not_stale(tmp_path, monkeypatch):
    """`luria index --check` must not fail over a view the project ignores.

    A project can point `[luria.paths] reports` at a build directory and
    publish the result as a CI artifact instead of committing it — which is
    the shape downstream had. A fresh clone then never has the file, so
    *missing* read as *stale*, and the remedy the failure printed ("regenerate
    and commit the result") is the one thing `.gitignore` forbids: the docs
    job went red on every commit and stayed there.
    """
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\nreports = "build/doc-reports"\n')
    (tmp_path / "docs" / "design-principles.md").write_text(
        "# Design principles\n\n## 1. First value\n\nBody.\n")
    (tmp_path / ".gitignore").write_text("build/\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "before")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()

    adr_index.run()                            # writes every view, ignored ones too
    assert (tmp_path / "build" / "doc-reports" /
            "reference-status.md").exists(), "an ignored view is still written"
    adr_index.run(check=True)                  # …and does not gate on them

    shutil.rmtree(tmp_path / "build")          # the state of every fresh clone
    adr_index.run(check=True)


def test_a_tracked_report_dir_still_gates(tmp_path, monkeypatch):
    """The exemption is `.gitignore`, not the reports directory.

    A project that commits its reports — which is this repo's own layout —
    must keep failing on a stale one, or the fix would have turned a real
    check off for everybody to unstick one project.
    """
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\nreports = "docs/reports"\n')
    (tmp_path / "docs" / "design-principles.md").write_text(
        "# Design principles\n\n## 1. First value\n\nBody.\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "before")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()

    adr_index.run()
    adr_index.run(check=True)
    (tmp_path / "docs" / "reports" / "reference-status.md").write_text("stale\n")
    with pytest.raises(SystemExit):
        adr_index.run(check=True)


def test_lint_and_index_check_agree_about_staleness(tmp_path, monkeypatch):
    """One rule set, two commands. They used to be two rule sets.

    `luria index --check` and `luria lint`'s `check_generated_index` both
    decided what "stale" means, from the same three rules written twice. The
    gitignore exemption above went into the first one and `lint` went on
    rejecting the identical tree — the fixer/linter split this package exists
    to prevent, reproduced inside the package. They share `staleness()` now,
    and this pins it from the outside: whatever one says about a tree, the
    other says too.
    """
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.paths]\nreports = "build/doc-reports"\n')
    (tmp_path / "docs" / "design-principles.md").write_text(
        "# Design principles\n\n## 1. First value\n\nBody.\n")
    (tmp_path / ".gitignore").write_text("build/\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "before")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()

    def verdicts() -> tuple[bool, list[str]]:
        try:
            adr_index.run(check=True)
            index_stale = False
        except SystemExit:
            index_stale = True
        errors: list[str] = []
        lint.check_generated_index(errors)
        return index_stale, errors

    adr_index.run()
    shutil.rmtree(tmp_path / "build")
    index_stale, errors = verdicts()
    assert not index_stale and not errors, errors

    # …and they agree the other way too, on a view that IS tracked.
    (tmp_path / "docs" / "decisions" / "README.md").write_text("hand-edited\n")
    index_stale, errors = verdicts()
    assert index_stale and errors, "both must fail on a genuinely stale view"
