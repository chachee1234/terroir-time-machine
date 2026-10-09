"""One door to the network for the data scripts (Tier 0, stdlib only).

urllib's urlopen also opens file://, ftp:// and custom schemes, so a URL that came from a server
response or a config file could read local files. open_url only lets http(s) through.
"""
import urllib.parse
import urllib.request


def open_url(req, timeout):
    """urllib.request.urlopen for an http(s) URL or Request; anything else raises ValueError."""
    url = req.full_url if isinstance(req, urllib.request.Request) else req
    if urllib.parse.urlsplit(url).scheme not in ("https", "http"):
        raise ValueError(f"refusing to open non-http(s) URL: {url!r}")
    return urllib.request.urlopen(req, timeout=timeout)  # nosec B310 - scheme checked above
