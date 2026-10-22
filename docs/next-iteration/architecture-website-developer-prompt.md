# WHY/NOW — architecture website developer handoff

Prepared 22 October 2026. This document is a self-contained prompt to give a website developer or an AI website builder. Its subject is the current local v0.5 MVP, with a separately identified Azure engineering topology and future work. Build the architecture website described below; this is not a request to change or deploy the product backend.

---

## Your assignment

Act as a senior product designer, information architect, and frontend engineer. Build a professional, interactive **software architecture explainer for WHY/NOW**, a football storytelling product developed for Microsoft's Inside the Game hackathon.

The central deliverable is a readable, technically accurate architecture diagram presented as a polished website. The diagram must be the main experience, visible immediately below a compact introduction. A judge should understand the product in 30 seconds, trace one story in two minutes, and inspect engineering decisions in five minutes.

Reference: https://preview--quipu-guardian-angel.lovable.app/

Inspect that reference if you have access. At handoff preparation it redirected to Lovable authentication, so its visual design has not been verified. Use it as the owner's intended reference, without claiming to reproduce unseen details. If it remains unavailable, proceed with the specific design direction below. Do not block implementation on access or invent observations about the reference.

Deliver a working responsive website, its editable diagram data, an exportable architecture image, and concise maintenance instructions. Make sensible reversible implementation decisions independently.

## Product story and language

**Name:** WHY/NOW

**Headline:** “From match evidence to a story worth showing.”

**Supporting copy:** “WHY/NOW turns time-scoped football observations into evidence-backed explanations. Agents propose and review supported stories. A producer approves the exact version viewers see.”

The product helps producers surface understandable moments and lets viewers inspect why a statement was made. It uses synthetic football observations today. It is not a video-analysis model, a match prediction service, or an integrated commercial live-data feed.

The architectural strengths to make visible are:

- Evidence is limited to what has arrived by the investigation's cutoff.
- Deterministic calculations and constrained rendering anchor every published claim.
- Distinct agent roles propose and review; humans retain publication authority.
- Every pass has its own story, revisions, evidence hash, and approval lifecycle.
- Viewer personalization selects previously prepared content without new model calls.
- Corrections, stale results, and retries have explicit handling.

Use concise product language on the canvas. Put implementation details in expandable panels. Avoid “autonomous publishing,” “AI understands the whole match,” “hallucination-free,” “production proven,” guaranteed scores, or prize claims.

## Visual direction

Create a restrained football broadcast control-room aesthetic: precise typography, clear lanes, measured use of color, and generous spacing. Aim for a technical product exhibit that engineers trust and nontechnical viewers can follow.

Suggested tokens, subject to contrast checks:

| Purpose | Color |
|---|---|
| Background | Midnight navy `#07111F` |
| Panels | Slate navy `#101E30` |
| Primary text | Cool white `#F3F7FC` |
| Secondary text | Blue gray `#A9B9CA` |
| Match data / supported evidence | Pitch green `#45D39A` |
| Azure infrastructure | Azure blue `#49A9FF` |
| Agent orchestration | Soft violet `#B6A0FF` |
| Human approval / attention | Amber `#F5C66A` |
| Invalidated / rejected | Coral `#FF8B8B` |

Use a readable sans serif such as Inter or the existing system font; reserve monospace for IDs, hashes, versions, and technical labels. Use subtle pitch geometry only as low-contrast background decoration. Avoid stadium photography behind the graph, large gradient hero sections, excessive glow, 3D nodes, bouncing cards, or continuous animated particles.

Use official service icons where licensing permits and a consistent icon family elsewhere. Always pair icons and state colors with text. Branding must not imply Microsoft endorsement. Provide a clean light-background export regardless of the website's dark theme.

## Information structure and controls

Use a compact header with WHY/NOW, “Architecture,” a snapshot date, and a presentation-mode control. Immediately below, display the headline, one supporting sentence, and the diagram.

