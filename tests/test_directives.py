"""Tests for scripts/ci/directives.py — the shared comment-directive parser.

Two checks take instructions from the prose they check, so the scope rules are
the contract between an author and the tooling. They also have to survive being
*documented*: an example of a directive must not fire, or writing the manual
changes the behaviour it describes.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

import pytest  # noqa: E402

from luria import directives, syntax  # noqa: E402

MD = Path("notes.md")
PY = Path("thing.py")
TS = Path("thing.ts")


def find(text, path=MD, names=None):
    return directives.find(path, text, names)


# ── Shape ────────────────────────────────────────────────────────────────


def test_parses_name_args_and_reason():
    """The codes here are a made-up scheme on purpose: the parser knows nothing
    about ADRs, and real codes in fixtures would show up in `luria reports`."""
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


# ── Frontmatter ──────────────────────────────────────────────────────────


def test_a_yaml_comment_in_frontmatter_is_a_comment():
    """A reference field is a citation site, and the frontmatter is YAML —
    so the comment that answers a finding there is a `#` one, line-scoped
    like everywhere else: its own line and the field below it."""
    text = ("---\n"
            "status: Superseded\n"
            "# inactive-ok: RFC-012 — the successor was itself later retired\n"
            "superseded_by: RFC-012\n"
            "title: 'Issue #12 is data, not a comment'\n"
            "---\n"
            "\n"
            "# RFC-013: A heading is not a comment either\n"
            "\n"
            "Body per RFC-012.\n")
    d, = find(text)
    assert d.name == "inactive-ok" and d.args == ("RFC-012",)
    assert d.reason == "the successor was itself later retired"
    assert d.line == 3 and d.lines == frozenset({3, 4})


def test_a_directive_shaped_heading_in_the_body_does_not_fire():
    """`#` opens a heading outside the frontmatter. The scan never leaves the
    frontmatter, so prose *about* the syntax stays prose."""
    assert find("---\ntitle: t\n---\n\n# inactive-ok: RFC-012 — a heading\n") == []


def test_no_frontmatter_means_no_yaml_comments():
    assert find("# inactive-ok: RFC-012 — a heading in a file with no frontmatter\n") == []


def test_frontmatter_and_html_comments_are_both_read_in_order():
    text = ("---\n"
            "# inactive-ok: RFC-012 — in the frontmatter\n"
            "status: Active\n"
            "---\n"
            "\n"
            "<!-- inactive-ok: RFC-020 — in the body -->\n"
            "RFC-020 here.\n")
    assert [(d.line, d.args) for d in find(text)] == [(2, ("RFC-012",)), (6, ("RFC-020",))]


def test_in_frontmatter_the_line_below_is_the_whole_entry():
    """`luria repair` writes `superseded_by:` as a list, so the code sits on
    the line after the key; a directive above the key has to reach it."""
    text = ("---\n"
            "status: Superseded\n"
            "# inactive-ok: RFC-012 — the chain is deliberate\n"
            "superseded_by:\n"
            "- RFC-012\n"
            "- RFC-020\n"
            "status_note: >-\n"
            "  a folded note\n"
            "  on two lines\n"
            "title: t\n"
            "---\n"
            "\n"
            "RFC-012 in the body is not reached.\n")
    d, = find(text)
    assert d.lines == frozenset({3, 4, 5, 6})


def test_in_prose_the_line_below_is_still_one_line():
    d, = find("<!-- inactive-ok: RFC-012 — x -->\n- RFC-012\n- RFC-020\n")
    assert d.lines == frozenset({1, 2})


# --- a docstring is one block (#222) -----------------------------------------

def test_a_block_directive_above_a_def_reaches_its_whole_docstring(tmp_path):
    """The case that motivated this: a citation in a docstring's *third*
    paragraph. Before, only `-file` reached it — far too blunt for one
    sentence of prose that happens to name a code."""
    src = ('# inactive-ok-block: ADR-012 — the decision this replaced\n'
           'def apply():\n'
           '    """First paragraph.\n'
           '\n'
           '    Second paragraph.\n'
           '\n'
           '    A third one citing ADR-012.\n'
           '    """\n'
           '    return 1\n')
    path = tmp_path / "m.py"
    path.write_text(src)
    found = directives.find(path, src)
    assert len(found) == 1
    cite = next(n for n, line in enumerate(src.splitlines(), 1)
                if "citing ADR-012" in line)
    assert cite in found[0].lines


