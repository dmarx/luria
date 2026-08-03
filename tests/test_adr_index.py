"""Tests for scripts/ci/build_adr_index.py — link rebasing across outputs.

The index renders the same ADR row into two places a directory apart:
`docs/decisions/README.md` and `docs/decisions/tags/<tag>.md`. Every relative
link in a row has to be rewritten for where it lands, or it 404s in one of them
— which is exactly what happened to four `Superseded — by [ADR-NNN](…)` notes
before this existed, and what made summaries link-free until ADR-187.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

from luria import adr_index as builder  # noqa: E402

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
    """The property the rebasing exists for, checked against the real corpus."""
    broken = []
    for path, text in builder.outputs().items():
        for target in builder.RELATIVE_LINK_RE.findall(text):
            file = target.split("#")[0]
            if file and not (path.parent / file).resolve().exists():
                broken.append(f"{path.name} -> {target}")
    assert broken == []