Provide five views using the same underlying architecture data:

1. **Story journey** — default; approximately 8–10 readable grouped nodes.
2. **Agent decisions** — role handoffs, tools, deterministic checks, bounded repair, and fallback.
3. **Azure infrastructure** — service boundaries, hosting, persistence, identity, and operations.
4. **Trust & recovery** — approval, corrections, immutable revisions, retry, expiry, and reconnect.
5. **Evidence & next steps** — measured results, limitations, and distinctly marked planned work.

Allow node selection to open a detail panel containing its purpose, inputs, outputs, technology, authority/permissions, failure behavior, implementation status, and source references. Highlight direct dependencies on selection and dim unrelated connections. Label arrows with concrete payloads or actions; “data” alone is insufficient.

Provide zoom, fit-to-view, reset, and a legend. Keep panning inside the diagram. Provide a keyboard-accessible ordered text view with equivalent content. On small screens, default to a vertical journey with expandable cards; never shrink a desktop graph until labels become unreadable.

Separate two kinds of status:

- **Implementation:** current code / evaluation only / planned.
- **Environment evidence:** local candidate / documented Azure topology / deployment verification needed.

Do not turn the presence of a cloud resource into a green claim that the latest code is deployed there. Keep status and edge legends distinct. Hide planned nodes by default; reveal them using “Show planned work,” with explicit badges and dashed boundaries.

## Authoritative architecture content

The following is the baseline content specification. If repository access is available, verify it against current source before implementing. If access is unavailable, use this supplied snapshot and label its date.

### Story journey

Render this main sequence, expanding grouped nodes on selection:

**Synthetic observations → Replay availability → Durable evidence and deterministic metrics → Story Director → Constrained renderer → Claim Reviewer → Immutable story package → Producer approval → Viewer / overlay / recap.**

Show template mode as a real alternative to model generation. The application can create a supported package without model calls; it still requires producer approval for publication. Model fallback must be labeled.

Use these node responsibilities:

| Node | Responsibility and important boundary |
|---|---|
| Synthetic observations | An allowlisted catalogue of 171 replays: three original plus 168 expanded cases. Observation events and tracking are runtime inputs; hidden evaluation labels are excluded. These are not 171 independent real matches. |
| Replay availability | Maps elapsed wall time to a synthetic replay clock; releases observations by `available_at_ms`. Resets create a new session. Event Hubs does not implement this clock. |
| Evidence and metrics | Stores delivered observations, applies correction lineage in projections, checks complete coverage/continuity, calculates supported metrics, and binds tools to a selected pass and time cutoff. Incomplete evidence can withhold a claim or story. |
| Story Director | Selects an angle and orders supported claim blocks. It can request bounded evidence. It does not invent measurements or publish. |
| Constrained renderer | Code produces exact bilingual wording, scoped actor references, titles, qualifications, and variants; validates the plan against canonical facts. This is software, not another agent. |
| Claim Reviewer | Checks rendered content against canonical facts and bounded evidence; can support, request evidence, request revision, or reject. It is a separate role using the same model deployment, not a statistically independent truth oracle. |
| Immutable package | Stores exact story/revision/hash, evidence references, rendered variants, and review provenance. A valid stored candidate is not an approved publication. |
| Producer | Reviews, edits, approves, suppresses, or retracts. Approval binds the exact revision and evidence hash. Edits create a new revision and invalidate prior approval. |
| Audience delivery | Approved story variants, timed shared overlay, evidence inspection, approved history, and recaps. Personal language/detail/focus selection does not grant editorial authority or trigger new model generation. |

The audience product includes English/Spanish, simple/detailed explanations, player/team focus, inline evidence, a pitch replay, signed prior-pass comparison bars, and Return to live. All 100 combinations are prepared before approval: four language/detail bases × general, 22 players, and two teams. These are generated selections over the same facts, not 100 model calls.

