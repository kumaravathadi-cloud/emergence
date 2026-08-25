"""Raw source payloads (YC Algolia hit, HN Algolia hit) -> candidate schema.

A candidate with a missing required field isn't dropped: it's kept with the
field set to a safe fallback and a reason appended to `flags`, so a thin
candidate degrades to `low_data: true` instead of breaking the run.
"""

from __future__ import annotations

from typing import Any

CANDIDATE_SCHEMA_VERSION = "1"

_HN_TITLE_SEPARATORS = (" – ", " — ", " - ", ": ")
_SHOW_HN_PREFIX = "Show HN: "


def normalize_yc(
    hit: dict[str, Any], founders: list[dict[str, Any]], run_id: str
) -> dict[str, Any]:
    name = (hit.get("name") or "").strip()
    site = (hit.get("website") or "").strip() or None
    one_liner = (hit.get("one_liner") or "").strip() or None
    founder_names = [f["full_name"] for f in founders if f.get("full_name")]
    slug = hit.get("slug")
    batch = (hit.get("batch") or "").strip() or None
    source_url = f"https://www.ycombinator.com/companies/{slug}" if slug else None

    flags = []
    if not name:
        flags.append("missing_name")
        name = "Unknown"
    if not site:
        flags.append("missing_site")
    if not one_liner:
        flags.append("missing_one_liner")
    if not founder_names:
        flags.append("missing_founders")
    if not source_url:
        flags.append("missing_source_url")
        source_url = "https://www.ycombinator.com/companies"
    if not batch:
        flags.append("missing_signal")

    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "run_id": run_id,
        "name": name,
        "site": site,
        "one_liner": one_liner,
        "founders": founder_names,
        "signal": {"source": "yc", "type": "batch", "value": batch or "unknown"},
        "source_url": source_url,
        "low_data": bool(flags),
        "flags": flags,
    }


def normalize_hn(hit: dict[str, Any], run_id: str) -> dict[str, Any]:
    raw_title = (hit.get("title") or "").strip()
    name = raw_title
    if name.startswith(_SHOW_HN_PREFIX):
        name = name[len(_SHOW_HN_PREFIX) :]

    one_liner = None
    for sep in _HN_TITLE_SEPARATORS:
        if sep in name:
            base, _, tail = name.partition(sep)
            name, one_liner = base.strip(), tail.strip()
            break
    if not one_liner:
        story_text = hit.get("story_text")
        one_liner = story_text.strip() if story_text else None

    site = (hit.get("url") or "").strip() or None
    author = hit.get("author")
    founders = [author] if author else []
    object_id = hit.get("objectID")
    source_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else None
    points = hit.get("points")

    flags = []
    if not name:
        flags.append("missing_name")
        name = "Unknown"
    if not site:
        flags.append("missing_site")
    if not one_liner:
        flags.append("missing_one_liner")
    if not founders:
        flags.append("missing_founders")
    if not source_url:
        flags.append("missing_source_url")
        source_url = "https://news.ycombinator.com/"
    if points is None:
        flags.append("missing_signal")

    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "run_id": run_id,
        "name": name,
        "site": site,
        "one_liner": one_liner,
        "founders": founders,
        "signal": {
            "source": "hacker_news",
            "type": "points",
            "value": points if points is not None else 0,
        },
        "source_url": source_url,
        "low_data": bool(flags),
        "flags": flags,
    }
