# WHY/NOW — next iteration: broader match coverage

Prepared 23 October 2026, America/Lima. **Status: implementation backlog authorized for planning; no features implemented by this document.** Product owner: James. Engineering, QA and reviewer assignments remain open.

## 1. Outcome and scope decision

Build a viewer companion that helps someone follow a varied football segment through goals, shots, possession and changes of control, alongside existing pass explanations. A first-time user should understand what happened and be able to inspect the evidence supporting the selected explanation.

James reports that first-time users found the pass-only experience confusing and wanted other match information. This is the motivation for the iteration, not a completed formal user study or proof that a broader product will succeed. Validate the result with real users before claiming improved comprehension or usefulness.

**Required for this iteration:** match clock/period and confirmed score; goal stories; shot stories; a defined possession overview; possession-change/recovery stories; a mixed-event approved timeline and recap; evidence, English/Spanish, relevant player/team focus, corrections and producer approval across those families. Retain existing passes as one supported category.

**Subsequent backlog:** longer connected attacking sequences, set pieces, fouls/cards and substitutions. A tackle explicitly observed in the new fixture can support recovery evidence; standalone tackle analysis is subsequent work. xG, tactical intent and claims about what caused a result remain separate research. Real vendor-feed integration, full-match completeness, external TV synchronization and new infrastructure are outside this iteration.

This scope promotes the original staged shot/recovery extensions and the later conditional event-family expansion into the next iteration's required backlog. It supersedes earlier deferral of **basic shots and broader event coverage** for this work. It does not promote xG, remove correctness gates, or mark previous operational/research gaps complete. Any reduction in the required families must be recorded with James's scope decision, rather than silently omitted from a release.

## 2. Starting point and planning history

The original Obsidian project brief includes shots and possession changes in synthetic data, while centering its demo on a pass. Its dataset plan calls for shots/outcomes and tackles/recoveries after the first working slice, including score changes when a goal outcome arrives. Later repository plans focused on deeper pass explanations and deferred expansion. See [the historical review](match-coverage-proposal.md).

Reuse the local 0.5.0 candidate's deterministic metrics, evidence hashes, bounded workflow, exact-revision approvals, immutable packages, correction handling, SQLite/Cosmos adapters, viewer variants, SSE and approved history. Source checkpoint at planning: `2d51551`; check the actual baseline before implementation and record it in the delivery log.

Important coupling to remove deliberately:

- `engine/contracts.py` accepts pass start/resolution, possession change and play-state change; it has no shot/goal/recovery event types. Initial score already exists in match metadata.
- `services/api/main.py::materialize_all` enumerates pass metrics, keys stories by pass, and uses pass-retention confirmation for scheduling/expiry.
- `EvidenceTools`, narrative rendering and structured model tools are pass-focused.
- `engine/recap.py` assumes passer/receiver metrics and groups at most three distinct signatures. Reusing it unchanged would fail or distort broader coverage.
- Producer/viewer evidence components and controls assume pass stages and roles in several places.

## 3. Product behavior and factual contracts

These are proposed implementation definitions, not general football standards. Freeze them with examples in ticket MC01 before writing generation prompts. Source observations remain authoritative; a model never invents an event, score, outcome or measurement.

### Match state, goals and shots

Use explicit period state and the existing segment initial score. Process observations only at their availability cutoff. Match time, replay navigation time and processing wall time must stay distinct.

Add typed `shot_started`, `shot_resolved` and `goal_status_changed` observations. A shot has a stable ID, team, verified actor or explicit unknown, occurrence time, optional valid location and a typed resolution: goal, saved, blocked, off-target, or unknown. Agree the precise outcome vocabulary in MC01. Never infer a save, scorer, assist or goal from ball coordinates alone.

Goal status has a stable goal ID, scoring team, nullable scorer, optional linked shot ID, and status pending/confirmed/cancelled. Permit an explicitly attributed own goal and a goal without a linked shot; do not force an invented shooter. Pending/cancelled status is distinct from producer approval. One confirmed goal increments the correct team's score once; cancellation removes it once. Recompute from initial state and latest available goal revisions, rather than blindly incrementing deliveries. A repeated message never adds another goal. A shot resolution labelled goal without a confirmed goal record is incomplete evidence and cannot independently change the score.

