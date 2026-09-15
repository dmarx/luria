# tests/test_mention_ok.py
"""`mention-ok:` — a code is named, not cited (ADR-tmphuvta).

Every other acknowledgement asserts something about a code's state, and so
retires correctly when that state changes: `inactive-ok` says the document is
not in force, `unresolved-ok` says the code resolves to nothing. Some
references assert neither — a specimen quoted as evidence, prose about a code's
literal spelling, a demonstration of what a moved address looks like. Written
as `unresolved-ok` those go stale the day somebody allocates that number, for a
reason unrelated to why they were written, and take every code in the same
annotation with them.

The load-bearing rule is what "still applies" means here. A `mention-ok` is
used when the code it names is cited in its scope, WHATEVER the document's
state — otherwise it would rot at exactly the moment it exists to survive.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import ref_status  # noqa: E402

# The specimens below are named, not cited, and both numbers are reachable —
# which is the case this whole file is about. Spelling them `unresolved-ok`
# would schedule exactly the failure the new word exists to avoid.
# mention-ok-file: ADR-404 — a specimen quoted by these tests
# mention-ok-file: ADR-405 — the same


def _doc(root: Path, number: int, body: str = "Body.", status: str = "Active") -> Path:
    path = root / "record" / "decisions.d" / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstatus: {status}\ntitle: 'Decision {number}'\ntags:\n- t\n"
        f"date: '2026-01-01'\n---\n\n# ADR-{number:03d}: Decision {number}\n\n{body}\n",
        encoding="utf-8")
    return path


def _scan(project):
    ref_status.forget_scan()
    return ref_status.scan()


def test_it_excuses_a_code_that_resolves_to_nothing(project):
    _doc(project, 1, body=(
        "<!-- mention-ok: ADR-404 — quoted as a specimen -->\n"
        "The specimen is ADR-404.\n"))
    result = _scan(project)
    sites = result.dangling.get("ADR-404", [])
    assert sites and all(c.excused_by is not None for c in sites), \
        "a named code that resolves to nothing is excused"


def test_it_excuses_a_retired_document_too(project):
    """One word covers both findings, because a mention makes no claim either
    way — which of the two applies is a fact about the record, not the text."""
    _doc(project, 1, status="Superseded")
    _doc(project, 2, body=(
        "<!-- mention-ok: ADR-001 — quoted as a specimen -->\n"
        "The specimen is ADR-001.\n"))
    result = _scan(project)
    sites = result.cited.get("ADR-001", [])
    assert sites and all(c.excused_by is not None for c in sites)


def test_it_survives_the_code_becoming_a_real_document(project):
    """The whole point. `unresolved-ok` goes stale here; this must not."""
    _doc(project, 2, body=(
        "<!-- mention-ok: ADR-001 — quoted as a specimen -->\n"
        "The specimen is ADR-001.\n"))
    ref_status.forget_scan()
    assert not ref_status.stale_annotations(), "nothing exists at ADR-001 yet"

    _doc(project, 1)                       # the number gets allocated
    ref_status.forget_scan()
    assert not ref_status.stale_annotations(), \
        "a mention says nothing about status, so status changing cannot stale it"


def test_an_unresolved_ok_in_the_same_place_does_go_stale(project):
    """The contrast that motivates the new word — same site, old spelling."""
    _doc(project, 2, body=(
        "<!-- unresolved-ok: ADR-001 — quoted as a specimen -->\n"
        "The specimen is ADR-001.\n"))
    _doc(project, 1)
    ref_status.forget_scan()
    stale = ref_status.stale_annotations()
    assert any("does resolve here" in s for s in stale), stale


def test_it_still_goes_stale_when_the_mention_is_gone(project):
    """The one staleness that was ever about this annotation rather than about
    the document: nothing in scope names the code any more."""
    _doc(project, 2, body=(
        "<!-- mention-ok: ADR-404 — quoted as a specimen -->\n"
        "No specimen in this text.\n"))
    ref_status.forget_scan()
    stale = ref_status.stale_annotations()
    assert any("nothing in scope cites ADR-404" in s for s in stale), stale


def test_its_own_arguments_are_not_read_as_citations(project):
    """The directive names codes; naming them is not citing them. Without this
    the annotation would excuse a mention it created itself."""
    _doc(project, 2, body=(
        "<!-- mention-ok: ADR-404 — quoted as a specimen -->\n"
        "No other text names it.\n"))
    result = _scan(project)
    assert "ADR-404" not in result.dangling, \
        "the directive's own argument list must be blanked before the scan"


def test_a_mention_naming_no_code_is_reported(project):
    """It makes no claim about state, which is not the same as making no claim
    at all — it still has to name a code."""
    _doc(project, 2, body=(
        "<!-- mention-ok: 404 — a bare number is not a code -->\n"
        "The specimen is ADR-404.\n"))
    ref_status.forget_scan()
    stale = ref_status.stale_annotations()
    assert any("names no document code" in s for s in stale), stale


def test_a_mention_mixing_a_code_with_a_bare_number_is_reported(project):
    """The same malformedness checks as the other kinds, in the same order: a
    bare number is only reportable as one once something in the list parsed."""
    _doc(project, 2, body=(
        "<!-- mention-ok: ADR-404, 405 — one code and one number -->\n"
        "The specimens are ADR-404 and ADR-405.\n"))
    ref_status.forget_scan()
    stale = ref_status.stale_annotations()
    assert any("bare number" in s for s in stale), stale


def test_it_is_counted_like_every_other_acknowledgement(project):
    """A suppression nobody counts is a suppression nobody notices."""
    _doc(project, 2, body=(
        "<!-- mention-ok: ADR-404 — quoted as a specimen -->\n"
        "The specimen is ADR-404.\n"))
    result = _scan(project)
    assert ref_status.dangling_acknowledged_count(result) >= 1
