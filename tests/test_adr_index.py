"""Tests for `luria index` — link rebasing across outputs, and the two renders.

The index renders the same ADR row into two places a directory apart:
`docs/decisions/README.md` and `docs/decisions/tags/<tag>.md`. Every relative
link in a row has to be rewritten for where it lands, or it 404s in one of them
— which is exactly what happened to four `Superseded — by [ADR-NNN](…)` notes
before this existed, and what made summaries link-free until ADR-005.

The second half covers `render = "document"` (ADR-012), where the same trap
arrives from a different direction: the fragments live one directory *below*
the page they assemble into.
"""
import sys
from pathlib import Path

# unresolved-ok-file: ADR-053, ADR-404 — fixture codes, deliberately not real
REPO = Path(__file__).resolve().parents[1]

from luria import adr_index as builder  # noqa: E402
from luria import doc_refs  # noqa: E402
from luria.config import Scheme  # noqa: E402

rebase = builder.rebase_links


def test_relative_targets_are_rebased():
    assert rebase("see [ADR-053](adr-053-x.md)", "../") == \
        "see [ADR-053](../adr-053-x.md)"
    assert rebase("see [dp](../design-principles.md#13-a)", "../") == \
        "see [dp](../../design-principles.md#13-a)"


def test_absolute_and_anchor_targets_are_left_alone():
    """A URL, a root-relative path and a same-page anchor mean the same thing
    from any directory — rewriting them would break them."""
    for target in ("https://github.com/dmarx/strata-g/issues/551",
                   "mailto:x@y.z", "/docs/x.md", "#a-heading"):
        text = f"see [x]({target})"
        assert rebase(text, "../") == text


def test_no_prefix_is_a_no_op():
    """README.md renders from the ADRs' own directory, so its rows are the
    unmodified text — that's what kept the ADR-004 migration byte-identical."""
    text = "see [ADR-053](adr-053-x.md) and [#1](https://example.com/1)"
    assert rebase(text, "") == text


def test_row_rebases_summary_and_status_together(tmp_path, monkeypatch):
    """The row's own link was always rebased; the summary and the status note
    are prose rendered into the same row and need the same treatment. Four
    supersession links 404'd on the tag pages until this held."""
    from luria import config
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()
    adr_dir = config.current().schemes["ADR"].dir
    adr_dir.mkdir(parents=True)
    (adr_dir / "ADR-001.md").write_text(
        "---\nstatus: 'Superseded — by [ADR-002](ADR-002.md)'\n"
        "tags:\n- record\n"
        "summary: 'refines [ADR-002](ADR-002.md)'\n---\n\n# ADR-001: Old\n")

    adr = builder.load_adrs()[0]
    assert "](ADR-002.md)" in adr.row()            # from the index
    row = adr.row("../")                            # from tags/, one deeper
    assert "](../ADR-002.md)" in row
    assert row.count("](ADR-002.md)") == 0          # summary AND status rebased
    config.reset()


def test_every_generated_relative_link_resolves():
    """The property the rebasing exists for, checked against the real corpus.
    Covers every render — scheme views and journal books both go through
    `outputs()`.

    Code spans are skipped for the same reason the hyperlink lint skips them:
    a link inside backticks is a *quotation* of a link, and the devlog quotes
    several broken ones on purpose."""
    broken = []
    for path, text in builder.outputs().items():
        quoted = doc_refs.code_spans(text)
        for m in builder.RELATIVE_LINK_RE.finditer(text):
            if doc_refs.in_html_block(m.start(), quoted):
                continue
            file = m.group(1).split("#")[0]
            if file and not (path.parent / file).resolve().exists():
                broken.append(f"{path.name} -> {m.group(1)}")
    assert broken == []


# ── render = "document" (ADR-012) ────────────────────────────────────────


def principle(root: Path, number: int, title: str, body: str = "Body.",
              **front) -> Path:
    path = root / "docs" / "principles" / f"DP-{number:03d}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["status: Active", f"title: {title!r}", "tags:", "- record"]
    lines += [f"{k}: {v}" for k, v in front.items()]
    path.write_text("---\n" + "\n".join(lines) + "\n---\n\n"
                    f"# DP-{number:03d}: {title}\n\n{body}\n")
    return path


