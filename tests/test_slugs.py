# tests/test_slugs.py
"""The anchor a heading answers to, computed the way the publisher does.

Owning a fourth copy of somebody else's algorithm is a thing to do carefully
or not at all (DP-4). Luria has to, because its generated contents lists link
headings now and a heading's id is assigned by `rehype-slug` on the site and
by the same `github-slugger` on GitHub.

So these tests are not about a specification I chose. Every case here was
taken from what Quartz actually published for this record, and two of them
are cases my first implementation got wrong (ADR-tmp29lk4).
"""

# inactive-ok-file: ADR-tmp29lk4 — Proposed. Every mention names it as
# the decision this file implements or is written against; the citation
# is to the reasoning, not a claim the decision is settled.

from __future__ import annotations

from luria import slugs


def test_the_ordinary_case():
    assert (slugs.slug("Three lint passes compile into one contract per scheme")
            == "three-lint-passes-compile-into-one-contract-per-scheme")


def test_punctuation_goes_and_the_word_characters_stay():
    assert (slugs.slug("The config migration's two silent failures")
            == "the-config-migrations-two-silent-failures")


def test_an_underscore_survives():
    """`\\w` includes it, so `github-slugger` keeps it. My first version
    stripped `_` as a markdown emphasis marker and produced `failon`, which
    is a link to nothing."""
    assert (slugs.slug("A mute dial, because `fail_on` only changes it")
            == "a-mute-dial-because-fail_on-only-changes-it")
    assert slugs.slug("rename_scheme renamed nothing") == "rename_scheme-renamed-nothing"


def test_removed_punctuation_leaves_its_spaces_behind():
    """The order is remove-then-replace, and each space becomes one hyphen
    rather than each RUN of them. An em-dash between two spaces therefore
    leaves a double hyphen — which my first version collapsed."""
    assert (slugs.slug("Development log — September 2026")
            == "development-log--september-2026")


def test_repeats_are_numbered_from_the_second():
    s = slugs.Slugger()
    assert [s.slug("Notes"), s.slug("Notes"), s.slug("Notes")] == [
        "notes", "notes-1", "notes-2"]


def test_a_repeat_that_collides_with_a_numbered_one_moves_on():
    """`github-slugger` keeps incrementing until the result is unused, so a
    document containing "Notes", "Notes" and "Notes 1" cannot end up with two
    headings answering to `notes-1`."""
    s = slugs.Slugger()
    got = [s.slug("Notes"), s.slug("Notes 1"), s.slug("Notes")]
    assert len(set(got)) == 3, got


def test_headings_come_out_in_document_order():
    assert slugs.headings("# One\n\ntext\n\n## Two\n\n### Three\n") == [
        "One", "Two", "Three"]


def test_a_heading_inside_a_fence_is_not_one():
    """It would consume a slug and shift the suffix of every heading after
    it, which is a link to the wrong entry rather than to none."""
    text = ("# Real\n\n```bash\n# not a heading\n```\n\n"
            "~~~\n## also not\n~~~\n\n## Also real\n")
    assert slugs.headings(text) == ["Real", "Also real"]


def test_a_longer_fence_closes_a_shorter_one_and_not_the_reverse():
    text = "````\n```\n# hidden\n```\n````\n\n# visible\n"
    assert slugs.headings(text) == ["visible"]


def test_anchors_for_maps_each_heading_to_its_own_slug():
    got = slugs.anchors_for("# A\n\n## Notes\n\n## Notes\n")
    assert got == {"A": "a", "Notes": "notes-1"}, got
