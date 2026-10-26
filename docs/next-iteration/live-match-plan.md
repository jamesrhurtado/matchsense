# Live-match explanation workflow — implementation plan

## Product decision

MatchSense helps a producer explain a match as it unfolds. A synthetic observation
stream stands in for a live football provider. Past insights and catch-up recaps
support the live experience. Implemented as a local pilot candidate on 24 October 2026. The proposed review-time gate remains unmet; human validation and deployment remain separate. See [verification](../../evals/live-match/verification.md) for measured results and retained failures.

The existing engine already limits evidence to delivered observations, maintains
source state separately from approved copy, supports asynchronous Director/Reviewer
work, streams updates and invalidates corrected explanations. It is not limited
to analysing a complete past match. The current default, however, is a guided,
pausable template-mode replay. New-family real-model smoke tests do not establish
continuous AI readiness. Reuse these systems rather than rebuilding the engine.

## Target experience

1. Producer opens “Start live simulation”; execution mode is visible before start.
2. A four-minute synthetic feed runs continuously at 1×. Reviewing evidence or
   opening an older insight never stops or rewinds the shared match clock.
3. Source-confirmed clock, period and score update independently of AI approval.
4. AI proposes supported explanations asynchronously. Producer sees ready,
   reviewing, unavailable, expired and corrected states with clear next actions.
5. Producer checks evidence and approves an exact revision while play continues.
6. Viewer sees eligible approved overlays, personalized explanations, history
   and catch-up recap. A viewer cannot pause the shared simulation.
7. Feed ends explicitly; final review/history remain available. Restart is a
   deliberate action creating a new session, never an automatic loop.

Keep a separate “Guided walkthrough” for onboarding and a separate template mode
for offline testing. Identify both honestly. Do not label the simulation a real
match broadcast or portray deterministic fallback as successful AI generation.

## Ordered work

| Ticket | Work | Acceptance |
|---|---|---|
| LM01 | Establish session-level live-simulation versus guided modes and execution provenance. Make live simulation the main product entrance; keep training controls under guided mode. | Mode survives refresh/restart; 1× continuous default; guided pauses and seek cannot control a live session. End-of-feed and restart behavior are explicit. |
| LM02 | Audit and complete background ingestion/scheduling. Delivery, opportunity detection and model scheduling must continue independently of any open producer/viewer page. Reuse local delivery and existing transport boundaries. | Close all browsers, reconnect later: clock, delivered observations, attempts and source corrections have advanced correctly. Future observations remain unavailable to tools. |
| LM03 | Connect the complete mixed-event workflow to existing Azure model configuration. Reuse Director/Reviewer, bounded queues, deadlines, canonical rendering and durable outcomes. Add startup/readiness checks and explicit AI-unavailable behavior. | Real-model runs for pass, pressure, shot, goal, recovery and possession; measured calls/usage, abstention, rejection, repair and fallback are visible. No extra agent roles required. No silent switch to templates. |
| LM04 | Producer live desk: useful ordering, relevant incident grouping, review time remaining, clear approve/dismiss controls and distinction between current play and inspected history. Reuse overlay priority/hold policy. | Opening evidence never pauses the match; stale approvals are rejected; reviewing one candidate does not lose another; corrections immediately withdraw affected publication. Source score stays separate. |
| LM05 | Viewer live companion: clear simulated-live status, current match clock, deliberate overlay timing, approved insights and catch-up. Preserve English/Spanish and relevant player/team focus. | All supported families work through approval, display, evidence, focus and recap. Reconnect restores current state without presenting an obsolete overlay as current. |
| LM06 | Add fresh continuous scenarios and failure exercises, then run measured real-model verification. Retain the original regression and report new results separately. | Full 1× runs without seek/pause/auto-approval; late, missing, duplicate and corrected observations; model timeout/rate limit; queue saturation; browser disconnect; API restart and pending-work recovery. Report every opportunity and failure. |
| LM07 | Prepare the live pilot and under-two-minute presentation. Update README and walkthrough around the actual verified execution mode. | Reviewer can distinguish simulation from real feed, AI from fallback, suggestion from approval and live view from history. Record real user results only after participation. Deployment remains separate. |

Dependencies: LM01 → LM02 → LM03 → LM04 → LM05 → LM06 → LM07.
Engineering may reuse independently verified components, but each acceptance gate
must be demonstrated on the assembled live workflow.

## Verification and release gates

- Freeze independent expected opportunities before evaluation. Include all families
  and ordinary play; do not equate every pass or observation with a highlight.
- Run at least 20 varied eligible opportunities at continuous 1×, first one stream,
  then two. Count opportunities, authored scenes and repeated trials separately.
- Measure evidence readiness, scheduling delay, model completion, review time left,
  approval and browser display. Distinguish source time from wall-clock time and
  server clocks from browser clocks. Unknown measurements remain unknown.
- Proposed initial target: at least 95% of eligible opportunities reach a usable
  candidate with at least 15 seconds left for review. Report per-family and pooled
  results, queue failures, latency distribution, actual model/version and estimated
  cost. This is a proposed gate, not achieved performance; expiry policy must be
  explicit before the run and must not be relaxed afterwards to conceal failures.
