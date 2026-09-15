# tests/test_one_render.py
"""One render of the view tree per lint, shared by the checks that read it.

`adr_index.outputs()` renders every view of every scheme, every journal and
every report — and then again for each nested record (ADR-078). It is the most
expensive thing `luria lint` does.

Two checks need it, and each reached for it independently: `check_view_dirs`
compares the tree against it, and `check_anchors` reads links out of it via
`anchors.documents`. So one lint rendered everything twice — on this record,
two passes over eight records, each pass re-scanning every corpus for the
reports it renders.

Both consumers already took a `rendered` argument for exactly this reason, and
nothing had ever passed one. `run` now renders once and hands the same dict to
both.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import adr_index, anchors, lint, ref_status, reports  # noqa: E402


def _doc(root: Path, number: int, body: str = "Body.") -> Path:
    path = root / "record" / "decisions.d" / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstatus: Active\ntitle: 'Decision {number}'\ntags:\n- t\n"
        f"date: '2026-01-01'\n---\n\n# ADR-{number:03d}: Decision {number}\n\n{body}\n",
        encoding="utf-8")
    return path


def test_one_lint_renders_the_view_tree_once(project, monkeypatch):
    _doc(project, 1)

    calls = []
    real = adr_index.outputs
    monkeypatch.setattr(adr_index, "outputs",
                        lambda nested=True: calls.append(nested) or real(nested))

    try:
        lint.run()
    except SystemExit:
        pass                                # findings are not this test's point

    top_level = [n for n in calls if n is True]
    assert len(top_level) == 1, \
        f"the tree should be rendered once per lint, not {len(top_level)}x"


def test_check_view_dirs_uses_the_render_it_is_given(project, monkeypatch):
    _doc(project, 1)
    rendered = adr_index.outputs()

    monkeypatch.setattr(adr_index, "outputs",
                        lambda nested=True: pytest_fail("rendered again"))
    lint.check_view_dirs([], rendered)      # must not re-render


def test_check_anchors_uses_the_render_it_is_given(project, monkeypatch):
    _doc(project, 1)
    rendered = adr_index.outputs()

    monkeypatch.setattr(adr_index, "outputs",
                        lambda nested=True: pytest_fail("rendered again"))
    lint.check_anchors([], rendered)        # must not re-render


def pytest_fail(msg):
    raise AssertionError(msg)


def test_a_given_render_finds_what_rendering_itself_would(project):
    """Sharing must not change either check's answer — the dict handed in is
    the same one each would have built."""
    _doc(project, 1)
    rendered = adr_index.outputs()

    shared_dirs, own_dirs = [], []
    lint.check_view_dirs(shared_dirs, rendered)
    lint.check_view_dirs(own_dirs)
    assert shared_dirs == own_dirs

    shared_anchors, own_anchors = [], []
    lint.check_anchors(shared_anchors, rendered)
    lint.check_anchors(own_anchors)
    assert shared_anchors == own_anchors


def test_anchors_documents_still_renders_when_given_nothing(project):
    """The argument is an optimisation, not a new requirement: every existing
    caller passes nothing and must keep working."""
    _doc(project, 1)
    out = anchors.documents()
    assert out, "documents() with no argument still reads sources plus views"
    assert out == anchors.documents(adr_index.outputs())


# ── the scan each record's reports took twice ─────────────────────────────
#
# `reference_status` read `docs = ref_status.load_docs()` and then asked for
# `scan(docs=docs)` — which is precisely what `scan()` computes when handed
# nothing. Restating the default meant the call could not be served from the
# corpus-scan cache, so every record scanned itself once for its reference
# status and again for its pending-decisions table.

def test_rendering_a_records_reports_scans_its_corpus_once(project, monkeypatch):
    _doc(project, 1)
    ref_status.forget_scan()

    calls = []
    real = ref_status._scan
    monkeypatch.setattr(ref_status, "_scan",
                        lambda f, d: calls.append(1) or real(f, d))

    reports.outputs()
    assert len(calls) == 1, \
        f"one corpus, one scan — not {len(calls)}"


def test_passing_the_default_docs_is_the_same_scan(project):
    """The equivalence the change rests on: `_scan` fills `docs` from
    `load_docs()` when given none, so naming it changes nothing but the
    cache's ability to answer."""
    _doc(project, 1)
    _doc(project, 2, body="Cites ADR-001.")
    named = ref_status._scan(None, ref_status.load_docs())
    default = ref_status._scan(None, None)
    assert named.cited.keys() == default.cited.keys()
    assert named.dangling.keys() == default.dangling.keys()
    assert len(named.annotations) == len(default.annotations)
    assert named.unlinted == default.unlinted
