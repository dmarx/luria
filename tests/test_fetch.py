"""tests/test_fetch.py — every socket carries the configured user agent."""
from __future__ import annotations

import urllib.request

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

FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"


def _project(project, extra: str = "") -> None:
    (project / "record" / "literature.d").mkdir(parents=True, exist_ok=True)
    (project / "luria.yaml").write_text(merged(BASE, extra))
    config.reset()


def test_the_default_user_agent_is_a_browser_string(project):
    """A deliberate choice, not an oversight: the stdlib default announces
    `Python-urllib/3.x`, which is the shape of traffic a metadata host
    rate-limits first. A project that would rather identify itself honestly
    sets `user_agent` — which is why this is configuration and not a
    constant."""
    _project(project)
    assert config.current().user_agent == FIREFOX


def test_a_project_sets_its_own(project):
    _project(project, "user_agent: 'luria/0.29 (+mailto:me@example.org)'")
    assert config.current().user_agent == "luria/0.29 (+mailto:me@example.org)"


def test_the_request_carries_it(project):
    _project(project)
    req = fetch.request("https://example.test/x")
    assert req.get_header("User-agent") == FIREFOX


def test_a_head_request_keeps_both_the_method_and_the_agent(project):
    """The site that already built a `Request` did so for `method`, and is
    the one a header added to the obvious place would have missed."""
    _project(project)
    req = fetch.request("https://example.test/x", method="HEAD")
    assert req.get_method() == "HEAD"
    assert req.get_header("User-agent") == FIREFOX


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
    assert seen["agent"] == FIREFOX


def test_remote_discovery_sends_it(project, monkeypatch):
    """The third call site. All of luria's traffic or none — a tool that
    identifies itself on two endpoints out of three has not identified
    itself."""
    _project(project)
    seen = _capture(monkeypatch, remotes)
    remotes._fetch_bytes("https://example.test/x")
    assert seen["agent"] == FIREFOX


def test_the_head_probe_sends_it(project, monkeypatch):
    _project(project)
    seen = _capture(monkeypatch, remotes)
    remotes._head("https://example.test/x")
    assert seen["agent"] == FIREFOX
