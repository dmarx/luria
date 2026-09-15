"""A field derived from a document this one references (ADR-092, #233).

`derive` computes a field from the document's own frontmatter. These tests
pin the second source: `from = "source[0]"` renders the same template against
the document that reference names, so a fact owned by one scheme can be read
by another instead of copied into it.

The copy is what this replaces, and the copy is what goes wrong — the
anthology found eight practices carrying the publication date of a source
they had stopped citing, invisible to every mechanical check because nothing
related one document's field to another's.
"""

from __future__ import annotations

from _config import merged

from pathlib import Path

import pytest

from luria import adr_index, config, contract


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


FOLLOW = """
schemes:
  SOTA:
    fields:
      published:
        derive: '{published}'
        from: source[0]
"""


def project(tmp_path, monkeypatch, extra: str = FOLLOW) -> Path:
    write(tmp_path, "luria.yaml", merged("""
                                  issue_url: https://example.test/issues/{n}
                                  schemes:
                                    LIT:
                                      dir: record/literature.d
                                      output: docs/literature
                                      fields:
                                        published:
                                          required: true
                                    SOTA:
                                      dir: record/practices.d
                                      output: docs/practices
                                      references:
                                        source:
                                          scheme: LIT
                                          required: true
                                          many: true
                                        paper:
                                          scheme: LIT
                                          required: false
                                          many: false
                                  """, extra))
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    return tmp_path


def paper(root: Path, number: int, published: str | None = "2020-10-01",
          extra: str = "") -> Path:
    front = ["---", "status: Active", f"title: 'Paper {number}'",
             "date: '2026-01-01'"]
    if published:
        front.append(f"published: '{published}'")
    if extra:
        front.append(extra)
    front += ["---", "", f"# LIT-{number:03d}: Paper {number}", "", "Body."]
    return write(root, f"record/literature.d/LIT-{number:03d}.md",
                 "\n".join(front) + "\n")


def practice(root: Path, number: int, *, source=(), paper_code: str = "",
             extra: str = "") -> Path:
    front = ["---", "status: Active", f"title: 'Practice {number}'",
             "date: '2026-01-01'"]
    if source:
        front.append("source:")
        front += [f"- {c}" for c in source]
    if paper_code:
        front.append(f"paper: {paper_code}")
    if extra:
        front.append(extra)
    front += ["---", "", f"# SOTA-{number:03d}: Practice {number}", "", "Body."]
    return write(root, f"record/practices.d/SOTA-{number:03d}.md",
                 "\n".join(front) + "\n")


def sota():
    return config.current().schemes["SOTA"]


def meta_of(path: Path) -> dict:
    return adr_index.Adr(path, sota()).meta


def findings(path: Path) -> list[str]:
    c = contract.for_scheme(sota())
    doc_meta, _ = adr_index.parse_frontmatter(path.read_text())
    known = {"LIT": contract.resolvable("LIT")}
    return contract.violations(c, config.current().rel(path), doc_meta, known)


# --- following the reference -------------------------------------------------

