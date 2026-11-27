# tests/test_site_social_cards.py
"""`site.social_cards` switches Quartz's per-page social-card emitter.

The first timed build of luria's own site (Pages run 368, 2026-11-27) put
the cost on one emitter: page HTML was done at 18.5 s, and `CustomOgImages`
ran on to 73.5 s, making 540 images, 8.66 MB of a 28.54 MB site. The key
defaults on, so no record's site changes unless it opts out.
"""
import pytest
import yaml

from _config import merged
from luria import config, site
from luria.config import current


def _og_image_entry(out) -> dict:
    staged = yaml.safe_load((out / "quartz.config.yaml").read_text())
    entries = [p for p in staged["plugins"]
               if p.get("source") == "@quartz-community/og-image"]
    assert len(entries) == 1, "the og-image plugin is written exactly once"
    return entries[0]


def _set(project, value) -> None:
    path = project / "luria.yaml"
    path.write_text(merged(path.read_text(), {"site": {"social_cards": value}}))
    config.reset()


def test_social_cards_default_on(project, tmp_path_factory):
    config.reset()
    assert current().site.social_cards is True
    out = tmp_path_factory.mktemp("site")
    site.stage(out, current())
    assert _og_image_entry(out)["enabled"] is True


def test_a_record_can_turn_social_cards_off(project, tmp_path_factory):
    _set(project, False)
    assert current().site.social_cards is False
    out = tmp_path_factory.mktemp("site")
    site.stage(out, current())
    assert _og_image_entry(out)["enabled"] is False


@pytest.mark.parametrize("bad", ["no", 0, "false"])
def test_a_non_boolean_is_refused_by_name(project, bad):
    """A string "false" would otherwise read as true. Say so, rather than
    publish the cards the record asked to drop (DP-001)."""
    _set(project, bad)
    with pytest.raises(ValueError, match="site.social_cards"):
        current()