A shot start supports only an attempt-in-progress observation. Generate its outcome story once resolution is available; a goal story requires confirmation. Group linked shot/goal stories as one viewer incident, retaining identities and audit history. If a previously approved shot story changes after goal confirmation, its replacement needs approval; do not silently rewrite it.

**Public state decision:** clock, period, source-confirmed score and a source-status label are basic match state and update without editorial approval. Explanatory text, event-story cards, overlays and recap entries require exact producer approval. Unapproved shot details, candidate prose and diagnostics remain producer-only. Label these boundaries clearly: a score being confirmed does not mean its explanation has been approved. Score correction is mandatory even if a producer retracts its story. This is an explicit projection policy to implement and test, not an assumption about existing behavior.

### Possession overview

First version: a trailing **60 seconds of observed replay coverage**, refreshed for producer candidates on fixed **15-second replay boundaries**. Display the actual start/end and call it a segment window. Do not imply a full-match statistic. Defer comparison to a previous window unless both windows are independently available and defined.

Integrate team possession by elapsed time, never by counting frames. The declared team can retain possession during a pass even when no player controls the ball. Dead-ball and loose-ball intervals are separate; unknown observations and gaps over the existing 200 ms continuity limit do not inherit possession across the gap. Freeze the interval-end treatment and all ball-state mappings in MC01.

For team percentages, denominator = known in-play time assigned to either team. Exclude dead/loose/unknown time from that denominator and display those durations plus coverage. Coverage = known in-play assignment divided by in-play time that is assigned or unknown; report dead/loose time separately. If the in-play state is itself unknown, count that duration as unknown in the coverage denominator. Require at least **30 seconds of assigned time** and **95% coverage** before offering percentages; otherwise show insufficient evidence. These are provisional product thresholds to test, not validated football significance rules.

Store each candidate as an immutable window snapshot with its source dependencies. An approved 60-second overview must not silently become a new rolling overview. A new window is a new candidate; a correction to the same window creates a revision and invalidates its old approval. Keep the latest approved overview visible with its interval; availability does not imply recency. Automatic percentages outside approval are not part of this iteration.

### Possession changes, recoveries and turnovers

Use existing possession transitions plus typed `ball_recovered` observations with explicit cause where supported. A change from team A to B is one incident, not two independent alerts for a turnover and a recovery. A pass interception and its matching possession transition must not double-count it.

Attribute a recovery to a player only when the source supports that role. Treat restarts separately. When the source supports only a team control change, say that; do not infer a tackle or interception from proximity. Later sustained-possession wording requires a continuous **three-second** confirmation interval with the same coverage rules as retained-possession evidence. A subsequent loss prevents that clause but does not erase the observed recovery.

### Stories, publication and selection

Use an event-neutral story reference: family, stable subject/incident IDs, team, verified participant roles, occurrence time, evidence-ready time, source cutoff, evidence hash and versioned dependencies. Keep old story IDs and package readers intact. New IDs must be deterministic under retries; pass/shot/goal IDs may not collide.

All families share reviewed candidate → exact approval → publication → expiry/history → retraction. Corrections revoke only affected approvals and derived recaps. New narrative schema readers must coexist with saved v1–v4 packages; choose a new schema version explicitly in MC02 and never reinterpret old hashes. Preserve restart recovery and SQLite/Cosmos parity.

For new event stories, propose a **30-second live publication window from evidence-ready replay time**; freeze per-family exceptions in MC01. A possession snapshot is live-eligible until the next 15-second sampling boundary. Historical review/approval needs an explicit archive-only path: it may add to approved history/recap but never revive an expired overlay. Avoid inheriting pass-specific expiry fields. Pending goals are not eligible confirmed-goal stories. Clock jumps are visible replay navigation, not a latency demonstration.

Initial selection is transparent and deterministic: eligible confirmed goals, resolved shots, verified recoveries/control changes, possession snapshots, then eligible pass stories. Sort within each family by occurrence time and stable ID. Apply an incident deduplication key and allow producer override. Offer at most one possession candidate per sampling boundary and replace its unreviewed predecessor in the active queue while retaining its disposition. Record deferred/expired candidates so queue limits do not hide failures. This order is a product rule to evaluate, not a claim of tactical importance.

The shared overlay shows one eligible approved story with an inspectable selection reason. Viewer history remains chronological and filterable by family/team/player. Personal focus uses family-specific roles: shooter, scorer, recovering player or existing pass roles; team-only possession is not falsely attributed to a favorite player.