The current v4 rendering distinguishes a factually true distance comparison from recommended editorial prominence. A provisional policy recommends emphasis at ≥3 m and ≥20% above the largest of the previous three comparators, using an absolute-only test near zero. This is a product hypothesis awaiting football review, not a validated measure of tactical value. Put this detail in a panel, not on the main canvas.

### Agent decisions view

Draw an application-owned workflow boundary labeled **“Python API · Microsoft Agent Framework.”** Inside it, distinguish agent-role nodes from deterministic validation/renderer nodes. Outside it, show the existing **Microsoft Foundry / Azure OpenAI model deployment**, shared by both roles.

Current model configuration: GPT-4o mini, version `2024-07-18`, deployment `story-model`. Latest local prompt: `director-critic-v4.1`; package schema `4.0.0`; renderer `editorial-claims-v4`. Historical v1/v2/v3 packages retain their original approved text and hashes.

Show a typed plan handoff from Director to renderer, rendered proposal and canonical claims to Reviewer, and reviewer feedback returning for at most one shared repair. Invalid-plan validator feedback also consumes this repair allowance; do not draw a separate unlimited loop.

Display the current bounds in an expandable “Execution budget” panel: normal path two model calls; at most six calls, twelve read-only tool requests, 15 seconds, and a conservative 32,000-token budget. There are two simultaneous workflow workers and at most four pending jobs. These application bounds are not a hard Azure invoice cap.

Tools can read bounded evidence; their windows are capped at 15 seconds and 180 observations. They cannot read arbitrary files, future observations, hidden evaluation labels, or publish content. Provider failure, invalid output, exhaustion, or concurrency limits can lead to a labeled factual fallback or abstention, still subject to the publication gate.

Add an **evaluation-only inset**, visually outside production flow:

- T3: deterministic selection and renderer.
- S3: one agent with self-check and repair.
- M3: Director plus Reviewer.
- D3: Director without model review; explicit evaluation flag, unavailable as an application selection.

Do not draw these four arms as four concurrent production agents.

### Azure infrastructure view

Label this **“Documented engineering topology; latest local release deployment not verified.”** Group resources by responsibility, not in one large undifferentiated cloud box. Resource group: `rg-whynow-demo`. The latest local v0.5 changes were not deployed during the last iteration.

| Boundary | Components and relationships |
|---|---|
| Browser | Producer studio `/studio/{sessionId}`, viewer `/watch/{sessionId}`, overlay `/overlay/{sessionId}`. Browsers call the web origin. |
| Azure Container Apps · East US | Public Next.js web app and internal FastAPI API, in `whynow-env`. Web proxies `/api/*`, including SSE, to the API. One replica per app and one API worker; scaling beyond this is not certified. |
| API application modules | Replay publisher, Event Hubs consumer, state/projection engine, deterministic metrics, bounded agent workflow, publication controls, snapshot/SSE delivery. These are logical responsibilities inside the API deployment, not separately deployed microservices. |
| Event Hubs · East US | Standard namespace; `match-observations`, two partitions, session partition key, consumer group `whynow-state`. Carries released observations to the consumer. |
| Blob Storage · East US | Private `eventhub-checkpoints` container. Consumer persists observations before checkpoint updates. Blob checkpoint storage is not the publication database. |
| Cosmos DB · East US 2 | Serverless account; `whynow` database; `session-state`, `story-state`, `observations`, partitioned by `/session_id`. Note the cross-region boundary without claiming measured latency. |
| Foundry / Azure OpenAI · East US | Resource and Foundry project with one shared text-model deployment. Workflow executes in the API container; this is not a Foundry hosted-agent service. |
| Identity | Separate API and web managed identities. API accesses required data/model services; web identity has image-pull permission. Prototype producer writes use a protected producer token. Production Entra producer onboarding is future work. |
| Build and operations | Azure Container Registry supplies API/web images. OpenTelemetry feeds Application Insights and Log Analytics. Put image deployment, authorization, and telemetry connections in an operations layer, separate from story payload flow. |