def test_an_indexed_reference_supplies_the_value(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    paper(root, 1, "2020-10-01")
    path = practice(root, 1, source=["LIT-001"])
    assert meta_of(path)["published"] == "2020-10-01"


def test_the_index_picks_which_reference(tmp_path, monkeypatch):
    """A practice with several sources takes its primary's date, and which
    one that is is the list's order — the property the whole feature rests on."""
    root = project(tmp_path, monkeypatch)
    paper(root, 1, "2020-10-01")
    paper(root, 2, "2023-03-01")
    first = practice(root, 1, source=["LIT-001", "LIT-002"])
    second = practice(root, 2, source=["LIT-002", "LIT-001"])
    assert meta_of(first)["published"] == "2020-10-01"
    assert meta_of(second)["published"] == "2023-03-01"


def test_a_scalar_reference_needs_no_index(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, FOLLOW.replace("from: source[0]", "from: paper"))
    paper(root, 7, "2019-05-01")
    path = practice(root, 1, source=["LIT-007"], paper_code="LIT-007")
    assert meta_of(path)["published"] == "2019-05-01"


def test_the_referenced_document_is_untouched(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    target = paper(root, 1, "2020-10-01")
    before = target.read_text()
    meta_of(practice(root, 1, source=["LIT-001"]))
    assert target.read_text() == before


# --- absence is absence, never a guess ---------------------------------------

def test_no_reference_derives_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    path = practice(root, 1)
    assert "published" not in meta_of(path)


def test_an_index_past_the_end_derives_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, FOLLOW.replace("from: source[0]", "from: source[2]"))
    paper(root, 1)
    path = practice(root, 1, source=["LIT-001"])
    assert "published" not in meta_of(path)


def test_a_dangling_reference_derives_nothing(tmp_path, monkeypatch):
    """The code resolves to no document. That is the reference check's
    finding to report, not this one's — deriving nothing keeps one fault to
    one line."""
    root = project(tmp_path, monkeypatch)
    path = practice(root, 1, source=["LIT-404"])
    assert "published" not in meta_of(path)


def test_a_target_without_the_field_derives_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    paper(root, 1, published=None)
    path = practice(root, 1, source=["LIT-001"])
    assert "published" not in meta_of(path)


# --- one hop, deliberately ---------------------------------------------------

def test_it_reads_written_frontmatter_not_the_target_s_own_derivation(
        tmp_path, monkeypatch):
    """One hop. The target's `published` here is itself derived, and this
    resolves to nothing rather than chaining — which is what makes a cycle
    impossible by construction rather than by detection."""
    extra = merged(FOLLOW, """
                     schemes:
                       LIT:
                         fields:
                           issued:
                             required: true
                         references:
                           origin:
                             scheme: LIT
                             required: false
                             many: false
                     """)
    root = project(tmp_path, monkeypatch, extra)
    write(root, "record/literature.d/LIT-009.md",
          "---\nstatus: Active\ntitle: 'Paper 9'\ndate: '2026-01-01'\n"
          "issued: '1999-01-01'\n---\n\n# LIT-009: Paper 9\n")
    paper(root, 1, published=None, extra="origin: LIT-009")
    path = practice(root, 1, source=["LIT-001"])
    assert "published" not in meta_of(path)


# --- still read-only ---------------------------------------------------------

def test_writing_it_down_is_still_a_finding(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch)
    paper(root, 1, "2020-10-01")
    path = practice(root, 1, source=["LIT-001"], extra="published: '2020-10-01'")
    out = findings(path)
    assert any("`published:` is written in frontmatter" in line for line in out)


def test_a_written_value_that_disagrees_is_the_motivating_defect(
        tmp_path, monkeypatch):
    """The anthology's eight stale dates, in one test: the practice says one
    thing, the paper it cites says another, and before this the record had no
    way to notice."""
    root = project(tmp_path, monkeypatch)
    paper(root, 1, "2017-01-01")
    path = practice(root, 1, source=["LIT-001"], extra="published: '2024-01-01'")
    assert any("`published:` is written in frontmatter" in line
               for line in findings(path))


# --- refused at load ---------------------------------------------------------

def test_from_must_name_a_reference_this_scheme_holds(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, FOLLOW.replace("from: source[0]", "from: nope"))
    with pytest.raises(ValueError, match="`nope` is not a reference"):
        config.current()


def test_a_plural_reference_needs_an_index(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, FOLLOW.replace("from: source[0]", "from: source"))
    with pytest.raises(ValueError, match="holds several"):
        config.current()


def test_a_scalar_reference_refuses_an_index(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, FOLLOW.replace("from: source[0]", "from: paper[0]"))
    with pytest.raises(ValueError, match="holds one"):
        config.current()


def test_the_template_is_checked_against_the_target_scheme(tmp_path, monkeypatch):
    """`{nonesuch}` is not a field LIT can hold, so this would resolve to
    nothing on every document — the quiet failure eager validation exists for."""
    root = project(tmp_path, monkeypatch, FOLLOW.replace("'{published}'", "'{nonesuch}'"))
    with pytest.raises(ValueError, match="nonesuch"):
        config.current()


def test_reading_the_same_name_is_not_self_derivation(tmp_path, monkeypatch):
    """`published` from `published` is a cycle within one document and a
    perfectly ordinary read across two. The rule has to know the difference."""
    root = project(tmp_path, monkeypatch)
    paper(root, 1, "2020-10-01")
    assert meta_of(practice(root, 1, source=["LIT-001"]))["published"] == "2020-10-01"


def test_a_lone_field_across_a_reference_is_not_a_rename(tmp_path, monkeypatch):
    """Within a document `"{x}"` copies a field under a second name and is
    refused. Across a reference it is the entire point."""
    root = project(tmp_path, monkeypatch)
    assert config.current().schemes["SOTA"].derived


def test_many_on_a_followed_derivation_names_the_derive_line(tmp_path, monkeypatch):
    """The refusal quotes the literal `derive =` value. `spec` also names the
    followed reference, which was written on its own line — quoting it here
    would print backticks inside a quoted string."""
    root = project(tmp_path, monkeypatch, merged(FOLLOW, {"schemes": {"SOTA": {"fields": {
                       "published": {"many": True}}}}}))
    with pytest.raises(ValueError) as caught:
        config.current()
    assert 'derive = "{published}"' in str(caught.value)


def test_from_alone_renders_nothing(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch,
                   """
                   schemes:
                     SOTA:
                       fields:
                         published:
                           from: source[0]
                   """)
    with pytest.raises(ValueError, match="renders nothing"):
        config.current()


def test_a_malformed_from_says_so(tmp_path, monkeypatch):
    root = project(tmp_path, monkeypatch, FOLLOW.replace("from: source[0]", "from: source[]"))
    with pytest.raises(ValueError, match="is not a reference"):
        config.current()