Recap reads exact approved revisions only. Show a score header from public match state, clearly separate from editorial entries. Deduplicate shot/goal incidents and similar possession windows; a family label alone must not collapse distinct goals. Target up to five incident summaries, prioritize approved goals, then select varied remaining incidents with documented ordering. Include a link/count for the complete approved timeline when truncated. A family with no approved story stays absent; never manufacture variety or call a segment recap a full-match result.

## 4. Prioritized engineering backlog

Every MC ticket below is required for this iteration. Estimates are initial hands-on engineering ranges, excluding recruitment, external review, paid model runs and deployment waiting. Owners are roles to assign, not people already allocated.

| ID | Deliverable | Owner | Dependencies | Hours |
|---|---|---|---|---:|
| MC01 | Freeze definitions, publication policy and reference examples | Product + backend + football reviewer | Baseline audit | 6–10 |
| MC02 | Versioned event/story contracts and compatible persistence | Backend | MC01 | 12–18 |
| MC03 | Varied generator, fixtures and independent expected outcomes | Data/QA | MC02 contract | 10–16 |
| MC04 | Goal/shot projections and corrected score | Backend | MC02; MC03 fixtures | 8–14 |
| MC05 | Possession integration and recovery/control-change detectors | Backend | MC02; MC03 fixtures | 10–16 |
| MC06 | Generalized evidence, rendering and bounded agent workflow | Backend/AI | MC04, MC05 | 10–16 |
| MC07 | Mixed-event scheduling, approvals and correction propagation | Backend | MC02, MC06 | 12–20 |
| MC08 | Producer/viewer coverage, evidence, timeline and recap | Frontend/backend | MC02 fixture interface; MC06–07 integration | 14–22 |
| MC09 | Regression, compatibility, continuous playback and failure checks | QA/backend | MC03–08 | 10–16 |
| MC10 | User pilot, corrections, documentation and release handoff | Product/QA/frontend | MC08–09 | 8–12 |

Total **100–160 engineering hours**, plus a **20% integration allowance: 120–192 hours**. Budget reviewer/research participation separately. At 30 focused engineering hours per week, expect roughly **4–7 weeks** for one engineer, subject to findings; this is an estimate, not a delivery promise. Re-estimate after MC02/03. Preserve the required event breadth if capacity changes: sequence delivery across milestones instead of silently releasing only more pass polish.

### MC01 — definitions and reference acceptance

Write `docs/match-events.md` with typed examples, clock/status rules, ownership, unsupported claims and all thresholds above. Review at least two positive, two negative and one correction example per family. Include goal cancellation, own goal/unknown scorer, unsuccessful attempt, loose-ball recovery, ordinary restart and incomplete possession. Record football-reviewer disagreements and any unavailable review explicitly. Exit: the same example has one agreed state, narrative eligibility and expected viewer projection.

### MC02 — contracts and storage

Touch `engine/contracts.py`, schema exports in `data/schemas/`, catalogue loading, `engine/repository.py`, `engine/cloud_repository.py` and transport serialization. Add typed event variants, generic participant roles, incident linking, family-specific evidence and package versioning. Reuse the existing observation envelope rather than building a second ingestion system. Invalid combinations and unsupported versions fail clearly; unavailable outcomes remain unknown. Include period starts/ends for clock context, without adding substitutes/cards in this slice.

Exit: original runtime fixtures and approved package readers still load unchanged; new examples validate and round-trip through both repository adapters; duplicate/reordered/corrected deliveries produce the same projection. Publish a compatibility/rollback matrix. An old binary that cannot read new sessions is not a valid rollback by itself: route/isolate those sessions or retain a compatible rollback build.

### MC03 — data that exercises the product

Extend `simulator/`, `engine/catalog.py` integration and observation-only runtime fixtures. Build a varied 3–5 minute discovery replay with a recovery, pass sequence, non-goal shot, goal and possession windows. No final whistle or full-match claim. Add a separate correction replay and at least **12 independently specified evaluation scenarios** spanning new families, missing data and timing faults. These are a proposed minimum, not existing test results or independent real-match validation.

A QA/reviewer-authored outcome table must be independent of production metric functions. Keep source labels and future trajectories outside runtime access. Preserve current 173 replay entries and original regression references; add new fixtures rather than altering the old test baseline. Exit: generation is reproducible, physical/temporal checks pass, and every new predicate has a positive, negative and correction checkpoint.

### MC04 — score and shots

