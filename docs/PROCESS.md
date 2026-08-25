# How This Was Approached

## 1. Vision first
Started by turning the take-home brief into [VISION.md](VISION.md) — objective, scope,
user workflow, AI's role, requirements, success metrics, risks. Goal: know what "done"
looks like before touching design.

## 2. Identify components + non-functional shape
Broke the objective into three components: sourcing, analysis, recommendation. Before
designing them, fixed the non-functional bar each had to meet — scalability (each
component independently pullable into its own service later), maintainability
(versioned data contracts, no shared business logic), reliability (retries, schema
validation, per-candidate failure isolation, not whole-run failure). These constraints
shaped the design, not an afterthought bolted on.

## 3. System design
Turned the three components + non-functional bar into [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md):
a Mermaid flow of the three stages, a folder structure with each component as an
independent package connected only by a file contract, and explicit reliability/
maintainability mechanisms (retry wrapper, schema versioning, structured logging).

## 4. Fixed the scope
Narrowed to a small number of concrete decisions instead of leaving them open:
sourcing from the YC company directory + Hacker News only (Product Hunt dropped after
its scraping path turned out to be Cloudflare-blocked), topic-query input only,
Python, one fixed thesis for the whole run. Each open question was resolved
explicitly rather than left ambiguous going into the build.

## 5. Thesis: how scope became scoring
Wrote [thesis.md](../thesis.md) to make the scope decision usable by the pipeline
itself: a specific thesis statement (narrow, workflow-specific AI agents for SMBs),
a weighted 0–100 rubric derived directly from that statement (product fit, team,
market/timing, traction, differentiation), and a fixed score-to-call mapping
(Pass / Watch / Meeting). The rubric's categories map 1:1 to the thesis criteria, so
the score is an application of the scope decision, not a separate judgment call.

## Sequence
`VISION.md` → components + scalability/reliability/maintainability bar →
`SYSTEM_DESIGN.md` → scope fixed to specific decisions → `thesis.md` (scope → scoring)
→ implementation.