def test_a_docstring_is_atomic_the_way_a_fence_is(tmp_path):
    """The principle it rests on, already in the rules for fenced code: a
    blank line inside one syntactic unit does not end the paragraph."""
    src = ('def apply():\n'
           '    """One.\n'
           '\n'
           '    Two.\n'
           '    """\n'
           '    return 1\n')
    # One run: the docstring's internal blank line no longer splits it, so the
    # definition and its body are a single block.
    assert directives.blocks(src, tmp_path / "m.py") == [(1, 6)]
    # Without the language, that blank line splits it as it always did.
    assert directives.blocks(src) == [(1, 2), (4, 6)]


def test_a_directive_written_inside_a_docstring_still_does_not_fire(tmp_path):
    """Unchanged, and load-bearing: a docstring is not a comment, so prose
    that looks like a directive is prose."""
    src = ('def apply():\n'
           '    """inactive-ok: ADR-012 — not a comment.\n'
           '\n'
           '    Citing ADR-012.\n'
           '    """\n'
           '    return 1\n')
    path = tmp_path / "m.py"
    path.write_text(src)
    assert directives.find(path, src) == []


def test_unparseable_python_yields_no_docstring_spans(tmp_path):
    """A directive's scope is not where a syntax error should surface."""
    assert directives.blocks("def (\n", tmp_path / "m.py") is not None


# ── The same block rule, in languages luria knows nothing about ──────────

needs_grammar = pytest.mark.skipif(not syntax.available(),
                                   reason="tree-sitter is an optional extra")


@needs_grammar
@pytest.mark.parametrize("name,src", [
    ("m.go", "// inactive-ok-block: RFC-012\nfunc f() {\n\n\treturn RFC012\n}\n"),
    ("m.rs", "// inactive-ok-block: RFC-012\nfn f() {\n\n    RFC012;\n}\n"),
    ("m.sh", "# inactive-ok-block: RFC-012\nf() {\n\n  echo RFC012\n}\n"),
    ("m.yaml", "# inactive-ok-block: RFC-012\njobs:\n  a:\n\n    run: RFC012\n"),
])
def test_block_reaches_past_a_blank_line_inside_one_unit(tmp_path, name, src):
    """The docstring case was never about docstrings. Every language has a
    construct that holds a blank line, and the run-of-non-blank-lines rule is
    wrong in all of them the same way."""
    path = tmp_path / name
    path.write_text(src)
    d, = directives.find(path, src)
    cite = next(n for n, line in enumerate(src.splitlines(), 1)
                if "RFC012" in line)
    assert d.covers(cite)


@needs_grammar
def test_a_block_does_not_grow_into_the_next_entry(tmp_path):
    """Growth stops at the unit the directive introduces. A top-level comment's
    next sibling is the whole YAML document; taking that would make `-block`
    mean `-file` in every workflow file in the repository."""
    src = ("# inactive-ok-block: RFC-012\njobs:\n  a: RFC012\n\nafter: RFC012\n")
    path = tmp_path / "wf.yaml"
    path.write_text(src)
    d, = directives.find(path, src)
    assert d.covers(3) and not d.covers(5)


@needs_grammar
def test_a_directive_inside_a_string_is_not_a_comment(tmp_path):
    """What the marker scan cannot do, and says so in its own comment."""
    for name, src in [
            ("m.sh", "echo 'inactive-ok: RFC-012'\n"),
            ("m.yaml", 'run: "inactive-ok: RFC-012"\n'),
            ("m.go", "var s = `inactive-ok: RFC-012`\n")]:
        path = tmp_path / name
        path.write_text(src)
        assert directives.find(path, src) == [], name


@needs_grammar
def test_a_directive_appended_after_other_comment_text_still_reads(tmp_path):
    """A grammar reads `// note  // dir: x` as one comment, which is true and
    would drop the directive. The spelling predates the grammar and keeps
    working: precision is applied to finding comments, not to redefining where
    one starts."""
    src = "// shaped by RFC-012  // inactive-ok: RFC-012\n"
    path = tmp_path / "m.go"
    path.write_text(src)
    d, = directives.find(path, src)
    assert d.args == ("RFC-012",)


@needs_grammar
def test_growth_never_narrows_what_a_block_already_covered(tmp_path):
    """The rule is a union. A file that lints today cannot start failing
    because a grammar has a tidier opinion about its blocks."""
    src = "# inactive-ok-block: RFC-012\nalpha = RFC012\nbeta = RFC012\n"
    path = tmp_path / "m.py"
    path.write_text(src)
    d, = directives.find(path, src)
    assert d.covers(2) and d.covers(3)
