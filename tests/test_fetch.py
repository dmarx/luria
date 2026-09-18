"""tests/test_fetch.py — every socket carries the configured user agent."""
from __future__ import annotations

import urllib.request
from importlib import metadata

from _config import merged
from luria import config, fetch, remotes, sources

BASE = """
paths:
  record: record
  docs: docs
schemes:
  LIT:
    dir: record/literature.d
    output: docs/literature
    title: Literature
remotes:
  ARXIV:
    name: arXiv
    uid: '(\\d{4})[.:](\\d{4,5})'
    url: https://arxiv.example/abs/{1}.{2}
    uris:
      title: https://export.example/api?id={1}.{2}
    title_re: '<title>(.*?)</title>'
"""

def _default() -> str:
    return config.DEFAULTS["user_agent"]


def _project(project, extra: str = "") -> None:
    (project / "record" / "literature.d").mkdir(parents=True, exist_ok=True)
    (project / "luria.yaml").write_text(merged(BASE, extra))
    config.reset()


def test_the_default_names_the_software_and_nothing_else(project):
    """Two constraints at once, and this pins both.

    It must be honest — `luria/<version>`, the way `curl/8.0` is — because
    the stdlib default names the language and is what a metadata host
    rations first. And it must carry NO contact: a URL or mailbox in a
    shipped default routes every user's traffic to whoever maintains luria,
    who did not agree to that and is not the operator a host wants anyway.
    The contact is the project's to add."""
    _project(project)
    agent = config.current().user_agent
    assert agent.startswith("luria/")
    assert "Mozilla" not in agent
    assert "@" not in agent and "http" not in agent


def test_the_version_comes_from_package_metadata(project):
    """Not from `luria.__version__`, which is a stale hand-maintained
    `0.1.0` that `pyproject.toml` says should not exist (#295). A user agent
    claiming 0.1.0 would misreport the software it is being honest about."""
    _project(project)
    assert config.current().user_agent != "luria/0.1.0"


def test_a_project_sets_its_own(project):
    _project(project, "user_agent: 'luria/0.29 (+mailto:me@example.org)'")
    assert config.current().user_agent == "luria/0.29 (+mailto:me@example.org)"


def test_the_request_carries_it(project):
    _project(project)
    req = fetch.request("https://example.test/x")
    assert req.get_header("User-agent") == _default()


def test_a_head_request_keeps_both_the_method_and_the_agent(project):
    """The site that already built a `Request` did so for `method`, and is
    the one a header added to the obvious place would have missed."""
    _project(project)
    req = fetch.request("https://example.test/x", method="HEAD")
    assert req.get_method() == "HEAD"
    assert req.get_header("User-agent") == _default()


def _capture(monkeypatch, module):
    seen = {}

    class _R:
        status = 200
        def read(self): return b"<title>x</title>"
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake(req, *a, **k):
        seen["agent"] = req.get_header("User-agent")
        seen["url"] = req.full_url
        return _R()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake)
    return seen


def test_the_identifier_check_sends_it(project, monkeypatch):
    _project(project)
    seen = _capture(monkeypatch, sources)
    sources._once("https://example.test/x", "<title>(.*?)</title>")
    assert seen["agent"] == _default()


def test_remote_discovery_sends_it(project, monkeypatch):
    """The third call site. All of luria's traffic or none — a tool that
    identifies itself on two endpoints out of three has not identified
    itself."""
    _project(project)
    seen = _capture(monkeypatch, remotes)
    remotes._fetch_bytes("https://example.test/x")
    assert seen["agent"] == _default()


def test_the_head_probe_sends_it(project, monkeypatch):
    _project(project)
    seen = _capture(monkeypatch, remotes)
    remotes._head("https://example.test/x")
    assert seen["agent"] == _default()


def test_the_package_version_is_not_hand_written():
    """`__version__` sat at "0.1.0" through twenty-seven releases while
    `pyproject.toml` derived the real version from git tags (#295). It is
    read from distribution metadata now, and this fails if anyone writes a
    literal back."""
    import luria
    assert luria.__version__ != "0.1.0"
    assert luria.__version__ == metadata.version("luria")
