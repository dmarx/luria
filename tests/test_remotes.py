"""Foreign references: `SG-ADR-032` is another project's decision (ADR-015).

The risky part is not the URL construction — it is the *precedence*. A composed
code has a local-looking code inside it, and four different scanners can each
read the tail out of the middle and quietly say something about the wrong
project: the reference finder, the fixer, the citation scan, and the annotation
validator. One test per mouth.
"""
import json
import sys
from pathlib import Path

from _scheme import decision

from luria import config, doc_refs, ref_status, remotes

# unresolved-ok-file: ADR-032 ADR-999 SG-ADR-999 — fixture codes, not claims about this repo
REPO = Path(__file__).resolve().parents[1]

REMOTE_TOML = (
    '[luria]\nissue_url = "https://example.test/issues/{n}"\n'
    '[luria.remotes.SG]\nname = "strata-g"\nrepo = "o/r"\n'
)


def with_remote(project, extra: str = "") -> Path:
    (project / "luria.toml").write_text(REMOTE_TOML + extra)
    config.reset()
    return project


def lockfile(project, entries: dict[str, str]) -> None:
    (project / "remotes.lock.json").write_text(
        json.dumps({"remotes": {"SG": entries}}))


# ── Construction ─────────────────────────────────────────────────────────


def test_code_only_convention_is_the_default(project):
    """Right whenever the remote follows ADR-013, and it is Luria's own
    convention — so a remote that uses it needs one config line."""
    with_remote(project)
    assert remotes.resolve("SG", "ADR-32") == (
        "https://github.com/o/r/blob/main/docs/decisions/ADR-032.md")


def test_a_discovered_filename_wins(project):
    """The only rung that can resolve a slug-named remote — no template can
    turn a number into `adr-032-changelog-ci-collection.md`."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-changelog-ci-collection.md"})
    assert remotes.resolve("SG", "ADR-032").endswith(
        "/adr-032-changelog-ci-collection.md")


def test_discovery_is_authoritative_once_done(project):
    """A code absent from a lockfile that was read *from the remote* names no
    document there. Guessing a filename anyway is how `DP-004` produced a
    confident link to a file that has never existed."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    assert remotes.resolve("SG", "ADR-999") == ""


def test_no_lockfile_means_fall_back_rather_than_refuse(project):
    """Never refreshed is not the same claim as "not there" — a project that
    has not run discovery still gets working links for a conventional remote."""
    with_remote(project)
    assert remotes.resolve("SG", "ADR-999").endswith("/ADR-999.md")


def test_an_explicit_template_overrides_everything(project):
    with_remote(project, 'url = "https://x.test/{code}"\n')
    lockfile(project, {"ADR-032": "ignored.md"})
    assert remotes.resolve("SG", "ADR-032") == "https://x.test/ADR-032"


def test_an_unregistered_prefix_is_not_a_namespace(project):
    """`MY-ADR-004` in prose must stay prose. The pattern is built from the
    registry precisely so unregistered text is never claimed."""
    with_remote(project)
    assert remotes.resolve("MY", "ADR-004") == ""


# ── Precedence: four scanners, one composed code ─────────────────────────


def test_the_finder_claims_the_whole_composed_span(project):
    """`SG-ADR-032` must not also be read as a local `ADR-032`."""
    with_remote(project)
    refs = doc_refs.find_refs("see SG-ADR-032 for that")
    assert [(r.kind, r.remote, r.code) for r in refs] == [("remote", "SG", "ADR-032")]


def test_a_local_code_still_reads_as_local(project):
    with_remote(project)
    assert [r.kind for r in doc_refs.find_refs("see ADR-032 for that")] == ["adr"]


def test_the_fixer_writes_a_url_not_a_relative_path(project):
    """A different repository, so no `link_base` applies and the same target is
    right from every file."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    out, n = doc_refs.linkify("see SG-ADR-032", project / "docs" / "page.md")
    assert n == 1
    assert out == ("see [SG-ADR-032]"
                   "(https://github.com/o/r/blob/main/docs/decisions/adr-032-x.md)")


def test_an_unresolvable_foreign_code_is_not_linked(project):
    """The lint never demands a rewrite the fixer wouldn't make, so a code the
    remote doesn't have stays bare — and is reported instead."""
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    _, n = doc_refs.linkify("see SG-ADR-999", project / "docs" / "page.md")
    assert n == 0


def test_the_citation_scan_does_not_read_a_local_code_out_of_it(project):
    """`SG-ADR-012` must not count as a citation of *this* project's ADR-012 —
    which would keep a local retired decision looking cited forever."""
    decision(project, 12, "Superseded", "The replaced one")
    with_remote(project)
    (project / "notes.md").write_text("per SG-ADR-012 upstream\n")
    docs = ref_status.load_docs()
    result = ref_status.scan([project / "notes.md"], docs)
    assert result.cited == {}


def test_an_unresolvable_foreign_code_is_reported(project):
    """Blanking the composed span must not make it invisible — a foreign code
    that names nothing is still a reference nobody can follow (ADR-014)."""
    decision(project, 1, "Active")
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    (project / "notes.md").write_text("per SG-ADR-999 upstream\n")
    result = ref_status.scan([project / "notes.md"], ref_status.load_docs())
    assert [c.line for c in result.dangling["SG-ADR-999"]] == [1]


def test_the_annotation_validator_reads_the_composed_code(project):
    """`unresolved-ok: SG-ADR-012` must be checked against the *remote*. Reading
    `ADR-012` out of the middle asks the wrong project, and the annotation is
    then reported as stale for a reason that isn't true."""
    decision(project, 12, "Active", "A local decision")
    with_remote(project)
    lockfile(project, {"ADR-032": "adr-032-x.md"})
    (project / "notes.md").write_text(
        "<!-- unresolved-ok: SG-ADR-999 — upstream, not here -->\nSG-ADR-999\n")
    docs = ref_status.load_docs()
    result = ref_status.scan([project / "notes.md"], docs)
    assert ref_status.dangling(result, docs) == []
    assert ref_status.stale_annotations(result, docs) == []


# ── Discovery ────────────────────────────────────────────────────────────


def test_discovery_reads_both_filename_conventions(tmp_path):
    """A remote that predates ADR-013 has slugs; one that follows it doesn't.
    Both have to read, or adoption means renaming somebody else's repo."""
    found = remotes._from_names(
        ["adr-032-changelog-ci.md", "ADR-004.md", "README.md", "tags.yaml"])
    assert found == {"ADR-032": "adr-032-changelog-ci.md", "ADR-004": "ADR-004.md"}


def test_discovery_uses_the_remotes_own_config(project, tmp_path):
    """The remote's `luria.toml` is the authority on where its documents live.
    Reading it rather than guessing is why a config file exists at all."""
    upstream = tmp_path / "upstream"
    (upstream / "records").mkdir(parents=True)
    (upstream / "luria.toml").write_text(
        '[luria.schemes.ADR]\ndir = "records"\n')
    (upstream / "records" / "ADR-007.md").write_text("x")
    with_remote(project, f'path = "{upstream}"\n')

    found, how = remotes.discover(config.current().remotes["SG"])
    assert found == {"ADR-007": "ADR-007.md"}
    assert "local checkout" in how


def test_discovery_says_why_it_found_nothing(project):
    """A discovery that silently returns {} is indistinguishable from a remote
    with no documents (DP-1)."""
    with_remote(project, 'path = "/nonexistent"\n')
    found, how = remotes.discover(config.current().remotes["SG"])
    assert found == {} and how