DP_SCHEME_ARGS = dict(active="Active", render="document")


def dp_scheme(root: Path) -> Scheme:
    return Scheme("DP", root / "docs" / "principles",
                  output=root / "docs" / "design-principles.md",
                  **DP_SCHEME_ARGS)


def render(root: Path) -> str:
    scheme = dp_scheme(root)
    return builder.render_document(scheme, builder.load_scheme(scheme))


def test_document_demotes_the_heading_and_renumbers(project):
    principle(project, 3, "Fire before trusting")
    out = render(project)
    assert "## 3. Fire before trusting" in out
    assert "# DP-003" not in out


def test_document_emits_a_stable_anchor(project):
    """Keyed to the number, not the wording — a principle is a living document
    and its heading moves (ADR-012)."""
    principle(project, 3, "Fire before trusting")
    assert '<a name="dp-3"></a>' in render(project)


def test_document_strips_the_frontmatter(project):
    principle(project, 1, "A value", **{"version": 2})
    out = render(project)
    assert "status: Active" not in out and "tags:" not in out


def test_metadata_line_carries_version_and_origin(project):
    principle(project, 1, "A value", **{"version": 2, "origin": "'An incident.'"})
    assert "*v2 · origin: An incident*" in render(project)


def test_a_retired_principle_says_so(project):
    """`Active` is the silent default; anything else is stated, because a
    principle nobody believes any more is exactly what a reader needs told."""
    path = principle(project, 1, "A value")
    path.write_text(path.read_text().replace("status: Active", "status: Rejected"))
    assert "**Rejected**" in render(project)


def test_influenced_by_renders_as_a_followable_backlink(project):
    """Relative to where the text *renders* — `docs/`, not the fragment's own
    directory — which is the trap that caught two links in the first eight.
    Under the record layout the decision sources are a tree away (ADR-021),
    and the relpath is derived so this asserts the rule, not the location."""
    import os
    from luria.config import current
    from tests import _scheme
    _scheme.decision(project, 4, "Active")
    principle(project, 1, "A value", influenced_by="[ADR-004]")
    target = os.path.relpath(current().schemes["ADR"].dir / "ADR-004.md",
                             current().design_principles.parent)
    assert f"[ADR-004]({target})" in render(project)


def test_an_unresolvable_backlink_stays_a_bare_code(project):
    """DP-1: say what can be said, rather than linking to nothing."""
    principle(project, 1, "A value", influenced_by="[ADR-404]")
    out = render(project)
    assert "shaped by ADR-404" in out and "](" not in out.split("shaped by")[1]


def test_outputs_covers_every_scheme(project, monkeypatch):
    """One `luria index`, every scheme — so the staleness check picks up a new
    scheme the moment it is configured, with no second command to remember."""
    from tests import _scheme
    _scheme.decision(project, 1, "Active")
    principle(project, 1, "A value")
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "docs/decisions"\n'
        '[luria.schemes.DP]\ndir = "docs/principles"\n'
        'render = "document"\noutput = "docs/design-principles.md"\n')
    from luria import config
    config.reset()

    out = builder.outputs()
    assert project / "docs" / "design-principles.md" in out
    assert project / "docs" / "decisions" / "README.md" in out


# ── Filenames and titles (ADR-013) ───────────────────────────────────────


def test_filename_is_the_code(project):
    scheme = builder.current().schemes["ADR"]
    assert scheme.filename(13) == "ADR-013.md"
    assert scheme.filename("4") == "ADR-004.md"


def test_a_legacy_slug_filename_is_still_read(project):
    """Most projects arrive with `adr-010-some-title.md`, and refusing to read
    them would make adoption a rename-everything-first proposition. Luria
    writes the short form and reads both."""
    from tests import _scheme
    path = _scheme.decision(project, 10, "Active")
    path.rename(path.parent / "adr-010-some-old-title.md")
    assert set(builder.current().schemes["ADR"].documents()) == {10}


