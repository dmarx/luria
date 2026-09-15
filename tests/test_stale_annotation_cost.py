# tests/test_stale_annotation_cost.py
"""What a poisoned annotation costs, said out loud.

`ref_status.scan` drops an annotation with a `problem` whole:

```python
usable = [a for a in anns if not a.problem]
```

Not "the codes that are still fine" — nothing. So one stale code in a
multi-code acknowledgement stops the others being excused too, and the finding
said only what was wrong with the annotation, never what that cost. In this
record a four-code `unresolved-ok` in `doc_refs.py` went stale on one code and
silently un-acknowledged the other three — four citations in all. They showed
up as unaccounted for in a different section of a different report, with
nothing tying them to the annotation that had stopped covering them.

The finding now names the citations left unacknowledged. Still a report, not a
failure: which of them is a typo and which is deliberate is a judgement.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import ref_status  # noqa: E402

# One code per annotation rather than a shared list: a shared acknowledgement
# fails whole the moment any member goes stale, which is the failure the finding
# below exists to report, and this file should not be a fresh instance of it.
#
# Only the one code needs it. The `inactive-ok` fixture's own codes are written
# inside a directive-SHAPED string, and `scan` blanks those by design — naming a
# code in a directive is not citing it, for a live annotation and an example of
# one alike — so they are never counted and an acknowledgement of them would
# itself be stale. luria said so the moment one was added.
# unresolved-ok-file: ADR-777 — a fixture code, deliberately naming nothing


def _doc(root: Path, number: int, body: str = "Body.", status: str = "Active") -> Path:
    path = root / "record" / "decisions.d" / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstatus: {status}\ntitle: 'Decision {number}'\ntags:\n- t\n"
        f"date: '2026-01-01'\n---\n\n# ADR-{number:03d}: Decision {number}\n\n{body}\n",
        encoding="utf-8")
    return path


def _stale(project) -> list[str]:
    ref_status.forget_scan()
    return ref_status.stale_annotations()


def test_it_names_the_citations_left_unacknowledged(project):
    """The real case: one code in the list starts resolving, and the codes
    beside it quietly stop being excused."""
    _doc(project, 1)
    _doc(project, 2, body=(
        "<!-- unresolved-ok-file: ADR-777, ADR-001 — illustrative codes -->\n\n"
        "Cites ADR-777 here.\n\nAnd ADR-777 again.\n\nAnd ADR-777 once more.\n"))

    lines = _stale(project)
    assert len(lines) == 1, lines
    assert "which does resolve here" in lines[0], lines[0]
    assert "ADR-777 (3 sites)" in lines[0], \
        f"the cost of the poisoned annotation is not named: {lines[0]}"


def test_a_single_site_reads_singular(project):
    _doc(project, 1)
    _doc(project, 2, body=(
        "<!-- unresolved-ok-file: ADR-777, ADR-001 — illustrative codes -->\n\n"
        "Cites ADR-777 once.\n"))

    line = _stale(project)[0]
    assert "ADR-777 (1 site)" in line, line


def test_a_poisoned_annotation_covering_nothing_else_says_nothing_more(project):
    """No citations lost means no tail — the message must not grow a limp
    clause when there was no cost."""
    _doc(project, 1)
    _doc(project, 2, body=(
        "<!-- unresolved-ok-file: ADR-001 — names only a code that resolves -->\n\n"
        "No dangling citation in this file.\n"))

    line = _stale(project)[0]
    assert "which does resolve here" in line
    assert "unacknowledged" not in line, \
        f"nothing was lost, so nothing should be reported lost: {line}"


def test_the_cost_respects_the_annotation_scope(project):
    """A line-scoped annotation only ever covered its own line, so only the
    citations it actually covered are its to lose."""
    _doc(project, 1)
    _doc(project, 2, body=(
        "Cites ADR-777 outside the annotation's scope.\n\n"
        "<!-- unresolved-ok: ADR-777, ADR-001 — illustrative -->\n"
        "Cites ADR-777 inside it.\n"))

    line = next(l for l in _stale(project) if "does resolve here" in l)
    assert "ADR-777 (1 site)" in line, \
        f"only the covered site is this annotation's to lose: {line}"


def test_a_healthy_annotation_is_unchanged(project):
    """The existing branch — an annotation with no problem that simply excuses
    nothing — must keep its own wording."""
    _doc(project, 1)
    _doc(project, 2, body=(
        "<!-- unresolved-ok-file: ADR-777 — nothing here cites it -->\n\n"
        "No citation at all.\n"))

    line = _stale(project)[0]
    assert "no longer applies" in line and "nothing in scope cites" in line, line


def test_a_retired_document_loses_its_excuse_the_same_way(project):
    """The same failure on the `inactive-ok` side: the annotation is poisoned
    by naming a document that does not exist, and the retired document beside
    it stops being excused."""
    _doc(project, 1, status="Superseded")
    _doc(project, 2, body=(
        "<!-- inactive-ok-file: ADR-001, ADR-778 — one real, one not -->\n\n"
        "Cites ADR-001 here.\n\nAnd ADR-001 again.\n"))

    line = next(l for l in _stale(project) if "unknown document" in l)
    assert "ADR-001 (2 sites)" in line, \
        f"the retired document's citations were lost too: {line}"
