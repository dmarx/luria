"""The `narrow-titles` class: titles that claim to transfer, in local nouns.

The check exists for one failure mode: a principle stated about the artifact it
was first noticed on is a principle nobody applies to the next artifact — and
nothing else catches it, because the document stays true, renders, and passes
every other check. It simply stops being cited.

Every test here states its own vocabulary. Luria ships none, and a test leaning
on a shipped list would be asserting the shipped list.
"""

from __future__ import annotations

from pathlib import Path

from luria import config, lint, narrow_titles


def _project(root: Path, monkeypatch, terms: str = "", generalize: bool = True
             ) -> None:
    """A project with a VP scheme rendering to a document, and the dial set.

    `VP` rather than `DP`: a fixture that borrows a real sequence's prefix is
    the hazard the fixture-code rule exists for, and this repo's own principles
    are the corpus a narrow-title check would otherwise read."""
    (root / "record" / "values.d").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        f'[luria.lint]\nnarrow_terms = [{terms}]\n'
        '[luria.schemes.VP]\n'
        'dir = "record/values.d"\n'
        'render = "document"\n'
        'output = "docs/values.md"\n'
        f'titles_generalize = {str(generalize).lower()}\n')
    monkeypatch.setenv("LURIA_ROOT", str(root))
    config.reset()


def _value(root: Path, number: int, title: str, body: str = "Body.") -> Path:
    path = root / "record" / "values.d" / f"VP-{number:03d}.md"
    path.write_text(
        f"---\nstatus: Active\ntitle: {title!r}\ntags:\n- craft\n"
        f"date: '2026-01-01'\n---\n\n# VP-{number:03d}: {title}\n\n{body}\n")
    return path


def test_no_vocabulary_means_no_check(tmp_path, monkeypatch):
    """The default posture: luria ships no nouns, so nothing fires.

    A project that has not thought about this must not be told it has a
    problem — and must not be told it is clean either. The class is absent."""
    _project(tmp_path, monkeypatch, terms="")
    _value(tmp_path, 1, "A rule about the toolbar and the canvas")
    assert narrow_titles.rows() == []
    assert "narrow-titles" not in {n for n, _, _ in lint.status_sections()}


def test_a_scheme_that_does_not_claim_to_transfer_is_untouched(tmp_path,
                                                               monkeypatch):
    """A decision is ABOUT something specific; naming it is correct."""
    _project(tmp_path, monkeypatch, terms='"toolbar"', generalize=False)
    _value(tmp_path, 1, "The toolbar renders lazily")
    assert narrow_titles.rows() == []


def test_a_local_noun_in_a_transferable_title_is_reported(tmp_path,
                                                          monkeypatch):
    _project(tmp_path, monkeypatch, terms='"toolbar", "canvas"')
    _value(tmp_path, 1, "Never block the toolbar")
    rows = narrow_titles.rows()
    assert len(rows) == 1
    assert "VP-001" in rows[0] and "toolbar" in rows[0]


def test_the_match_is_plural_tolerant_and_case_insensitive(tmp_path,
                                                           monkeypatch):
    _project(tmp_path, monkeypatch, terms='"node"')
    _value(tmp_path, 1, "Nodes are cheap")
    assert len(narrow_titles.rows()) == 1


def test_a_substring_is_not_a_match(tmp_path, monkeypatch):
    """`node` must not fire on "anode" — the alternation is word-bounded.

    The word has to genuinely CONTAIN the term, or the test passes whatever
    the pattern does. A first draft used "nodded", which does not contain
    "node" at all, and so held even with the boundaries removed."""
    _project(tmp_path, monkeypatch, terms='"node"')
    _value(tmp_path, 1, "Measure at the anode, not the cathode")
    assert narrow_titles.rows() == []


def test_another_sense_is_acknowledged_not_removed(tmp_path, monkeypatch):
    """The vocabulary keeps working elsewhere; this USE is the exception.

    Shrinking the vocabulary to silence one document is how the check stops
    protecting every other document."""
    _project(tmp_path, monkeypatch, terms='"overlay"')
    _value(tmp_path, 1, "User choice overlays the baseline",
           "<!-- broad-ok: overlay — a verb here, not the UI noun -->\n\nBody.")
    assert narrow_titles.rows() == []

    _value(tmp_path, 2, "The overlay is opaque")
    rows = narrow_titles.rows()
    assert len(rows) == 1 and "VP-002" in rows[0], \
        "the acknowledgement is per-document, not global"


def test_the_class_is_failable(tmp_path, monkeypatch):
    """Emitted classes must be nameable in `fail_on` — the dial and the
    reporter read the same vocabulary."""
    assert "narrow-titles" in lint.FAILABLE
    _project(tmp_path, monkeypatch, terms='"toolbar"')
    _value(tmp_path, 1, "Never block the toolbar")
    assert "narrow-titles" in {n for n, _, _ in lint.status_sections()}
