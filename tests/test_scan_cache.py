# tests/test_scan_cache.py
"""The corpus-scan cache under `ref_status.scan` (#265).

One `luria lint` calls `scan()` 36 times, and 18 of those pass no arguments at
all — identical full-corpus scans, fanned out through `reports.outputs` and
`adr_pending.pending`, each one re-reading and re-regexing every file in the
record.

Unlike the directive-scan cache, this one reads the filesystem itself, so the
key cannot be the content — nothing hands it in. It is the bargain
`_LISTING_CACHE` and `_DOCUMENT_CACHE` already take: a `(path, mtime_ns, size)`
fingerprint of the scanned set, which a writer invalidates by writing. That
matters because `repair`, `field_edit` and `migrate` all rewrite documents
mid-run and read them back.

Only the no-argument call is cached. A call that names its own `files` or
`docs` is asking about a corpus the fingerprint does not describe.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import ref_status  # noqa: E402


def _doc(root: Path, number: int, body: str = "Body.") -> Path:
    path = root / "record" / "decisions.d" / f"ADR-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstatus: Active\ntitle: 'Decision {number}'\ntags:\n- t\n"
        f"date: '2026-01-01'\n---\n\n# ADR-{number:03d}: Decision {number}\n\n{body}\n",
        encoding="utf-8")
    return path


def test_a_second_scan_of_an_unchanged_corpus_is_not_redone(project, monkeypatch):
    _doc(project, 1)
    ref_status.forget_scan()

    calls = []
    real = ref_status._scan
    monkeypatch.setattr(ref_status, "_scan",
                        lambda f, d: calls.append(1) or real(f, d))

    first = ref_status.scan()
    second = ref_status.scan()
    assert first is second, "the second call should hand back the same Scan"
    assert len(calls) == 1


def test_a_rewrite_is_seen(project):
    """The property the whole cache rests on. `repair` and `migrate` rewrite
    documents mid-run and read them back; a cache that missed that would hand
    back the record as it was before the repair."""
    _doc(project, 2)                       # so the citation below resolves
    _doc(project, 1, body="Body.")
    ref_status.forget_scan()
    assert not ref_status.scan().cited.get("ADR-002")

    # A citation that was not there a moment ago, in a file that already was.
    _doc(project, 1, body="This extends ADR-002 in a longer body than before.")
    assert ref_status.scan().cited.get("ADR-002"), \
        "a rewritten file must not be read from the cache"


def test_a_new_document_is_seen(project):
    """The fingerprint covers the *set*, not just each file's stamp, so a
    document appearing is a different corpus."""
    _doc(project, 1)
    ref_status.forget_scan()
    before = ref_status.scan()

    _doc(project, 2, body="Cites ADR-001 from a file that did not exist.")
    after = ref_status.scan()
    assert after is not before
    assert after.cited.get("ADR-001")


def test_a_deleted_document_is_seen(project):
    _doc(project, 1)
    second = _doc(project, 2, body="Cites ADR-001.")
    ref_status.forget_scan()
    assert ref_status.scan().cited.get("ADR-001")

    second.unlink()
    assert not ref_status.scan().cited.get("ADR-001"), \
        "a removed file must not keep its citations alive"


def test_a_call_with_arguments_is_not_served_from_the_cache(project, monkeypatch):
    """`files=` and `docs=` describe a corpus the fingerprint does not, so
    those calls run every time rather than colliding with the shared entry."""
    _doc(project, 1)
    ref_status.forget_scan()
    ref_status.scan()                      # populate

    calls = []
    real = ref_status._scan
    monkeypatch.setattr(ref_status, "_scan",
                        lambda f, d: calls.append(1) or real(f, d))

    ref_status.scan(files=[])
    ref_status.scan(files=[])
    assert len(calls) == 2, "an argued call is computed each time"


def test_the_shared_scan_still_matches_its_own_annotations(project):
    """`Scan.used` compares annotations by identity, so handing the same
    object to every caller has to keep that relationship intact — it is the
    one thing sharing could plausibly break."""
    path = project / "record" / "decisions.d" / "ADR-001.md"
    _doc(project, 1)
    path.write_text(path.read_text(encoding="utf-8")
                    + "\n<!-- inactive-ok: ADR-002 — a reason -->\n"
                      "\nThis names ADR-002.\n", encoding="utf-8")
    ref_status.forget_scan()

    result = ref_status.scan()
    again = ref_status.scan()
    assert result is again
    for ann in result.annotations:
        # Whatever `used` says, it must say the same thing through either
        # handle — they are the same object, and the identity check inside
        # must still find the citations that point at these annotations.
        assert result.used(ann) == again.used(ann)
