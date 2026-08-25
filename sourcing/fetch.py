"""Clients for the two sourcing feeds: the YC company directory and Hacker News.

Both are public, unauthenticated surfaces:
- YC directory: the same public, search-only Algolia key YC's own site embeds in
  ycombinator.com/companies (scoped read-only to YCCompany_production, public tag).
  Founder names/bios aren't in that index, so they're read from the JSON YC's
  company page server-renders into the HTML (no JS execution needed).
- Hacker News: the public Algolia HN Search API, filtered to Show HN posts.

All endpoint/key/UA values are read from the environment (see .env.example) so they
can be updated without a code change if YC or HN change anything on their end.
"""

from __future__ import annotations

import html
import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from common.retry import call_with_retry

load_dotenv()

USER_AGENT = os.environ["SOURCING_USER_AGENT"]
TIMEOUT = float(os.environ["SOURCING_HTTP_TIMEOUT_SECONDS"])

YC_ALGOLIA_APP_ID = os.environ["YC_ALGOLIA_APP_ID"]
YC_ALGOLIA_API_KEY = os.environ["YC_ALGOLIA_API_KEY"]
YC_ALGOLIA_INDEX = os.environ["YC_ALGOLIA_INDEX"]
YC_ALGOLIA_URL = f"https://{YC_ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{YC_ALGOLIA_INDEX}/query"
YC_COMPANY_URL_TEMPLATE = os.environ["YC_COMPANY_URL_TEMPLATE"]

HN_SEARCH_URL = os.environ["HN_ALGOLIA_SEARCH_URL"]

_RETRYABLE = (httpx.HTTPError,)


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, follow_redirects=True)


def fetch_yc_companies(topic: str, *, hits_per_page: int = 20) -> list[dict[str, Any]]:
    """Search the YC directory for `topic`, returning raw Algolia hits."""

    def _do() -> list[dict[str, Any]]:
        with _client() as client:
            resp = client.post(
                YC_ALGOLIA_URL,
                headers={
                    "X-Algolia-Application-Id": YC_ALGOLIA_APP_ID,
                    "X-Algolia-API-Key": YC_ALGOLIA_API_KEY,
                },
                json={"query": topic, "hitsPerPage": hits_per_page},
            )
            resp.raise_for_status()
            return resp.json().get("hits", [])

    return call_with_retry(_do, exceptions=_RETRYABLE)


def fetch_yc_founders(slug: str) -> list[dict[str, Any]]:
    """Fetch a YC company page and extract its embedded founders list.

    Returns [] if the page can't be parsed rather than raising, since a missing
    founders block degrades the candidate to low_data rather than failing the run.
    """

    def _do() -> str:
        with _client() as client:
            resp = client.get(YC_COMPANY_URL_TEMPLATE.format(slug=slug))
            resp.raise_for_status()
            return resp.text

    page_html = call_with_retry(_do, exceptions=_RETRYABLE)
    founders = _extract_json_array(page_html, "founders")
    return founders or []


def fetch_hn_show_posts(topic: str, *, hits_per_page: int = 20) -> list[dict[str, Any]]:
    """Search HN Show HN posts for `topic`, returning raw Algolia hits."""

    def _do() -> list[dict[str, Any]]:
        with _client() as client:
            resp = client.get(
                HN_SEARCH_URL,
                params={"query": topic, "tags": "show_hn", "hitsPerPage": hits_per_page},
            )
            resp.raise_for_status()
            return resp.json().get("hits", [])

    return call_with_retry(_do, exceptions=_RETRYABLE)


def _extract_json_array(page_html: str, key: str) -> list[Any] | None:
    """Pull out the JSON array value of `"key":[...]` from HTML-escaped inline JSON.

    Server-rendered pages HTML-escape embedded JSON (e.g. &quot; for "), and the
    array can itself contain nested brackets/strings, so this walks it manually
    rather than relying on a regex.
    """
    text = html.unescape(page_html)
    marker = f'"{key}":['
    start = text.find(marker)
    if start == -1:
        return None

    array_start = start + len(marker) - 1  # index of the opening '['
    depth = 0
    in_string = False
    escaped = False
    end = None
    for i in range(array_start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end is None:
        return None

    try:
        return json.loads(text[array_start:end])
    except json.JSONDecodeError:
        return None
