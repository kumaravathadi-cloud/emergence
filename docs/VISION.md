# AI-Augmented Investment Pipeline — Build Plan

## 1. Objective
Automate the triage layer of VC deal sourcing: topic in → ranked, sourced memos out. Partners only spend time on the top 10%.

## 2. Scope
A single CLI running 3 stages (source → analyze → recommend), sourcing from the **YC company directory + Hacker News**, scored against the fixed thesis in [thesis.md](../thesis.md) (AI agents for SMB workflows), with all outputs committed to the repo.

## 3. User Workflow
```
partner runs 1 command with a topic
  → 10–20 candidates sourced
  → each analyzed against thesis
  → 1 memo/candidate: Pass / Watch / Meeting
partner skims each memo in <60s
```

## 4. AI Role
- **In product:** extraction, analysis, scoring, memo drafting — every claim cited back to a source.
- **In build:** used for planning/coding/debugging, disclosed honestly, with commits and decision notes captured as the work happens.

## 5. Requirements
- Input: topic query
- Output per candidate: name, site, one-liner, founder signal, 1 traction signal
- Analysis: team, product, market, risks, score (0–100) vs. thesis
- Memo: call + rationale + 2–3 things that'd change it
- All claims traceable to a source
- Thin/missing data produces a flagged, lower-confidence memo
- Single command run; stages independently re-runnable

## 6. Architecture
```
seed input
  → [source]   candidates.json   (YC directory + Hacker News, cached raw)
  → [analyze]  <company>.json    (thesis-scored, cited)
  → [recommend] <company>.md     (memo)
```
File hand-off between stages. Thesis is one fixed config, referenced everywhere.

## 7. Plan to Build
1. Write the thesis (specific, defensible) — everything depends on this
2. Sourcing stage → commit sample candidates.json
3. Analysis stage → structured JSON per candidate, cited
4. Recommendation stage → memo template + generation
5. CLI entrypoint wiring all 3 (stage-level re-run flags)
6. Handle thin/bad data cases
7. Tests on parsing + scoring logic
8. Commit a full real run's outputs
9. Record 5-min walkthrough (1 startup, end-to-end)

## 8. Evaluation Targets
- Process/AI-workflow trail visible, built in from the start (40% of grade)
- Memos skimmable, scores defensible, robust to bad data (20%)
- Thesis specific + held consistently, right corners cut (20%)
- Clean stage separation, replayable (10%)
- Readable, modular, tested (10%)

## 9. Success Metrics
- One command → memos out
- Any memo's call understood in <60s
- 100% of claims traceable to a source
- Run survives thin-data candidates
- Reviewer gets a real picture of the build process from the repo alone

## 10. Risks
| Risk | Mitigation |
|---|---|
| Hallucinated claims | force citations at analysis stage |
| Thesis drift | one fixed thesis artifact, reused everywhere |
| Bad data breaks a run | explicit low-confidence path per candidate |
| Reflective writing reads authentic | write notes contemporaneously, as I build |