- Zero unsupported published claims in the reviewed run; corrections must withdraw
  dependent text and recap entries. This does not prove general factual accuracy.
- Preserve stored package hashes, compatibility, original 168-case/594-checkpoint
  regression, meaningful backend/build checks and desktop/mobile browser flows.
- Verify local SQLite path first. Existing Cosmos/Event Hubs adapters and old Azure
  tests do not certify the new workflow; require separate integration verification
  before any authorized deployment. Do not provision resources or spend on model
  evaluation merely by creating this plan; budget the verification run first.

## Scope and demonstration

No real-feed integration, professional video synchronization, xG, tactical-cause
claims, Chaos Index, calibrated difficulty metric or additional Azure services are
needed. The synthetic source is prerecorded; delivery and processing happen live
within the simulation. Training pause/seek is not evidence of AI response speed.

For the pitch, show an uninterrupted excerpt: incoming event → actual AI decision
and trace → evidence → human approval → viewer overlay → Spanish/player view →
catch-up recap. Disclose any accelerated playback, prerecorded footage or editing.
Do not claim participant usefulness, production scale or multi-agent superiority
without the corresponding evidence.

## Reconciliation with the original Chrome research plan

Reviewed directly in the Chrome app on 24 October 2026:
[original research conversation](https://m365.cloud.microsoft/agents/researcher/SYSTEM_ResearcherConsumerGPT.dr_work/conversation/85cfa56d-4df5-4e99-966b-de4b21db69cc).
The report is a design reference, not evidence that its proposed capabilities
exist or that every recommended service/agent is necessary. Current user scope
and supported observations govern implementation.

| Original recommendation | Live iteration decision / acceptance addition |
|---|---|
| Five stages: ingest, interpret, explain, render, personalize | Demonstrate all five on one uninterrupted synthetic stream. LM06 traces one incident from delivery to approved viewer display. |
| Match-story desk chooses what deserves interruption | LM04 ranks supported candidates with explicit reasons, groups related incidents, permits dismiss/suppress and manual selection, and enforces one readable shared overlay at a time. Test competing events, goal preemption, expiry and correction. Do not present every candidate as an important highlight. |
| Metrics respond first; generative reasoning is asynchronous | LM02–03 keep source score/clock and deterministic evidence available while AI runs. An optional deterministic explanation is explicitly labeled and separately approved; a later AI result cannot silently replace approved text or inherit its approval. No model completion is required to update confirmed match state. |
| Evidence graph links trigger, preceding observations, metrics, comparison and provenance | Reuse canonical package/dependency infrastructure; LM04–06 verify exact event IDs, intervals, coverage, revision/hash, scoped comparisons and overlay eligibility. No invented confidence percentages. |
| Studio, casual, analyst and favorite-player outputs | LM05 and LM07 show one producer cue, a plain-language fan explanation, analyst measurements and a relevant player's observed role from the same approved facts; also Spanish. Verify meaningful audience differences rather than only relabeling views. Do not invent off-ball contributions. |
| End-of-match verified recap | LM05 makes a completed-segment recap discoverable when the feed ends, based only on approved valid insights, with current corrected score and links to evidence. Call it a segment recap unless the source explicitly confirms full time. No automatic new match. |
| Purposeful specialized agents and visible recovery | Reuse Director/Reviewer with bounded tools, evidence requests, repair/rejection and traces. Add no scouts without a measured need. LM06 includes a disclosed injected unsupported-claim challenge; never stage it as a spontaneous AI error or claim multi-agent superiority from it. |
| Microsoft platform and observability | Reuse existing Agent Framework/model integration, transport, persistence and trace hooks. Report actual model identity, calls, retries/failures, latency and cost; connect each service to observed behavior. Fabric, hosted agent runtime, speech and vector search remain optional. |
| Seeded, correlated synthetic scenarios and golden evaluation | LM06 uses reproducible coherent observations plus fresh independently authored references, held outside runtime/model access. Validate physical continuity and delivery/correction behavior; authored intent alone does not prove tactical truth. |
| Three proposed metrics / tactical turning-point headline | Intentional adaptation: retain supported Pressure Swing proximity, pass progression/comparison and broader match facts. Chaos Index, calibrated difficulty and tactical causation remain deferred. A visible pressure change can anchor the pitch without claiming intent or a cause of a later goal. |
| Production and ROI measures | LM06 records event-to-metric and candidate/display timing, failures, grounded-reference checks, detection misses and per-segment model cost. LM07 collects real producer acceptance/edit effort, time to usable insight and viewer comprehension; do not substitute automated checks for human usefulness or claim revenue. |
| Under-two-minute functioning demonstration and public delivery | LM07 prepares an honest continuous excerpt with one central story, evidence, audience variants and recap. Public deployment, repository visibility and video publication stay explicit release actions; current local verification does not certify Azure deployment readiness. |

### Revised completion condition

The iteration is complete only when a new reviewer can identify the product as a
simulated live-match explanation desk, watch uninterrupted play, observe an actual
AI attempt, approve a supported explanation before it becomes stale, and see the
correct personalized viewer output and recap. Repeat verification with correction,
model failure and browser disconnect. Preserve failed attempts in the report.
Human usefulness and submission/deployment completion remain separately tracked.
