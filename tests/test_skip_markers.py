"""The guard for a convention that has no escape.

A forge skips a build when the head commit's message carries a skip marker.
Nothing distinguishes an instruction from a mention, so a commit message
*about* the convention suppresses the build for the commit that writes about
it — which happened to a project adopting this package's own workflow, to an
author who had read the warning comment first.

The position rule is the whole design: subject line or trailer is an
instruction, anywhere else is prose. Everything below pins one half of that.
"""

import subprocess

import pytest

from luria import ci


# --- what passes silently -----------------------------------------------

def test_the_bots_own_commit_never_fires():
    """The generate action's default message, which is the reason no author
    check is needed: one line is first and last at once."""
    assert ci.prose_skip_marker("docs: regenerate views [skip ci]") is None


def test_a_deliberate_trailer_is_an_instruction():
    """Someone skipping a build on purpose puts the marker where the
    convention puts it. Reporting that would be reporting correct use."""
    assert ci.prose_skip_marker("fix a typo in the README\n\n[skip ci]") is None


def test_a_subject_line_skip_is_an_instruction():
    assert ci.prose_skip_marker("[skip ci] bump the pinned runner") is None


def test_an_ordinary_message_is_quiet():
    assert ci.prose_skip_marker("refactor the collector\n\nNo behaviour "
                                "change; the fragments are unaffected.") is None


# --- what it catches -----------------------------------------------------

def test_a_marker_described_in_the_body_fires():
    """The observed failure, reduced: a commit explaining what the marker
    does, and thereby doing it."""
    message = ("consolidate the build\n"
               "\n"
               "the generate action already marks its commits [skip ci];\n"
               "nothing else did.\n"
               "\n"
               "Co-Authored-By: someone <s@example.com>")
    assert ci.prose_skip_marker(message) == "[skip ci]"


@pytest.mark.parametrize("marker", ci.SKIP_MARKERS)
def test_every_spelling_is_caught(marker):
    """Five spellings, and a guard that knows one of them is a guard that
    misses four."""
    assert ci.prose_skip_marker(f"subject\n\nprose {marker} prose\n\ntrailer") \
        == marker


def test_the_match_is_case_insensitive():
    assert ci.prose_skip_marker("subject\n\nprose [SKIP CI] prose\n\nend") \
        == "[skip ci]"


# --- reading real history ------------------------------------------------

@pytest.fixture
def repo(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True,
                       capture_output=True)
    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "T")
    (tmp_path / "f").write_text("1")
    git("add", "-A")
    git("commit", "-q", "-m", "first")
    return tmp_path, git


def test_scanning_history_finds_the_prose_commit(repo, monkeypatch):
    path, git = repo
    (path / "f").write_text("2")
    git("add", "-A")
    git("commit", "-q", "-m",
        "subject\n\nexplaining [ci skip] here\n\ntrailer")
    monkeypatch.chdir(path)

    found = [m for _, msg in ci.commits("HEAD~1..HEAD")
             if (m := ci.prose_skip_marker(msg))]
    assert found == ["[ci skip]"]


def test_a_shallow_or_missing_history_says_nothing(tmp_path, monkeypatch):
    """`actions/checkout` fetches depth 1 by default, so an unreadable range
    is the ordinary case. A guard that cannot see history has nothing to
    say, and must not turn a checkout setting into a failed build."""
    monkeypatch.chdir(tmp_path)
    assert ci.commits("HEAD~50..HEAD") == []


def test_run_is_silent_when_there_is_nothing_to_say(repo, monkeypatch, capsys):
    """The lesson this module already learned once: a warning printed on
    correct runs trains readers to skip warnings."""
    path, _ = repo
    monkeypatch.chdir(path)
    ci.run("HEAD~1..HEAD")
    assert capsys.readouterr().err == ""


def test_run_warns_without_failing(repo, monkeypatch, capsys):
    path, git = repo
    (path / "f").write_text("2")
    git("add", "-A")
    git("commit", "-q", "-m", "subject\n\nabout [skip ci] again\n\ntrailer")
    monkeypatch.chdir(path)

    ci.run("HEAD~1..HEAD")                      # no SystemExit
    assert "[skip ci]" in capsys.readouterr().err


def test_strict_promotes_the_warning(repo, monkeypatch):
    path, git = repo
    (path / "f").write_text("2")
    git("add", "-A")
    git("commit", "-q", "-m", "subject\n\nabout [skip ci] again\n\ntrailer")
    monkeypatch.chdir(path)

    with pytest.raises(SystemExit):
        ci.run("HEAD~1..HEAD", strict=True)


def test_annotations_only_inside_the_forge(repo, monkeypatch, capsys):
    path, git = repo
    (path / "f").write_text("2")
    git("add", "-A")
    git("commit", "-q", "-m", "subject\n\nabout [no ci] again\n\ntrailer")
    monkeypatch.chdir(path)

    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    ci.run("HEAD~1..HEAD")
    assert capsys.readouterr().err.startswith("luria:")

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    ci.run("HEAD~1..HEAD")
    assert capsys.readouterr().err.startswith("::warning::")