Show local mode in a compact alternative inset: Next.js + FastAPI, SQLite persistence, local observation transport, deterministic templates by default. Foundry model calls are an explicit option. SQLite and Cosmos are alternative persistence adapters, not sequential stores or replicated peers.

Do not add AI Search, vector search, RAG, AKS, Fabric, Service Bus, APIM, Key Vault, video recognition, or a hosted agent runtime as existing components. They are not part of the documented topology. Do not invent extra services for visual complexity.

### Trust and recovery view

Show three labeled sequences with a step-through control:

**A. Supported story:** observation becomes available → evidence and metrics → proposal/render/review → candidate persisted → producer approves exact revision/hash → approved variant and overlay become visible.

**B. Delivered correction:** corrected source arrives → affected story evidence hash changes → prior approval becomes invalid → replacement candidate requires fresh review/approval → viewer publication state updates. Other passes keep their independent approvals. Never depict an approved package being rewritten in place.

**C. Failure and recovery:** malformed plan receives bounded repair feedback; unresolved failure uses labeled fallback or abstention. Separately illustrate a lost persistence response: exact retry finds the durable package and reconciles accounting without duplicating publication.

Explain these invariants in node details:

- Package acceptance and its acceptance lifecycle events commit in one SQLite transaction or one Cosmos same-partition batch. Package acceptance here means durable storage, not human approval. Do not imply an atomic transaction across Cosmos containers.
- Historical recovery requires an exact durable revision/hash and records recovery time, not an invented original acceptance timestamp.
- Jobs bind session, story, and evidence revision; stale completion cannot overwrite another pass or revive an expired display.
- SSE reconnect sends an authoritative resync snapshot. There is no claimed durable SSE message backlog. A periodic snapshot provides a recovery path.
- An expired overlay may still have an approved historical story. Expiry and retraction are distinct states.
- Return to live changes a viewer's personal selection; it does not change the shared replay or another viewer's overlay.

Label animations **“Illustrative architecture walkthrough”**. Step durations and sample values must not look like live telemetry or measured performance. Use sanitized synthetic examples only.

### Evidence and next steps view

Use a compact evidence panel, dated to this snapshot. Avoid celebratory score gauges or invented uptime counters.

- 325 backend tests passed.
- 17 local browser tests passed; two hosted checks excluded.
- Production frontend build and TypeScript passed.
- Synthetic regression: 168 cases, 594 checkpoints, 72 distinct moments, unchanged baseline.
- Agent discovery: 60 outcomes over 15 correlated cases across four arms. All selected the same broad angles; M3 requested no repairs. S3 produced one factual fallback. **The comparison did not demonstrate an advantage for the two-agent approach.**
- Human football, producer/viewer usefulness, and independent Spanish reviews are pending. Reviewers can be arranged; no completed ratings are implied.

Clearly mark planned work:

1. Blinded expert/user reviews and a fresh independent final evaluation set.
2. Retain or simplify agent architecture according to measured usefulness and editing effort.
3. Exact durable-evidence-to-display timing, clock uncertainty, and varied continuous-opportunity measurements.
4. Persistent reverse-dependency indexing, retention decisions, and lock profiling.
5. A declared-unit incoming vendor-feed adapter with independent format tests; current input remains allowlisted synthetic replays.

These roadmap items should appear as future additions/validation gates, not services already connected in the main flow. Live-feed ingestion is not merely a vendor logo swap.

## Engineering requirements for this website

If integrating into the existing repository, follow its AGENTS.md and use its existing Next.js App Router, TypeScript, React, and Tailwind setup. An `/architecture` route is a suitable reversible default. If building separately in Lovable or another React environment, keep this explainer self-contained and document how to move it later. Do not require backend credentials or product mutations to view it.

