"""Does a document's identifier name the document's subject? (#166)

The failure this exists for is not a broken link — it is a *working* link to
the wrong paper. 53 of 139 arXiv identifiers in `anthology-of-the-sota`
resolved to real papers on unrelated subjects and stayed green for two years,
because every check in the lint asked whether a reference pointed somewhere
and none asked whether it pointed where it said.

Nothing here opens a socket: the resolved titles come from the committed
lockfile, exactly as the lint reads them.
"""
import json

from luria import config, lint, sources

SOURCE_TOML = (
    '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
    '[luria.remotes.ARXIV]\n'
    'uid = "(\\\\d{4})[.:](\\\\d{4,5})"\n'
    'url = "https://arxiv.org/abs/{1}.{2}"\n'
    'uris.title = "https://export.example/api?id={1}.{2}"\n'
    'title_re = "<title>(.*?)</title>"\n'
    '[luria.schemes.LIT]\n'
    'dir = "record/literature.d"\n'
    'render = "index"\n'
    'output = "docs/literature"\n'
)


def _project(project, extra: str = "") -> None:
    (project / "record" / "literature.d").mkdir(parents=True, exist_ok=True)
    (project / "docs" / "literature").mkdir(parents=True, exist_ok=True)
    (project / "luria.toml").write_text(SOURCE_TOML + extra)
    config.reset()


def _note(project, number: int, title: str, arxiv: str,
          directive: str = "") -> None:
    head = f"status: Active\ntitle: '{title}'\n"
    if directive:
        head += f"# {directive}\n"
    head += f"arxiv: '{arxiv}'\n"
    (project / "record" / "literature.d" / f"LIT-{number:03d}.md").write_text(
        f"---\n{head}---\n\n# LIT-{number:03d}: {title}\n\nBody.\n")


def _resolved(project, entries: dict[str, str]) -> None:
    (project / "remotes.lock.json").write_text(json.dumps(
        {"titles": {k: {"title": v} for k, v in entries.items()}}))


def test_an_identifier_naming_a_different_paper_is_reported(project):
    """The whole point. `2305.10755` is a real arXiv paper and a valid
    identifier; it is simply not the PaLM 2 technical report, and no check
    that stops at "does this resolve" can say so."""
    _project(project)
    _note(project, 99, "PaLM 2 Technical Report", "2305.10755")
    _resolved(project, {
        "ARXIV/2305.10755": "Measurement-Device-Independent Quantum Secret Sharing"})
    flagged, _ = sources.mismatch_lines()
    assert len(flagged) == 1
    assert "Quantum Secret Sharing" in flagged[0]
    assert "PaLM 2 Technical Report" in flagged[0]


def test_an_agreeing_identifier_is_silent(project):
    _project(project)
    _note(project, 1, "Adam: A Method for Stochastic Optimization", "1412.6980")
    _resolved(project, {
        "ARXIV/1412.6980": "Adam: A Method for Stochastic Optimization"})
    assert sources.mismatch_lines() == ([], [])


def test_wrapping_case_and_punctuation_do_not_count_as_disagreement(project):
    """A recorded title keeps its own capitalisation and line breaks. Only the
    words decide, or the check would fire on every document that was typed by
    a human rather than pasted."""
    _project(project)
    _note(project, 2, "GQA:  Training Generalized  Multi-Query Transformer models",
          "2305.13245")
    _resolved(project, {
        "ARXIV/2305.13245":
            "GQA: Training Generalized Multi-Query Transformer Models"})
    assert sources.mismatch_lines() == ([], [])


def test_a_truncated_title_is_a_disagreement(project):
    """The tempting case to forgive, and it is not forgiven. Dropping a
    subtitle is usually harmless and sometimes not: one record read "Neural
    Networks are Surprisingly Modular" for a paper about *Pruned* networks,
    which is a weaker claim wearing a stronger title. The directive is how a
    deliberate trim is recorded, so the judgement lands on a person."""
    _project(project)
    _note(project, 19, "The Lottery Ticket Hypothesis", "1803.03635")
    _resolved(project, {
        "ARXIV/1803.03635":
            "The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks"})
    flagged, _ = sources.mismatch_lines()
    assert len(flagged) == 1


def test_a_source_ok_directive_acknowledges_it(project):
    """A nickname the project prefers is legitimate and common — 22 of the 53
    were this class. Without an acknowledgement the check is noisy enough to
    be switched off."""
    _project(project)
    _note(project, 12, "AdamW: Decoupled Weight Decay Regularization",
          "1711.05101",
          directive="source-ok: 1711.05101 — the optimizer's name, kept on purpose")
    _resolved(project, {"ARXIV/1711.05101": "Decoupled Weight Decay Regularization"})
    flagged, stale = sources.mismatch_lines()
    assert flagged == [] and stale == []


def test_a_source_ok_that_excuses_nothing_is_reported(project):
    """Same bargain every other directive strikes: an acknowledgement cannot
    outlive what it excused, or the record fills with permissions nobody can
    audit."""
    _project(project)
    _note(project, 1, "Adam: A Method for Stochastic Optimization", "1412.6980",
          directive="source-ok: 1412.6980 — this one agrees, so it excuses nothing")
    _resolved(project, {
        "ARXIV/1412.6980": "Adam: A Method for Stochastic Optimization"})
    flagged, stale = sources.mismatch_lines()
    assert flagged == []
    assert len(stale) == 1 and "matches no identifier" in stale[0]


def test_an_unresolved_identifier_is_not_a_finding(project):
    """A project that has never run `--resolve` must not see every document
    turn into a finding — that teaches people to run the command to silence
    the lint rather than to read what it says."""
    _project(project)
    _note(project, 1, "Adam: A Method for Stochastic Optimization", "1412.6980")
    _resolved(project, {})
    assert sources.mismatch_lines() == ([], [])


def test_the_lint_carries_the_class(project):
    _project(project)
    _note(project, 99, "PaLM 2 Technical Report", "2305.10755")
    _resolved(project, {"ARXIV/2305.10755": "Something Else Entirely"})
    assert "source-mismatch" in {name for name, _, _ in lint.status_sections()}


def test_the_title_url_indexes_the_uid_capture_groups(project):
    """`uris.title` renders over the same vocabulary as `url`, so a remote
    whose metadata API wants the identifier restructured needs one line, not a
    second subsystem."""
    _project(project)
    remote = config.current().remotes["ARXIV"]
    assert sources._title_url(remote, "2502.11089") == (
        "https://export.example/api?id=2502.11089")


def test_a_remote_with_no_title_uri_is_skipped(project):
    """Most remotes are records, not metadata APIs. Declaring nothing means
    the check has no opinion, rather than an opinion it cannot support."""
    _project(project, extra='[luria.remotes.TICKET]\nuid = "[A-Z]+-\\\\d+"\n'
                            'url = "https://tickets.example/{uid}"\n')
    remote = config.current().remotes["TICKET"]
    assert sources._title_url(remote, "OPS-1") == ""
