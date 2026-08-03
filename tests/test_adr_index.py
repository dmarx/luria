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

REPO = Path(__file__).resolve().parents[1]

from luria import adr_index as builder  # noqa: E402
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
    unmodified text — that's what kept the ADR-158 migration byte-identical."""
    text = "see [ADR-053](adr-053-x.md) and [#1](https://example.com/1)"
    assert rebase(text, "") == text


def test_row_rebases_summary_and_status_together(tmp_path, monkeypatch):
    """The row's own link was always rebased; the summary and the status note
    are prose rendered into the same row and need the same treatment. Four
    supersession links 404'd on the tag pages until this held."""
    from luria import config
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "docs" / "decisions" / "adr-001-old.md").write_text(
        "---\nstatus: 'Superseded — by [ADR-002](adr-002-new.md)'\n"
        "tags:\n- record\n"
        "summary: 'refines [ADR-002](adr-002-new.md)'\n---\n\n# ADR-001: Old\n")
    monkeypatch.setenv("LURIA_ROOT", str(tmp_path))
    config.reset()

    adr = builder.load_adrs()[0]
    assert "](adr-002-new.md)" in adr.row()        # from the index
    row = adr.row("../")                            # from tags/, one deeper
    assert "](../adr-002-new.md)" in row
    assert row.count("](adr-002-new.md)") == 0      # summary AND status rebased
    config.reset()


def test_every_generated_relative_link_resolves():
    """The property the rebasing exists for, checked against the real corpus.
    Covers both renders — every scheme's view goes through `outputs()`."""
    broken = []
    for path, text in builder.outputs().items():
        for target in builder.RELATIVE_LINK_RE.findall(text):
            file = target.split("#")[0]
            if file and not (path.parent / file).resolve().exists():
                broken.append(f"{path.name} -> {target}")
    assert broken == []


# ── render = "document" (ADR-012) ────────────────────────────────────────


def principle(root: Path, number: int, title: str, body: str = "Body.",
              **front) -> Path:
    path = root / "docs" / "principles" / f"dp-{number:03d}-fixture.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["status: Active", "tags:", "- record"]
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
    """Relative to where the text *renders* — `docs/`, one level above the
    fragment — which is the trap that caught two links in the first eight."""
    from tests import _scheme
    _scheme.decision(project, 4, "Active")
    principle(project, 1, "A value", influenced_by="[ADR-004]")
    assert "[ADR-004](decisions/adr-004-fixture.md)" in render(project)


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