Use an editable SVG/DOM graph, with an established graph library only if useful. Verify the chosen library's current official documentation before using its APIs. Avoid a bitmap-only diagram or a graph built as one unmaintainable JSX block.

Keep content separate from presentation in typed architecture data. Each node should have an ID, title, kind, responsibility, implementation status, environment evidence, inputs, outputs, limitations, source references, and group. Each edge should have an ID, endpoints, label, relation type, and applicable view. Use distinct labeled styles for runtime payload, control/approval, model request, observability, and planned relationships. Group boundaries must remain understandable in export.

Interaction requirements:

- Node and view deep links so a reviewer can share a specific part of the architecture.
- Guided walkthrough with next/previous, pause/reset, and a visible current step.
- Presentation mode that hides secondary controls and fits a 16:9 display.
- SVG export preserving readable labels; high-resolution PNG export; printable text/diagram view for PDF printing.
- Every export includes title, snapshot date, view, legend, and status caveats relevant to that view.
- Native accessible controls, visible focus, Escape dismissal and focus restoration for dialogs, meaningful labels, reduced-motion support, and no hover-only facts.
- Verify text contrast, non-color state distinctions, 200% text zoom, and touch interaction. Provide equivalent list content for readers who cannot use the graph.
- Smooth interaction with a small graph; lazy-load optional diagram/export tooling and avoid unnecessary animation dependencies.

Keep private endpoints, subscription identifiers, tokens, keys, private reviewer mappings, and raw traces out of browser bundles and exports. Use logical resource labels on the default canvas. Provide source file paths in a developer reference panel, but do not create broken public GitHub links to a private repository.

## Source-of-truth checklist

Repository owner/name: `jamesrhurtado/why-now` (private; MIT). Working directory if available: `/Users/james/dev/why now`.

Read these before implementation, in this order:

1. `docs/next-iteration/quality-v4-handoff.md` — current iteration and verification.
2. `engine/structured_workflow.py` and `engine/editorial_narrative.py` — latest role/prompt/renderer behavior.
3. `docs/architecture.md` — system invariants and boundaries; contains historical version sections.
4. `docs/azure/README.md` and service-specific files — documented Azure topology; deployment details can lag local code.
5. `engine/repository.py`, `engine/cloud_repository.py`, `engine/dispositions.py`, and `services/api/main.py` — state, transactions, recovery, API boundaries.
6. `docs/next-iteration/multi-agent-evidence.md` and `evals/agentic/discovery-v4/README.md` — actual comparison, limitations, and decision rules.
7. `docs/incoming-feed.md` and `docs/next-iteration/reviewer-guide-v4.md` — input boundary and pending validation.

When older architecture prose disagrees with current code and the dated v4 handoff, preserve the historical distinction and use verified current behavior for the default view. In particular, old v3/v4.0 sections are not the latest v4.1 prompt. Record unresolved discrepancies instead of silently guessing.

## Delivery and acceptance

Deliver the working page, typed diagram data, component source, one clean 16:9 architecture export, mobile/desktop screenshots, and README instructions for running, editing, and exporting. Include a brief fact-check table mapping major diagram claims to their source files. Run build/type checks and meaningful interaction tests for view switching, node details, walkthrough, keyboard navigation, and export.

The work is complete when:

- A first-time visitor can identify input, evidence checks, agent roles, human approval, and audience output without opening details.
- Every arrow has a defensible direction and meaning; logical modules are visibly distinct from deployed resources.
- The latest local candidate, recorded cloud topology, evaluation-only arms, and future work cannot be mistaken for one another.
- Corrections and failures visibly preserve the human approval boundary.
- The graph is readable on a laptop, navigable on mobile, and understandable through its text alternative.
- Exports are complete, readable, and include relevant limitations.
- There are no fabricated integrations, live indicators, success metrics, human reviews, or claims of demonstrated multi-agent superiority.

Start with the content model and accurate default diagram, then add visual polish and alternate views. Prioritize a convincing explanation of the system that exists today.
