"""Tests for luria/syntax.py — the optional tree-sitter backing for directives.

The module is an *extra*: every test here has to state which side of that line
it stands on. Tests that need a grammar skip when tree-sitter is not installed;
tests about the fallback run either way, because the fallback is what most
installs get.
"""
from pathlib import Path

import pytest

from luria import syntax

pytestmark = pytest.mark.skipif(not syntax.available(),
                                reason="tree-sitter is an optional extra")


# ── Comments, without a per-language table ───────────────────────────────

CASES = {
    "m.py": "# dir: X\ndef f():\n    return 1\n",
    "m.yaml": "# dir: X\njobs:\n  a: 1\n",
    "m.sh": "# dir: X\nf() {\n  echo hi\n}\n",
    "m.go": "// dir: X\nfunc f() {\n}\n",
    "m.rs": "// dir: X\nfn f() {\n}\n",
    "m.js": "// dir: X\nfunction f() {\n}\n",
    "m.c": "/* dir: X */\nint f(void) {\n  return 1;\n}\n",
    "m.toml": "# dir: X\n[a]\nb = 1\n",
}


@pytest.mark.parametrize("name,src", sorted(CASES.items()))
def test_one_comment_rule_covers_every_language(name, src):
    """`"comment" in node.type` is the whole of luria's per-language knowledge.
    Seven grammars spell the node `comment` and Rust spells it `line_comment`;
    nothing here enumerates either."""
    found = syntax.comments(Path(name), src)
    assert found is not None
    # `*/` is left on the body: the directive parser already ends an argument
    # list there, and trimming trailing punctuation would eat a reason's stop.
    assert [(line, body.split("*/")[0].strip())
            for line, _, body in found] == [(1, "dir: X")]


def test_a_hash_inside_a_string_is_not_a_comment():
    """The crude marker scan cannot tell these apart, and says so in its own
    comment. A grammar can, in every language at once."""
    assert syntax.comments(Path("m.sh"), "echo 'a # not a comment'\n") == []
    assert syntax.comments(Path("m.go"), "var s = `raw # string`\n") == []
    assert syntax.comments(Path("m.yaml"), 'run: "echo see # X"\n') == []


def test_a_real_comment_beside_a_string_still_reads():
    """The point is precision, not silence."""
    found = syntax.comments(Path("m.sh"), "echo 'a # b'  # dir: X\n")
    assert [body.strip() for _, _, body in found] == ["dir: X"]


def test_offsets_are_character_offsets_not_byte_offsets():
    """Every other scanner in luria hands out character offsets, and a
    directive's span is compared against them."""
    src = "# héllo\n# dir: X\n"
    found = syntax.comments(Path("m.py"), src)
    line, offset, _ = found[1]
    assert (line, offset) == (2, src.index("# dir"))


def test_an_unparseable_file_yields_nothing_rather_than_guessing():
    """A grammar that cannot parse the file has no opinion worth acting on, and
    the caller falls back to the scan that at least sees the text."""
    assert syntax.comments(Path("m.py"), "def (((\n# dir: X\n") is None


def test_a_suffix_no_grammar_claims_is_not_an_error():
    assert syntax.comments(Path("m.unheardof"), "# dir: X\n") is None


# ── Growth: the block a comment introduces ───────────────────────────────

DOCSTRING = (
    "# dir: X\n"
    "def apply():\n"
    "    '''First paragraph.\n"
    "\n"
    "    A later paragraph citing X.'''\n"
)


def test_growth_reaches_past_a_blank_line_inside_one_syntactic_unit():
    """The case this exists for: the blank-line run stops at line 3, and the
    citation is on line 5. The definition is one node, so the block is too."""
    assert syntax.grow(Path("m.py"), DOCSTRING, (1, 3), after=1) == (1, 5)


def test_growth_never_shrinks_a_block():
    """The rule is a union with the blank-line block, so a directive that works
    today cannot stop working because a grammar disagrees."""
    src = "# dir: X\nalpha = 1\nbeta = 2\n"
    assert syntax.grow(Path("m.py"), src, (1, 3), after=1) == (1, 3)


def test_growth_takes_the_smallest_unit_that_holds_the_block():
    """A top-level YAML comment's next sibling is the whole document, which
    would make `-block` mean `-file`. The smallest node that starts where the
    block's content starts and still holds the block is the `jobs:` entry."""
    src = "# dir: X\njobs:\n  a:\n\n    run: echo X\n\nafter: 1\n"
    assert syntax.grow(Path("m.yaml"), src, (1, 3), after=1) == (1, 5)


def test_growth_stops_at_the_entry_it_introduces():
    """Same file, one line later: `after:` is a sibling entry, not part of the
    block, and nothing grows into it."""
    src = "# dir: X\njobs:\n  a: 1\n\nafter: 1\n"
    assert syntax.grow(Path("m.yaml"), src, (1, 3), after=1) == (1, 3)


@pytest.mark.parametrize("name,src,block,want", [
    ("m.go", "// dir: X\nfunc f() {\n\n\treturn\n}\n", (1, 2), (1, 5)),
    ("m.rs", "// dir: X\nfn f() {\n\n    ();\n}\n", (1, 2), (1, 5)),
    ("m.js", "// dir: X\nfunction f() {\n\n  return 1;\n}\n", (1, 2), (1, 5)),
    ("m.sh", "# dir: X\nf() {\n\n  echo hi\n}\n", (1, 2), (1, 5)),
    ("m.c", "/* dir: X */\nint f(void) {\n\n  return 1;\n}\n", (1, 2), (1, 5)),
])
def test_growth_is_the_same_rule_in_every_language(name, src, block, want):
    assert syntax.grow(Path(name), src, block, after=1) == want


def test_growth_declines_on_an_unparseable_file():
    assert syntax.grow(Path("m.py"), "def (((\n", (1, 1), after=1) == (1, 1)


# ── The opt-out ──────────────────────────────────────────────────────────


def test_the_extra_can_be_turned_off_without_uninstalling_it(monkeypatch):
    """A grammar that misreads a file is a bug someone needs a way around
    tonight, not after a release."""
    monkeypatch.setenv("LURIA_TREE_SITTER", "0")
    syntax.available.cache_clear()
    try:
        assert not syntax.available()
        assert syntax.comments(Path("m.py"), "# dir: X\n") is None
        assert syntax.grow(Path("m.py"), DOCSTRING, (1, 3), after=1) == (1, 3)
    finally:
        syntax.available.cache_clear()


# ── The repository itself ────────────────────────────────────────────────


def test_every_file_in_this_repository_scans_without_crashing():
    """Not a formality. Two lifetime bugs in this module took a real file to
    reproduce and killed the process rather than raising, which no other test
    here can see: a `try` catches an exception, not a segfault. Scanning the
    tree is the only check that runs the grammars over the shapes people
    actually write."""
    from luria import directives

    repo = Path(__file__).resolve().parents[1]
    scanned = 0
    for path in sorted(repo.rglob("*")):
        if ".git/" in str(path) or not path.is_file() or not path.suffix:
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        directives.find(path, text)
        scanned += 1
    assert scanned > 100
