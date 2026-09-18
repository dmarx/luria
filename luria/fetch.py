"""The one place a request is built.

Every socket luria opens goes through `request()`, so the headers it sends
are a single fact rather than a habit repeated at three call sites
(DP-004). What made that worth extracting is that the sites had drifted
already: two passed a bare URL string to `urlopen` and one built a `Request`
to set `method="HEAD"`, so a header added to the obvious place would have
covered some of luria's traffic and not the rest.
"""
from __future__ import annotations

import urllib.request

from .config import current


def request(url: str, method: str | None = None) -> urllib.request.Request:
    """A `Request` carrying this project's `user_agent`.

    Passed to `urlopen` in place of a bare URL. The stdlib default is
    `Python-urllib/3.x`, which identifies the language and nothing else —
    not the tool, not the project, not a way to be contacted — and is the
    shape of traffic a host rate-limits first.
    """
    headers = {"User-Agent": current().user_agent}
    return (urllib.request.Request(url, headers=headers, method=method)
            if method else urllib.request.Request(url, headers=headers))
