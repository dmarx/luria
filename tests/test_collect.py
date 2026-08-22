"""The two collection shapes (ADR-028): append for narrative logs, changelog
for release logs. Pure-function tests — `collect` takes text and bodies."""
from luria.collect import collect

APPEND_VIEW = """# Log

Old entry.

<!-- luria-insert-here -->
"""

CHANGELOG_VIEW = """# Changelog

Assembled from fragments.

<!-- luria-insert-here -->

## 2026-07-01

- an old batch
"""


def test_append_lands_before_the_marker_oldest_first():
    out = collect(APPEND_VIEW, ["First.", "Second."])
    assert out.index("Old entry.") < out.index("First.") < out.index("Second.")
    assert out.index("Second.") < out.index("<!-- luria-insert-here -->")


def test_changelog_batch_lands_after_the_marker_newest_first():
    out = collect(CHANGELOG_VIEW, ["- older change", "- newer change"],
                  style="changelog", date="2026-08-04")
    marker = out.index("<!-- luria-insert-here -->")
    # The batch heading sits right after the marker, above the old batch…
    assert marker < out.index("## 2026-08-04") < out.index("## 2026-07-01")
    # …and within the batch the newest fragment reads first.
    assert out.index("- newer change") < out.index("- older change")


def test_changelog_batches_stack_newest_first():
    once = collect(CHANGELOG_VIEW, ["- first round"],
                   style="changelog", date="2026-08-04")
    twice = collect(once, ["- second round"],
                    style="changelog", date="2026-08-05")
    assert (twice.index("## 2026-08-05") < twice.index("## 2026-08-04")
            < twice.index("## 2026-07-01"))


def test_a_stub_only_batch_emits_no_date_heading():
    """The failure this prevents was documented as a caveat under scriv: a
    collection round of only no-user-facing-changes stubs left a bare date
    heading behind, which somebody then had to revert by hand."""
    out = collect(CHANGELOG_VIEW, ["<!-- no user-facing changes -->"],
                  style="changelog", date="2026-08-04")
    assert out == CHANGELOG_VIEW


def test_stubs_are_dropped_from_a_mixed_batch():
    out = collect(CHANGELOG_VIEW, ["- real change", "<!-- stub -->"],
                  style="changelog", date="2026-08-04")
    assert "- real change" in out
    assert "stub" not in out


def test_changelog_style_with_marker_at_eof_keeps_a_final_newline():
    view = "# Changelog\n\n<!-- luria-insert-here -->\n"
    out = collect(view, ["- only change"], style="changelog", date="2026-08-04")
    assert out.endswith("- only change\n")
    assert "<!-- luria-insert-here -->\n\n## 2026-08-04" in out