Implement a pure cutoff-aware match projection and shot/goal fact builders, preferably in focused new `engine/match_state.py` and `engine/event_metrics.py` modules. Use source-confirmed event status, not model text. Exit: shot start never reveals its future outcome; unknown remains unknown; a confirmed goal changes score once; duplicates, cancellation, reordered delivery, corrected team/scorer, own goal and restart reproduce exact expected states. Score works without a model or a producer-approved story.

### MC05 — possession and recoveries

Implement interval accounting and incident-linked control-change facts with unit/coverage metadata. Exit: irregular frame cadence, gaps, in-flight team possession, loose/dead time, period/window boundaries and delayed corrections match hand-worked duration references. Percentages are withheld below minimum coverage/duration; raw values determine calculations before display rounding. A recovery followed by immediate loss can be described accurately without a sustained-possession clause. One interception/control transition yields one incident.

### MC06 — evidence and text across families

Extend `EvidenceTools` and the claim/renderer modules without accepting arbitrary predicates. Provide family-specific evidence retrieval, source cutoff and role bindings. Add deterministic English/Spanish simple/detail variants first. Then extend `engine/structured_workflow.py` and Foundry tools to select/order only supported new facts within the existing call/deadline limits; retain labelled template fallback and abstention. Do not add agent roles for breadth.

Exit: a deliberately permissive fake reviewer cannot publish invented scores, goals, assists, actor roles or possession denominators. Unknown actor variants remain valid. Both languages preserve state, units, roles and qualifications. Use zero-call offline checks first; model-specific verification is required before claiming AI support for these families. Record any paid run separately with actual usage and existing authorization requirements.

### MC07 — lifecycle and scheduling

Refactor pass-specific materialization into a family-dispatch path, reusing shared approval/accounting rather than duplicating it for every family. Update `engine/outcomes.py`, `engine/dispositions.py` and API snapshot/SSE/review paths where necessary. Freeze evidence-ready timestamps, expiry and incident grouping. Add the explicit archive-only approval path and protected producer projection.

Exit: duplicate requests are idempotent; a job completed against old evidence cannot commit; provider failure cannot fabricate facts; review rejection/abstention/expiry/capacity deferral is recorded. A new shot/goal cannot starve forever behind repeated possession snapshots. Test correction while a model job or approval request is in flight, retraction while recap is open, reconnect, process restart and unrelated-story isolation. Public score stays source-correct through every editorial action.

### MC08 — actual producer and viewer utility

Update shared types in `apps/web/lib/api.ts`, existing hooks, `match-desk.tsx`, audience/review panels, evidence components and `engine/recap.py`. Add event-family labels, family filters, match state, approved possession window, mixed timeline and recap. Evidence must fit its family: shot location/outcome, goal/score transition, possession duration/coverage, or recovery/control transition. Preserve the pass replay where relevant; do not fabricate tracking around events with missing positions.

Provide a plainly labelled producer-demo entrance and short help for the access key. Explain the synthetic segment, available event categories and difference between source-confirmed state and approved explanations. Keep viewers free of producer credentials. Design from fixtures before integration; follow local frontend instructions and review desktop/phone layout when implementing.

Exit: a first-time viewer can locate the score, a non-goal attempt, possession window and recovery without knowing technical terms. Filters and language/focus changes never reveal unapproved stories. Goal/shot grouping has one incident summary with access to the source details. Timeline navigation does not alter another viewer's selection or the shared overlay.

### MC09 — integrated evidence

Run appropriate backend tests, type/build checks and real browser flows. Existing Makefile checks include `make test`, `make data-check`, `make evaluate`, `make synthetic-evaluate`, and `make web-build`; use the web typecheck and Playwright suite with the correct running servers. Add a new mixed-event evaluation command/manifest in MC03/09 rather than assuming the pass-only suite covers new event types. Preserve original regression expectations and report new results separately.

Required browser flows: goal approval; non-goal shot; recovery; approved possession snapshot; mixed recap; score correction; narrative invalidation/reapproval; duplicate incident grouping; Spanish and actor/team focus; mobile evidence; live stream reconnect; archived navigation. Local mock tests do not prove Azure persistence or model behavior. Verify the selected release mode and label untested modes.

