"""The `broken-targets` class: relative links that go nowhere from the view.

The check exists for one failure mode, and it is a quiet one. Record prose is
rendered into a view in another directory, so a link target has to resolve from
where the text *lands*, not where it lives. Count the directories from the
source file and you get an answer that looks right beside the source and points
at nothing in the view — and every other check passes, because they are about
whether `ADR-035` names a document, not about whether the path someone typed
around it goes anywhere.

Fired once before being trusted (DP-6): pointed at a project that had been
hand-writing journal targets since its first commit, it reported 99 dead links
that eleven clean lints had not mentioned.

The journal fixture is the load-bearing one. A journal entry is the widest gap
between where prose lives and where it renders — five directories — so it is
the case where the two frames give different answers and the check has to
choose the right one.
"""

from __future__ import annotations

from pathlib import Path

from luria import config, lint, link_targets


def _project(root: Path, monkeypatch) -> None:
    """A project with an index scheme and a journal, which is the layout that
    separates the two frames: a record document is read where it sits, a
    journal entry is assembled into `docs/log/`."""
    (root / "record" / "notes.d").mkdir(parents=True, exist_ok=True)
    (root / "record" / "log.d").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.NT]\n'
        'dir = "record/notes.d"\n'
        'render = "index"\n'
        'output = "docs/notes"\n'
        '[luria.journals.log]\n'
        'dir = "record/log.d"\n'
        'output = "docs/log"\n'
        'granularity = "day"\n')
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()


def _note(root: Path, number: int, body: str = "Body.") -> Path:
    path = root / "record" / "notes.d" / f"NT-{number:03d}.md"
    path.write_text(
        f"---\nstatus: Active\ntitle: 'A note'\ntags:\n- record\n"
        f"date: '2026-01-01'\n---\n\n# NT-{number:03d}: A note\n\n{body}\n")
    return path


def _entry(root: Path, body: str) -> Path:
    path = root / "record" / "log.d" / "2026" / "01" / "01" / "120000.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: 'An entry'\ncreated: '2026-01-01T12:00:00'\n"
        f"tags: [log]\n---\n\n{body}\n")
    return path


def test_a_target_that_resolves_is_silent(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1)
    _note(tmp_path, 2, "See [NT-001](NT-001.md).")
    assert link_targets.broken()[0] == []


def test_a_target_that_resolves_to_nothing_is_reported(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, "See [NT-009](NT-009.md).")
    flagged, _ = link_targets.broken()
    assert len(flagged) == 1
    assert "NT-009.md" in flagged[0] and "NT-001.md:11" in flagged[0]


def test_a_journal_entry_resolves_from_where_it_renders(tmp_path, monkeypatch):
    """The whole point. `record/log.d/2026/01/01/` is five directories deep and
    renders into `docs/log/`, so the target that works is the one written for
    the view — and the arithmetic that looks right beside the source is wrong.

    Both assertions matter. Accepting the view-relative form is not evidence on
    its own: a check that resolved from the source directory would also have to
    reject it, and a check that resolved from *neither* would reject both."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1)
    _entry(tmp_path, "See [NT-001](../../record/notes.d/NT-001.md).")
    assert link_targets.broken()[0] == []

    _entry(tmp_path, "See [NT-001](../../../../record/notes.d/NT-001.md).")
    flagged, _ = link_targets.broken()
    assert len(flagged) == 1, "source-relative depth must not be accepted"
    assert "docs/log/" in flagged[0], "the message names the frame it used"


def test_urls_anchors_and_absolute_paths_are_not_checked(tmp_path, monkeypatch):
    """None of these name a file in this repo, so none of them can be dead
    here. A check that reported them would be unusable in prose that cites the
    web, which is most prose."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1,
          "[a](https://example.test/x) [b](//host/x) [c](/abs/x) [d](#here) "
          "[e](mailto:x@example.test)")
    assert link_targets.broken()[0] == []


def test_a_pattern_is_not_a_path(tmp_path, monkeypatch):
    """A URL template and a uid regex are link-shaped by accident. Both appear
    in config examples in this repo's own record, which is how they were
    found: `uid = "(\\d{4})[.:](\\d{4,5})"` reads as a link to `(\\d{4,5})`."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, 'uid = "(\\d{4})[.:](\\d{4,5})" and {n} in a url')
    assert link_targets.broken()[0] == []


def test_an_example_in_code_is_not_a_citation(tmp_path, monkeypatch):
    """Same rule the reference checks use: markdown showing a link is not
    writing one."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1,
          "Write `[NT-009](NT-009.md)`.\n\n```\n[NT-009](NT-009.md)\n```\n")
    assert link_targets.broken()[0] == []


def test_a_fragment_does_not_hide_a_missing_file(tmp_path, monkeypatch):
    """`#section` is not checked, but the file it hangs off still is —
    otherwise appending an anchor would silence any dead link."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, "See [NT-009](NT-009.md#context).")
    assert len(link_targets.broken()[0]) == 1


def test_a_percent_encoded_target_resolves_to_the_real_name(tmp_path,
                                                            monkeypatch):
    """A filename with a space is written `a%20note.md` in markdown and stored
    with the space on disk. Comparing the encoded form would report every one
    of them."""
    _project(tmp_path, monkeypatch)
    (tmp_path / "docs" / "a note.md").write_text("# A note\n")
    _note(tmp_path, 1, "See [it](../../docs/a%20note.md).")
    assert link_targets.broken()[0] == []


def test_a_deliberate_target_is_acknowledged_not_deleted(tmp_path, monkeypatch):
    """The escape hatch, and it is per-target: acknowledging one placeholder
    must not silence the dead link three lines down."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1,
          "<!-- target-ok: build/out.md — generated, not committed -->\n"
          "See [out](build/out.md).")
    assert link_targets.broken()[0] == []

    _note(tmp_path, 2,
          "<!-- target-ok: build/out.md — generated, not committed -->\n"
          "See [out](build/out.md).\n\nAnd [NT-009](NT-009.md).")
    flagged, _ = link_targets.broken()
    assert len(flagged) == 1 and "NT-009.md" in flagged[0]


def test_a_directive_that_acknowledges_nothing_is_reported(tmp_path,
                                                           monkeypatch):
    """A directive that silently does nothing is worse than no directive: it
    reads as considered when the consideration has expired."""
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1,
          "<!-- target-ok: build/out.md — generated, not committed -->\n"
          "Nothing links there any more.")
    flagged, stale = link_targets.broken()
    assert flagged == []
    assert len(stale) == 1 and "build/out.md" in stale[0]


def test_the_class_is_failable(tmp_path, monkeypatch):
    """Emitted classes must be nameable in `fail_on` — the dial and the
    reporter read the same vocabulary."""
    assert "broken-targets" in lint.FAILABLE
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1, "See [NT-009](NT-009.md).")
    assert "broken-targets" in {n for n, _, _ in lint.status_sections()}


def test_a_clean_project_does_not_emit_the_class(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch)
    _note(tmp_path, 1)
    assert "broken-targets" not in {n for n, _, _ in lint.status_sections()}
