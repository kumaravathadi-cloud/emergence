import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from sourcing.normalize import normalize_hn, normalize_yc

SCHEMA = json.loads(
    (Path(__file__).resolve().parent.parent.parent / "schemas" / "candidate.v1.json").read_text()
)
VALIDATOR = Draft7Validator(SCHEMA)

YC_HIT_FULL = {
    "name": "Acme AI",
    "slug": "acme-ai",
    "website": "https://acme.ai",
    "one_liner": "AI agent that reconciles vendor invoices against POs.",
    "batch": "Summer 2026",
    "tags": ["B2B", "AI"],
}
YC_FOUNDERS_FULL = [
    {"full_name": "Jane Doe", "title": "Founder/CEO", "founder_bio": "Ex-Stripe."},
    {"full_name": "John Roe", "title": "Founder/CTO", "founder_bio": "Ex-Plaid."},
]

HN_HIT_FULL = {
    "title": "Show HN: Acme – AI agent for invoice reconciliation",
    "url": "https://acme.ai",
    "author": "janedoe",
    "objectID": "12345",
    "points": 87,
    "story_text": None,
}


def test_normalize_yc_full_data():
    candidate = normalize_yc(YC_HIT_FULL, YC_FOUNDERS_FULL, "run123")

    assert candidate["name"] == "Acme AI"
    assert candidate["site"] == "https://acme.ai"
    assert candidate["one_liner"] == "AI agent that reconciles vendor invoices against POs."
    assert candidate["founders"] == ["Jane Doe", "John Roe"]
    assert candidate["signal"] == {"source": "yc", "type": "batch", "value": "Summer 2026"}
    assert candidate["source_url"] == "https://www.ycombinator.com/companies/acme-ai"
    assert candidate["low_data"] is False
    assert candidate["flags"] == []
    VALIDATOR.validate(candidate)


def test_normalize_yc_thin_data_is_flagged_not_dropped():
    thin_hit = {"name": "Thin Co", "slug": "thin-co"}  # no website, one_liner, batch

    candidate = normalize_yc(thin_hit, [], "run123")

    assert candidate["name"] == "Thin Co"
    assert candidate["site"] is None
    assert candidate["founders"] == []
    assert candidate["low_data"] is True
    assert set(candidate["flags"]) == {
        "missing_site",
        "missing_one_liner",
        "missing_founders",
        "missing_signal",
    }
    VALIDATOR.validate(candidate)


def test_normalize_yc_missing_name_and_slug():
    candidate = normalize_yc({}, [], "run123")

    assert candidate["name"] == "Unknown"
    assert candidate["source_url"] == "https://www.ycombinator.com/companies"
    assert candidate["low_data"] is True
    assert "missing_name" in candidate["flags"]
    assert "missing_source_url" in candidate["flags"]
    VALIDATOR.validate(candidate)


def test_normalize_hn_full_data():
    candidate = normalize_hn(HN_HIT_FULL, "run123")

    assert candidate["name"] == "Acme"
    assert candidate["one_liner"] == "AI agent for invoice reconciliation"
    assert candidate["site"] == "https://acme.ai"
    assert candidate["founders"] == ["janedoe"]
    assert candidate["signal"] == {"source": "hacker_news", "type": "points", "value": 87}
    assert candidate["source_url"] == "https://news.ycombinator.com/item?id=12345"
    assert candidate["low_data"] is False
    VALIDATOR.validate(candidate)


def test_normalize_hn_thin_data_is_flagged_not_dropped():
    thin_hit = {
        "title": "Show HN: Mystery Thing",
        "url": None,
        "author": None,
        "objectID": "999",
        "points": None,
        "story_text": None,
    }

    candidate = normalize_hn(thin_hit, "run123")

    assert candidate["name"] == "Mystery Thing"
    assert candidate["site"] is None
    assert candidate["founders"] == []
    assert candidate["signal"]["value"] == 0
    assert candidate["low_data"] is True
    assert set(candidate["flags"]) == {
        "missing_site",
        "missing_one_liner",
        "missing_founders",
        "missing_signal",
    }
    VALIDATOR.validate(candidate)


@pytest.mark.parametrize(
    "title,expected_name,expected_one_liner",
    [
        ("Show HN: Acme – does a thing", "Acme", "does a thing"),
        ("Show HN: Acme - does a thing", "Acme", "does a thing"),
        ("Show HN: Acme: does a thing", "Acme", "does a thing"),
        ("Show HN: JustAName", "JustAName", None),
    ],
)
def test_normalize_hn_title_parsing(title, expected_name, expected_one_liner):
    hit = {**HN_HIT_FULL, "title": title, "story_text": None}

    candidate = normalize_hn(hit, "run123")

    assert candidate["name"] == expected_name
    assert candidate["one_liner"] == expected_one_liner