Measure at least **20 varied opportunities** during continuous 1× playback, including a new-family burst and two simultaneous sessions. Report family, evidence-ready time, queue wait, candidate time, review time available, deferrals, expiry, provider usage and missing telemetry. Target at least **90% of live opportunities ready with 10 seconds left to review** under the configured test load; this is a provisional acceptance target, not production P95. Report all attempted opportunities, not only produced packages. Fix measured misses or declare a smaller supported operating load before the pilot.

### MC10 — user evidence and reviewable release

Run a formative pilot with **5–8 first-time viewers**, plus **1–2 football-aware producer/reviewer participants** where available. James owns recruitment; assign a facilitator before scheduling. Include people who need plain-language football explanations. Do not describe the owner's feedback as a completed recruited study. Capture consent and anonymous task-level notes; use existing study materials as a starting point.

Counterbalance the current pass-only baseline and the varied candidate, with scripted answers and the same amount of navigation help. Ask users to find the current score, distinguish a shot from a goal, identify a possession change, interpret the possession window and find the source of an explanation. Ask which information helped and what was missing; include a normal-play interval to check alert overload. Producers review supported facts and reject misleading candidates.

Provisional gate: at least **80% of viewer task attempts succeed without facilitator rescue**, **zero unresolved critical score/outcome/approval misconceptions**, and at least **70% of reviewed candidate stories accepted as useful and supported without substantive editing**. Show raw counts, individual failures and sample limits. These thresholds guide corrections; small-sample results do not establish broad football accuracy or market demand. If recruitment is unavailable, label the build engineering-ready and leave user validation open.

Update `README.md`, `docs/metrics.md`, `docs/incoming-feed.md`, `docs/demo.md`, the presenter/friend scripts and the user-study record to match the actual release. Replace the pass-only pitch with the varied verified replay once it exists. Present outcome/sequence facts without claiming a pass caused a goal. Rehearse the exact build; keep local template narration distinct from actual model execution.

## 5. Milestones and release gate

| Milestone | Tickets | Reviewable result | Exit evidence |
|---|---|---|---|
| A — foundation | MC01–03 | Frozen definitions, new schema and mixed fixture; old app still works | Example table, compatibility matrix, independent reference checkpoints |
| B — complete factual backend | MC04–07 | Every required family yields supported candidates with shared approval/correction behavior | Per-family tests, corrected-score replay, lifecycle/accounting checks |
| C — usable mixed-event companion | MC08–09 | Desktop/phone producer and viewer flows, varied timeline/recap | Browser evidence and continuous-play report |
| D — next iteration ready for users | MC10 | Corrected product and truthful demo/handoff | Pilot findings or explicit engineering-only status; release checklist |

Release only when required families work end to end, compatibility passes, no unapproved narrative leaks, score corrections reconcile, unknown data stays unknown, and critical user misconceptions are resolved. Maintain source-confirmed state even when model work is unavailable. Zero-call template operation remains a supported demo mode; it must be labelled.

Deployment is a separate recorded step against the selected environment; a local implementation is not a deployed release. Do not silently change paid resources or the current hosted build as a documentation task. For the new family feature flag, default off until compatibility checks pass; enable a disposable local pilot session first and retain a compatible rollback release. Never mutate old approved packages to make a demonstration look updated.

## 6. Delivery accounting and subsequent backlog

Record each MC ticket as **planned → in progress → implemented → verified → deployed**, with commit, test artifact, supported mode and open limitation. Assign the engineering/reviewer roles during kickoff. Add scope changes and unresolved evidence to `decision-log.md`; a checkbox or an AI completion statement is not delivery evidence.

Subsequent candidates remain separate tickets, not hidden obligations of MC01–10:

| ID | Candidate | Prerequisite |
|---|---|---|
| MX01 | Connected buildup/carries across events | Stable event links, sequence boundaries and user demand |
| MX02 | Corners, free kicks and penalties as event families | Restart contracts and outcome evidence |
| MX03 | Fouls/cards/substitutions | Authoritative status/attribution and lineup changes |
| MX04 | Real incoming vendor feed | Declared-unit adapter, completeness/correction contract and independent integration test |
| MX05 | xG or tactical interpretations | Separate measured model/metric definition and independent football validation |

## References

- [Coverage proposal and historical findings](match-coverage-proposal.md)
- [Previous improvement plan](grand-prize-90-plus-plan.md)
- [Earlier engineering tickets](engineering-backlog.md)
- [Implementation record](decision-log.md)
- [Current metrics](../metrics.md), [incoming observations](../incoming-feed.md), [user-study materials](../user-study.md)
