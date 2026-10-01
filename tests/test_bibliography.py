# tests/test_bibliography.py
"""Reference-list detection by shape, not by heading.

A record's bibliography line — `Kingma et al. (2014), LIT-001 — ARXIV-…` —
cites a code without saying anything about it, so a check that asks prose to
explain a relation must not count it. Which heading a list sits under is one
record's convention; what an entry looks like is not, so the detector reads
morphology: an author/year lead, identifiers, title and venue, and how little
ordinary prose is left once those are gone. Most positives below are real
lines from the anthology, which is where the need was measured.
"""

from __future__ import annotations

import pytest

from luria import bibliography

ENTRIES = [
    # The anthology's own shapes.
    "Kingma et al. (2014), [LIT-001](../literature.d/LIT-001.md) — "
    "[ARXIV-1412.6980](https://arxiv.org/abs/1412.6980).",
    "Chen et al. (2023) — [ARXIV-2302.06675](https://arxiv.org/abs/2302.06675)",
    "Evci, Ioannou, Keskin and Dauphin (2020), [LIT-039](../literature.d/LIT-039.md).",
    "Kimi Team, Moonshot AI (2025) — [ARXIV-2510.26692](https://arxiv.org/abs/2510.26692)",
    "Chen et al. (2024), [LIT-464](../literature.d/LIT-464.md) — read as "
    "[NOTE-214](../notes.d/NOTE-214.md).",
    "Yeh, Hsieh, Suggala, Inouye and Ravikumar (2019), "
    "[LIT-725](../literature.d/LIT-725.md) — NeurIPS 2019, §2–3.",
    "Read from [LIT-378](../literature.d/LIT-378.md) — "
    "[ARXIV-2305.14314](https://arxiv.org/abs/2305.14314).",
    "**Dao et al. (2022)** — `LIT-074`, FlashAttention.",
    # An affiliation after `et al.`, and a corporate author in lower case.
    "Shi et al., Meta (2023) — [ARXIV-2309.06497](https://arxiv.org/abs/2309.06497)",
    "The Movie Gen team (2024), [LIT-626](../literature.d/LIT-626.md), Table 8b.",
    "Liu, Gong and Liu, University of Texas at Austin (2022) — "
    "[ARXIV-2209.03003](https://arxiv.org/abs/2209.03003)",
    "Liang, Yu, Luo, Iyer and colleagues (2024), [LIT-483](LIT-483.md) §3.5 "
    "and §4 — read as [NOTE-232](NOTE-232.md).",
    # Classic bibliography styles, which carry an unquoted title.
    "[1] A. Vaswani, N. Shazeer, N. Parmar, et al. Attention is all you need. "
    "In Advances in Neural Information Processing Systems, 2017.",
    "Kingma, D. P., & Ba, J. (2014). Adam: A method for stochastic "
    "optimization. arXiv preprint arXiv:1412.6980.",
    "- He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning "
    "for image recognition. In CVPR. https://doi.org/10.1109/CVPR.2016.90",
    "- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)",
]

PROSE = [
    "Kingma et al. (2014) showed that the bias correction matters most when "
    "the second-moment decay is close to one.",
    "LIT-541 makes the case. Neural networks are *singular* statistical "
    "models, so the usual curvature measures do not apply.",
    "As Kingma et al. (2014), [LIT-001](LIT-001.md), argue, the second moment "
    "is what makes the step size scale-free.",
    # An annotated entry explains its paper: the annotation is the prose.
    "McCandlish et al. (2018), [LIT-017](../literature.d/LIT-017.md) — "
    "[ARXIV-1812.06162](https://arxiv.org/abs/1812.06162). Where the critical "
    "batch size Kaplan fits an exponent for is defined, and given a "
    "measurement procedure; model size enters only through the loss.",
    # Telegraphic annotations: few connectives, but plainly prose.
    "He et al. (2019), [LIT-590](LIT-590.md) — [ARXIV-1911.05722](https://arxiv.org/abs/1911.05722), "
    "§3.3, and Chen et al. (2020), [LIT-591](LIT-591.md), §2.2. Two groups, three "
    "months apart, the same bug and two different fixes.",
    "Zhu et al. (2024), [LIT-205](LIT-205.md), and Finke et al. (2025), "
    "[LIT-485](LIT-485.md) — read as [NOTE-234](NOTE-234.md). Two groups, two "
    "corpora, two instruments, no citation in either direction.",
    # An annotation as short as a clause is still one.
    "Ba et al. (2016), [LIT-005](LIT-005.md) — "
    "[ARXIV-1607.06450](https://arxiv.org/abs/1607.06450), where the bias is introduced.",
    "- Porian et al. (2024) measured the exponent at 0.497 over 5M–901M, "
    "within 15% of Chinchilla, which is why this practice cites it.",
    "Adam is what to reach for absent a reason to do otherwise, and it is "
    "[LIT-001](../literature.d/LIT-001.md) that the record leans on for it.",
]


@pytest.mark.parametrize("text", ENTRIES)
def test_a_reference_entry_is_one(text):
    assert bibliography.is_entry(text), text


@pytest.mark.parametrize("text", PROSE)
def test_prose_that_cites_is_not_an_entry(text):
    assert not bibliography.is_entry(text), text


def test_regions_are_offsets_of_the_entries_in_a_body():
    body = ("## Source\n\n"
            "Kingma et al. (2014), LIT-001 — ARXIV-1412.6980.\n\n"
            "## The claim\n\n"
            "Adam is the default, and LIT-001 says why: the second moment "
            "makes the step size invariant to the gradient's scale.\n")
    spans = bibliography.regions(body)
    covered = [body[a:b] for a, b in spans]
    assert covered == ["Kingma et al. (2014), LIT-001 — ARXIV-1412.6980."]


def test_each_list_item_is_judged_on_its_own():
    body = ("- He, K., & Sun, J. (2016). Deep residual learning. In CVPR.\n"
            "- He et al. (2016) show the identity shortcut is what lets the "
            "deeper network train at all, which is the whole claim here.\n")
    spans = bibliography.regions(body)
    assert len(spans) == 1 and body[spans[0][0]:].startswith("- He, K.")


def test_no_heading_is_consulted():
    """A reference list under any heading — or none — is found; a prose
    paragraph under a heading called Source is not one."""
    body = ("## References\n\nThe paper we lean on argues that warm-up exists "
            "because Adam's early variance estimate is poor, LIT-020.\n\n"
            "## Notes\n\nZhang et al. (2019), LIT-020 — ARXIV-1908.03265.\n")
    covered = [body[a:b] for a, b in bibliography.regions(body)]
    assert covered == ["Zhang et al. (2019), LIT-020 — ARXIV-1908.03265."]


def test_fences_comments_headings_and_tables_are_never_entries():
    body = ("```\nKingma et al. (2014), LIT-001 — ARXIV-1412.6980.\n```\n\n"
            "<!-- Kingma et al. (2014), LIT-001 -->\n\n"
            "# Kingma et al. (2014), LIT-001\n\n"
            "| Kingma et al. (2014) | LIT-001 |\n| --- | --- |\n")
    assert bibliography.regions(body) == []
