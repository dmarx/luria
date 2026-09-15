# tests/test_directive_cache.py
"""The scan cache under `directives` (#265).

`_parse` re-derives two things for every directive lookup: the blank-line
blocks of a file, and every comment fragment in it. Both are pure functions of
`(path, text)`, and both are expensive on Python sources — `blocks` walks an
AST for docstring spans, `comment_fragments` runs the tokenizer.

Neither was cached, and the lookups are not one per file: a lint over this
repository called each of them 11,142 times over 451 distinct `(path, text)`
inputs, about 25 readings of every file. Tokenizing and walking the ASTs was
30 of the run's 33 seconds.

The key is the text itself rather than a stat, so a rewrite mid-run cannot be
read stale — the hazard `_DOCUMENT_CACHE` needs `(mtime_ns, size)` to dodge
does not arise when the caller hands the content in.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from luria import directives  # noqa: E402

SOURCE = '''\
"""Module docstring."""


# inactive-ok-block: ADR-001 — a reason
def f():
    """A docstring.

    With a second paragraph.
    """
    return 1
'''


def test_a_second_scan_of_the_same_text_does_not_retokenize(monkeypatch):
    path = Path("sample.py")
    directives.forget_scans()

    calls = []
    real = directives._comment_fragments
    monkeypatch.setattr(directives, "_comment_fragments",
                        lambda p, t: calls.append(1) or real(p, t))

    first = directives.comment_fragments(path, SOURCE)
    second = directives.comment_fragments(path, SOURCE)
    assert first == second
    assert len(calls) == 1, "the second scan should answer from the cache"


def test_a_second_blocks_call_does_not_rewalk_the_ast(monkeypatch):
    path = Path("sample.py")
    directives.forget_scans()

    calls = []
    real = directives._blocks
    monkeypatch.setattr(directives, "_blocks",
                        lambda t, p: calls.append(1) or real(t, p))

    assert directives.blocks(SOURCE, path) == directives.blocks(SOURCE, path)
    assert len(calls) == 1, "the second call should answer from the cache"


def test_a_rewrite_is_never_read_stale():
    """The property that makes keying on content safe: `field_edit` and
    `repair` rewrite files mid-run, and the new text is simply a different
    key rather than a stale entry waiting to be invalidated."""
    path = Path("sample.py")
    directives.forget_scans()

    assert directives.comment_fragments(path, "# one: A — r\n")[0][2] \
        .strip().startswith("one:")
    rewritten = directives.comment_fragments(path, "# two: B — r\n")
    assert rewritten[0][2].strip().startswith("two:")


def test_the_same_text_at_two_paths_is_not_confused():
    """A comment in Markdown and a comment in Python are not the same scan,
    so the path belongs in the key even when the bytes match."""
    directives.forget_scans()
    text = "# heading\n"
    as_python = directives.comment_fragments(Path("a.py"), text)
    as_markdown = directives.comment_fragments(Path("a.md"), text)
    assert as_python and not as_markdown, \
        "`# heading` is a comment in Python and prose in Markdown"


def test_a_caller_cannot_scribble_on_the_next_readers_result():
    """Both return lists, and a caller that mutates one would otherwise be
    editing what every later reading of that file sees."""
    path = Path("sample.py")
    directives.forget_scans()

    first = directives.comment_fragments(path, SOURCE)
    first.append((999, 0, "invented"))
    assert (999, 0, "invented") not in directives.comment_fragments(path, SOURCE)

    spans = directives.blocks(SOURCE, path)
    spans.append((999, 999))
    assert (999, 999) not in directives.blocks(SOURCE, path)


def test_unparseable_python_still_scans_through_the_cache():
    """The crude fallback is part of what gets cached, not a path around it."""
    directives.forget_scans()
    broken = "def f(:\n    # inactive-ok: ADR-001 — a reason\n"
    once = directives.comment_fragments(Path("broken.py"), broken)
    assert any("inactive-ok" in body for _, _, body in once)
    assert directives.comment_fragments(Path("broken.py"), broken) == once


def test_directives_still_resolve_the_lines_they_govern():
    """The cache sits under `_parse`, so the thing it speeds up must be
    unchanged: a `-block` directive above a definition still governs the
    whole docstring it introduces (#222)."""
    directives.forget_scans()
    found = directives.find(Path("sample.py"), SOURCE)
    assert len(found) == 1
    governed = found[0].lines
    assert 5 in governed, "the def line it introduces"
    assert 8 in governed, "the docstring's second paragraph, across its blank line"
