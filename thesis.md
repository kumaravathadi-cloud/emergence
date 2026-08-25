# Investment Thesis

Single fixed artifact, read by the analysis system for every candidate in a run
(see [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)).

## Sources
- **YC company directory** (ycombinator.com/companies) — batch, founder names/bios,
  one-liner, tags. Accessed by scraping the public directory pages (no login, no
  registration).
- **Hacker News** — Show HN posts + comment threads, for technical/community traction
  and unfiltered early reaction. Accessed via the public Algolia HN Search API
  (`https://hn.algolia.com/api/v1`, no auth required).

YC gives structured company/founder data at the source; HN signals whether technical
people engaged with it.

## Thesis Statement

> We back narrow, workflow-specific AI agents that fully own one repeatable
> back-office or ops task for small/medium businesses (1–200 employees).

A candidate fits the thesis when it:
1. Sells to SMBs as the primary buyer.
2. Automates a **named, specific workflow** end-to-end (e.g. "reconciles vendor
   invoices against POs").
3. Acts as an agent — takes actions and makes decisions within that workflow.

## Scoring Rubric (0–100)

| Category | Points | What earns points |
|---|---|---|
| **Product fit to thesis** | 30 | Clearly owns one named SMB workflow end-to-end; agentic (acts, not just answers) |
| **Team & execution signal** | 25 | Relevant domain or technical background; prior startup/exec experience; technical founder present |
| **Market & timing** | 20 | Workflow is common across many SMBs; credible "why now" (new model capability, new regulation, category shift) |
| **Traction / signal** | 15 | YC batch recency, HN engagement quality, any funding/GitHub/usage signal found |
| **Differentiation** | 10 | Defensible edge — proprietary data, workflow depth, integration, distribution |

Risk and open questions are captured in the memo's rationale and falsifiers section,
and feed directly into the Pass/Watch/Meeting call alongside the score.

## Call Mapping
- **0–39** → Pass
- **40–69** → Watch
- **70–100** → Take a meeting

The score sets the call; the memo's rationale documents the reasoning and the 2–3
things that would change it.