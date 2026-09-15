# tests/test_one_reader.py
"""One reader for a document, read the same way everywhere (DP-4).

`read_document` is the cache, and its invalidation is the bargain that makes
caching safe here at all: a writer bumps the file's mtime, so the entry
expires on its own, and `field_edit` and `repair` can write mid-run and read
back. A second reader that opens and parses the file itself does not take
that bargain — it cannot be dropped by `forget_documents()`, and it can see a
different revision than every other caller inside one run.

Eleven call sites composed `parse_frontmatter(path.read_text(...))` and so
were second readers. This pins the shape closed, because the drift DP-4 names
is not a thing you fix once: `documents()`'s own docstring records five
copies of one glob accumulating, "harmless only for as long as the filename
shape never changed".
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import adr_index as builder  # noqa: E402
from luria import config  # noqa: E402

# `parse_frontmatter(<anything>.read_text(...))` — the composed form that
# opens a file. Parsing text a caller already holds is not a second reader
# and is not matched.
SECOND_READER = re.compile(
    r"parse_frontmatter\(\s*[A-Za-z_][\w.]*\.read_text\(", re.S)


def test_no_module_opens_a_document_for_itself():
    offenders = []
    for path in sorted((REPO / "luria").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for m in SECOND_READER.finditer(text):
            line = text[:m.start()].count("\n") + 1
            if path.name == "adr_index.py" and _inside_read_document(text, m.start()):
                continue  # the one reader, reading
            offenders.append(f"{path.name}:{line}")
    assert not offenders, (
        "these open and parse a document instead of asking `read_document`: "
        + ", ".join(offenders))


def _inside_read_document(text: str, at: int) -> bool:
    """The fallback inside `read_document` itself, for a path it cannot stat."""
    start = text.rfind("\ndef ", 0, at)
    return text[start:at].lstrip().startswith("def read_document")


def test_two_consumers_parse_each_document_once(tmp_path, monkeypatch):
    """The behaviour the shape is for: a second pass over the same corpus
    costs no parses, whichever consumer asks."""
    (tmp_path / "luria.yaml").write_text(
        "issue_url: https://example.test/{n}\n"
        "schemes:\n  ADR:\n    dir: record/decisions.d\n"
        "    output: docs/decisions\n", encoding="utf-8")
    d = tmp_path / "record" / "decisions.d"
    d.mkdir(parents=True)
    for n in (1, 2, 3):
        (d / f"ADR-{n:03d}.md").write_text(
            f"---\nnumber: {n}\nstatus: Active\ntitle: 'D{n}'\n---\n\nbody\n",
            encoding="utf-8")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    builder.forget_documents()

    calls = []
    real = builder.parse_frontmatter
    monkeypatch.setattr(builder, "parse_frontmatter",
                        lambda text: calls.append(1) or real(text))

    scheme = config.current().schemes["ADR"]
    from luria import statuses
    statuses._observed(scheme)
    first = len(calls)
    assert first, "the first pass must actually read something"
    statuses._observed(scheme)
    assert len(calls) == first, "the second pass should parse nothing again"
    config.reset()
