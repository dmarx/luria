"""The parse cache under `Adr` (#249).

Every `Adr` construction parsed the file it names, and the schemes are loaded
once per consumer rather than once per run — so one `luria lint` over a
729-document record parsed 16,872 frontmatter blocks, about 23 per document.

A cache is only safe here because `field_edit` and `repair` write documents
mid-run and read them back, so the invalidation has to be the filesystem's own:
`(mtime_ns, size)`, the bargain `_NUMBER_CACHE` already takes.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import adr_index as builder  # noqa: E402


def _doc(path: Path, title: str, body: str = "body") -> Path:
    path.write_text(f"---\nstatus: Active\ntitle: '{title}'\n---\n\n{body}\n",
                    encoding="utf-8")
    return path


def test_second_read_does_not_reparse(tmp_path, monkeypatch):
    path = _doc(tmp_path / "ADR-001.md", "First")
    builder.forget_documents()

    calls = []
    real = builder.parse_frontmatter
    monkeypatch.setattr(builder, "parse_frontmatter",
                        lambda text: calls.append(1) or real(text))

    assert builder.read_document(path)[0]["title"] == "First"
    assert builder.read_document(path)[0]["title"] == "First"
    assert len(calls) == 1, "the second read should answer from the cache"


def test_a_rewrite_invalidates_it(tmp_path):
    """The property the whole cache rests on: a writer bumps the mtime, so no
    caller has to remember to drop anything."""
    path = _doc(tmp_path / "ADR-001.md", "First")
    builder.forget_documents()
    assert builder.read_document(path)[0]["title"] == "First"

    _doc(path, "Second", body="a longer body, so the size moves too")
    import os
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))

    assert builder.read_document(path)[0]["title"] == "Second"


def test_callers_cannot_scribble_on_each_others_metadata(tmp_path):
    """`Adr` folds derived fields into the mapping it is handed. A shared dict
    would let one reading's derivation leak into the next — the failure the
    per-`Adr` resolver exists to avoid (#233), reintroduced one layer down."""
    path = _doc(tmp_path / "ADR-001.md", "First")
    builder.forget_documents()

    first, _ = builder.read_document(path)
    first["title"] = "scribbled"
    first.setdefault("tags", []).append("invented")

    second, _ = builder.read_document(path)
    assert second["title"] == "First"
    assert "tags" not in second


def test_body_survives_the_round_trip(tmp_path):
    path = _doc(tmp_path / "ADR-001.md", "First", body="# ADR-001: First\n\ntext")
    builder.forget_documents()
    meta, body = builder.read_document(path)
    assert meta["status"] == "Active"
    assert body.strip().endswith("text")
    assert builder.read_document(path)[1] == body


def test_a_document_with_no_frontmatter_still_reads(tmp_path):
    path = tmp_path / "ADR-001.md"
    path.write_text("no frontmatter here\n", encoding="utf-8")
    builder.forget_documents()
    meta, body = builder.read_document(path)
    assert meta == {}
    assert body == "no frontmatter here\n"
