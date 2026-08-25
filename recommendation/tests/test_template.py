from recommendation.template import render_memo

ANALYSIS = {
    "schema_version": "1",
    "run_id": "run123",
    "candidate_name": "Acme AI",
    "source_url": "https://www.ycombinator.com/companies/acme-ai",
    "team": {"summary": "Solo technical founder.", "citations": ["https://acme.ai"]},
    "product": {
        "summary": "Owns invoice reconciliation end to end.",
        "citations": ["https://acme.ai"],
    },
    "market": {"summary": "Common SMB workflow.", "citations": ["https://acme.ai"]},
    "traction": {
        "summary": "YC batch Summer 2026 is the only traction evidence.",
        "citations": ["https://www.ycombinator.com/companies/acme-ai"],
    },
    "risks": {"summary": "Early stage, unproven retention.", "citations": ["https://acme.ai"]},
    "differentiation": {"summary": "Deep ERP integrations.", "citations": ["https://acme.ai"]},
    "score": {
        "product_fit": 24,
        "team_execution": 15,
        "market_timing": 14,
        "traction": 9,
        "differentiation": 4,
        "total": 66,
    },
    "confidence": "high",
    "flags": [],
}


def test_render_memo_includes_call_and_score():
    memo = render_memo(
        ANALYSIS,
        call="Watch",
        call_note="score 66/100 maps to Watch.",
        falsifiers=["Do X.", "Do Y."],
    )

    assert "# Acme AI" in memo
    assert "**Call: Watch**" in memo
    assert "66/100" in memo


def test_render_memo_lists_falsifiers_in_order():
    memo = render_memo(
        ANALYSIS, call="Watch", call_note="note", falsifiers=["First thing.", "Second thing."]
    )

    assert "1. First thing." in memo
    assert "2. Second thing." in memo


def test_render_memo_dedupes_and_includes_sources():
    memo = render_memo(ANALYSIS, call="Watch", call_note="note", falsifiers=[])

    assert memo.count("https://acme.ai") == 1
    assert "https://www.ycombinator.com/companies/acme-ai" in memo


def test_render_memo_flags_low_confidence():
    low_confidence = {**ANALYSIS, "confidence": "low", "flags": ["missing_founders"]}

    memo = render_memo(low_confidence, call="Watch", call_note="note", falsifiers=[])

    assert "Low confidence" in memo
    assert "missing_founders" in memo


def test_render_memo_is_skimmable_length():
    memo = render_memo(
        ANALYSIS,
        call="Watch",
        call_note="score 66/100 maps to Watch.",
        falsifiers=["Do X.", "Do Y."],
    )

    # A partner should be able to skim it in under 60s cold.
    assert len(memo.splitlines()) < 40
