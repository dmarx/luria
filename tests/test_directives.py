"""Tests for scripts/ci/directives.py — the shared comment-directive parser.

Two checks take instructions from the prose they check, so the scope rules are
the contract between an author and the tooling. They also have to survive being
*documented*: an example of a directive must not fire, or writing the manual
changes the behaviour it describes.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

from luria import directives  # noqa: E402

MD = Path("notes.md")
PY = Path("thing.py")
TS = Path("thing.ts")


def find(text, path=MD, names=None):
    return directives.find(path, text, names)


# ── Shape ────────────────────────────────────────────────────────────────


def test_parses_name_args_and_reason():
    """The codes here are a made-up scheme on purpose: the parser knows nothing
    about ADRs, and real codes in fixtures would show up in `make ref-status`."""
    d, = find("<!-- inactive-ok: RFC-012, RFC-020 — the history -->\n")
    assert d.name == "inactive-ok"
    assert d.args == ("RFC-012", "RFC-020")
    assert d.reason == "the history"


def test_directive_must_open_its_comment():
    """`# noqa` convention. Matching mid-comment means prose *about* the syntax
    invokes it — comments in the scanner explaining these rules did exactly
    that before this held."""
    assert find("<!-- note that inactive-ok: RFC-012 exists -->\n") == []
    assert find("# see the inactive-ok: RFC-012 form\n", PY) == []


def test_examples_are_not_directives():
    """A fenced example in markdown and a docstring example in Python are not
    comments. Documenting the syntax must not activate it."""
    assert find("```\n<!-- inactive-ok-file: RFC-012 -->\n```\n") == []
    assert find('"""\n# inactive-ok-file: RFC-012\n"""\n', PY) == []
    assert find("`<!-- inactive-ok: RFC-012 -->` inline\n") == []


def test_reads_code_comments():
    d, = find("const x = 1;  // unexempt: codeblock — why\n", TS)
    assert (d.name, d.args) == ("unexempt", ("codeblock",))
    d, = find("x = 1  # inactive-ok: RFC-012\n", PY)
    assert d.name == "inactive-ok"


def test_second_comment_on_a_line_is_seen():
    d, = find("// shaped by RFC-012  // inactive-ok: RFC-012\n", TS)
    assert d.name == "inactive-ok"


def test_names_filter():
    text = "<!-- inactive-ok: RFC-012 -->\n<!-- unexempt: codeblock -->\n"
    assert [d.name for d in find(text, names={"unexempt"})] == ["unexempt"]


# ── Scope ────────────────────────────────────────────────────────────────


def test_line_scope_is_its_line_and_the_next():
    d, = find("text <!-- inactive-ok: RFC-012 -->\nnext\nfar\n")
    assert d.scope == directives.LINE
    assert d.covers(1) and d.covers(2) and not d.covers(3)


def test_block_scope_is_the_paragraph():
    d, = find("a <!-- inactive-ok-block: RFC-012 -->\nb\nc\n\nd\n")
    assert d.scope == directives.BLOCK
    assert all(d.covers(n) for n in (1, 2, 3)) and not d.covers(5)


def test_file_scope_is_everything():
    d, = find("<!-- inactive-ok-file: RFC-012 -->\n\na\n\n\nb\n")
    assert d.scope == directives.FILE
    assert d.covers(1) and d.covers(6) and d.covers(999)


def test_no_directive_has_its_own_default_scope():
    """The suffix decides, uniformly. A per-directive default is one more thing
    to remember, and it made the bare form reach across a blank line for one
    directive and not another."""
    for text in ("<!-- unexempt: codeblock -->\n```\nx\n```\n",
                 "<!-- inactive-ok: RFC-012 -->\nx\n"):
        d, = find(text)
        assert d.scope == directives.LINE


def test_a_bare_directive_does_not_reach_across_a_blank_line():
    """The rule that was tried and removed: a standalone bare directive silently
    governing the block below it. Convenient for one example, unpredictable
    everywhere else — `-block` says it out loud instead."""
    d, = find("<!-- inactive-ok: RFC-012 -->\n\nfirst\nsecond\n")
    assert d.covers(1) and d.covers(2) and not d.covers(3)


def test_a_standalone_block_directive_governs_the_block_it_introduces():
    """A directive alone between blank lines has no content block of its own, so
    the block it means is the next one. That is the reading of "block", not an
    exception to it."""
    d, = find("<!-- inactive-ok-block: RFC-012 -->\n\nfirst\nsecond\n\nlater\n")
    assert d.covers(3) and d.covers(4) and not d.covers(6)


def test_two_directives_in_one_standalone_block_both_reach():
    text = ("<!-- unexempt-block: codeblock --><!-- inactive-ok-block: RFC-012 -->"
            "\n\n```\nx\n```\n")
    assert all(d.covers(4) for d in find(text))


def test_a_bare_directive_flush_against_a_fence_reaches_it():
    """No blank line, so line scope covers the fence's opening line — and
    unexempting any line of a fence unexempts that fence."""
    d, = find("<!-- unexempt: codeblock -->\n```\nx\n```\n")
    assert d.covers(2)


# ── Blocks ───────────────────────────────────────────────────────────────


def test_a_fence_is_one_block_even_with_blank_lines():
    text = "intro\n\n```py\ndef f():\n\n    pass\n```\n\nafter\n"
    assert (3, 7) in directives.blocks(text)


def test_blocks_are_blank_line_delimited():
    assert directives.blocks("a\nb\n\nc\n") == [(1, 2), (4, 4)]


# ── Validation ───────────────────────────────────────────────────────────


def test_missing_argument_is_a_problem():
    d, = find("<!-- unexempt: -->\n")
    assert "names no argument" in directives.problems(d, {"codeblock"})


def test_unknown_argument_is_a_problem():
    d, = find("<!-- unexempt: sidebar -->\n")
    assert "unknown argument" in directives.problems(d, {"codeblock"})
    assert directives.problems(d, None) is None      # no vocabulary, no claim


def test_valid_directive_has_no_problem():
    d, = find("<!-- unexempt: codeblock — deliberate -->\n")
    assert directives.problems(d, {"codeblock"}) is None


# ── Shaped spans ─────────────────────────────────────────────────────────


def test_shaped_spans_match_examples_too():
    """A code named in directive syntax is being governed, not cited — whether
    the directive is live or an illustration of one."""
    text = "```\n<!-- inactive-ok: RFC-012 -->\n```\n"
    assert directives.shaped_spans(text, {"inactive-ok"})
    assert directives.shaped_spans(text, {"unexempt"}) == []