def test_a_readme_is_not_a_document(project):
    """`README.md`, `README.stub`, `_template.md` and `tags.yaml` share the
    directory with the sources — the scheme's own filename rule is what tells
    them apart, and it is the only such rule in the package."""
    from tests import _scheme
    _scheme.decision(project, 1, "Active")
    decisions = project / "docs" / "decisions"
    (decisions / "README.md").write_text("# Index\n")
    (decisions / "_template.md").write_text("---\nstatus: Proposed\n---\n")
    assert set(builder.current().schemes["ADR"].documents()) == {1}


def test_title_frontmatter_wins_over_the_heading(project):
    from tests import _scheme
    path = _scheme.decision(project, 1, "Active", title="The real title")
    path.write_text(path.read_text().replace(
        "# ADR-001: The real title", "# ADR-001: A stale heading"))
    assert builder.load_adrs()[0].title == "The real title"


def test_the_heading_is_the_fallback(project):
    """A project mid-adoption has decisions with no `title:` yet, and a blank
    index cell would be worse than a heading-derived one."""
    from tests import _scheme
    path = _scheme.decision(project, 1, "Active", title="From the heading")
    path.write_text(path.read_text().replace(
        "title: 'From the heading'\n", ""))
    assert builder.load_adrs()[0].title == "From the heading"


# ── The read/write boundary (ADR-021) ────────────────────────────────────


def test_prefix_for_collocated_scheme_is_empty():
    """Unset `output` is the old layout — view beside sources — and its
    rendering must stay byte-identical, or every pre-record project's index
    goes stale on upgrade."""
    s = Scheme("ADR", REPO / "x")
    assert builder.prefix_for(s, s.view) == ""


def test_split_scheme_rows_link_into_the_source_tree(project, monkeypatch):
    """An index rendered away from its sources reaches back with a relative
    prefix — the row's own link, the summary's links and the status note all
    take the same one."""
    from luria import config
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        'output = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, "Active", summary="see [ADR-002](ADR-002.md)")
    _scheme.decision(project, 2, "Active")

    rendered = builder.outputs()
    index = rendered[project / "docs" / "decisions" / "README.md"]
    assert "[ADR-001](../../record/decisions.d/ADR-001.md)" in index
    assert "see [ADR-002](../../record/decisions.d/ADR-002.md)" in index
    tag = rendered[project / "docs" / "decisions" / "tags" / "record.md"]
    assert "[ADR-001](../../../record/decisions.d/ADR-001.md)" in tag


def test_stub_lives_with_the_sources_and_renders_in_the_view(project):
    """The stub is authored, so it sits on the write side; the view directory
    holds only what the generator wrote (ADR-021)."""
    from luria import config
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        'output = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, "Active")
    stub = project / "record" / "decisions.d" / "README.stub"
    stub.write_text("# Mine\n\nProse.\n\n{categories}\n\n{table}\n")

    index = builder.outputs()[project / "docs" / "decisions" / "README.md"]
    assert index.startswith("# Mine")


def test_orphans_reports_strays_in_every_view_dir(project):
    from luria import config
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "record/decisions.d"\n'
        'output = "docs/decisions"\n'
        '[luria.journals.devlog]\ndir = "record/devlog.d"\n'
        'output = "docs/devlog"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, "Active")
    rendered = builder.outputs()
    for path, text in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert builder.orphans(rendered) == []

    stray = project / "docs" / "decisions" / "notes.md"
    stray.write_text("# Handwritten\n")
    assert builder.orphans(rendered) == [stray]


def test_a_collocated_view_dir_is_not_policed(project):
    """With no separate `output` the scheme's directory holds the sources —
    calling every ADR an orphan would fail the entire pre-record layout."""
    from luria import config
    (project / "luria.toml").write_text(
        '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
        '[luria.schemes.ADR]\ndir = "docs/decisions"\n')
    config.reset()
    from tests import _scheme
    _scheme.decision(project, 1, "Active")
    rendered = builder.outputs()
    for path, text in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    # The ADR source sits in the same directory as the rendered index, and it
    # is not an orphan — only the tag dir is policed here.
    assert builder.orphans(rendered) == []
