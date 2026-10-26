# Engineering backlog — next submission iteration

> **Active next-iteration backlog:** [MC01–MC10: broader match coverage](match-coverage-implementation-plan.md). James requested this plan on 23 October 2026 to address first-use confusion about pass-only coverage. It promotes basic goals/shots, possession overview and recovery/control-change stories; xG remains separate research. The tickets below retain their historical status and must not be counted as newly delivered coverage.

This is the original ticket specification. Current delivery status, explicit deferrals and outstanding acceptance evidence are tracked in [the implementation record](decision-log.md); several core tickets have now been implemented. Effort is hands-on engineering hours, excluding waiting for people or cloud jobs. The core totals roughly 60–90 h plus a 10 h integration buffer. C03/N01/L02 are conditional and add 15–23 h. Engineers should update estimates after the discovery gates.

## Ticket index

| ID | Priority | Deliverable | Owner | Depends on | Estimate |
|---|---|---|---|---|---:|
| R01 | P0 | Definitions and research decisions | Backend + product | Existing audit | 4–6 h |
| F01 | P0 | Correct wording and actor attribution | Backend | R01a | 2–3 h |
| O01 | P0 | Complete workflow outcomes and timings | Backend | Baseline preserved | 5–7 h |
| C01 | P0 | Versioned claim/plan/realization contract | Backend/AI | R01, F01 | 7–10 h |
| E01 | P0 | Fresh evaluation parents and fair harness | Evaluation | O01; C01 interface | 6–8 h |
| C02 | P0 in recommended scope | Exact spatial context | Backend/data | C01 | 3–5 h |
| A01 | P0 | Updated Director and Claim Reviewer | AI | C01; C02 if included | 6–9 h |
| A02 | P0 | Agent architecture experiment | Evaluation/AI | E01, A01 | 3–5 h |
| U01 | P0 | Explanation-first audience experience | Frontend | C01 fixture | 4–6 h |
| P01 | P1, high value | Relevant player/team history and trails | Frontend/backend | C01, U01 | 3–5 h |
| C03 | Conditional P1 | Actual prior-pass comparison | Backend/data | R01b, C02, E01 | 6–9 h |
| N01 | Conditional P1 | Editorial priority and concise recap | Backend/frontend | C01, P01, R01e | 4–6 h |
| L01 | P0 | Continuous replay timing and capacity | Backend/QA | O01, A02 | 4–6 h |
| L02 | Conditional P1 | Explicit factual-first candidate path | Backend/frontend | L01 failure analysis | 5–8 h |
| E02 | P0 | Final evaluation and decision report | Evaluation/QA | A02, selected features frozen | 4–6 h |
| U02 | P0 | Formative user evidence | Product/frontend | U01; stable candidate | 2–3 h engineering + 6–8 h research |
| Q01 | P0 | Integration, compatibility and deployment gate | QA/backend | Selected tickets, E02 | 4–6 h |
| S01 | P0 | Public source, demo and submission evidence | Release/product | Q01; publication prep starts early | 3–5 h engineering + 2–4 h recording |

P0 means a release commitment, not a requirement to implement every optional variant. Scope changes must be explicit in the decision log. The one-engineer scope in [README](README.md) may defer C02/P01 while preserving meaningful explanation and evaluation on existing facts.

## R01 — Freeze definitions before prompt changes

**Problem:** richer wording can exceed what the current observations establish.

**Work:** conduct the research spikes in [research-decisions](research-decisions.md), record the allowed vocabulary, define subject/time/source scope for each claim, and review representative English/Spanish examples. Inspect how much prior history the current data actually provides. Prototype output should be evaluated as text/evidence pairs before committing to UI or agent contracts.

**Acceptance:** every proposed metric has an operational definition, abstention rule, at least two positive and two negative examples, and a named owner for review. Unsupported tactical labels are removed. An unavailable football reviewer is recorded as an evidence limitation, not implied approval.

**Files:** `docs/metrics.md`, `docs/next-iteration/decision-log.md` (new during implementation); proposed claim glossary.

## F01 — Correct receiver attribution and claim language

**Problem:** receiver variants say the receiver kept possession, although the metric establishes team possession. Generic labels can imply more football meaning than the geometry establishes.

**Work:** separate reception by the player from retention by the team in English and Spanish, including model instructions, fallback text, focused variants and demo narration. Label proximity and longitudinal bypass precisely. Remove generic “notable” assertions without a supported rationale.

**Acceptance tests:** a successful receiver passes onward during the three-second window while the team retains possession; wording credits reception only. A later team turnover prevents a retention claim. Both languages preserve actor/polarity/interval meaning. Existing numerical thresholds remain unchanged.

**Files:** `engine/workflow.py`, `engine/foundry_workflow.py`, `tests/test_foundry.py`, new focused semantic tests; `docs/metrics.md` and demo copy.

**Compatibility:** old packages remain immutable. New sessions use corrected generation. Identify any existing approved packages requiring withdrawal as a separate audited operation; never silently edit previously approved text. The submission uses a fresh verified session.

## O01 — Account for every workflow outcome

**Problem:** package-only reports omit abstentions/rejections and cannot distinguish queue delay from model work.

**Work:** introduce a durable `WorkflowOutcome` stored independently of packages in SQLite/Cosmos. Persist `scheduled`/`started` before model work; finalize `produced`, `abstained`, `rejected`, `fallback`, `failed`, `cancelled`, `stale` or `interrupted`. Include run/attempt IDs, source cutoff/hash, selected story, model/deployment/version, prompt/tool/renderer versions, calls, tokens, usage completeness, fallback/error category and package reference. Use existing storage resources.

Capture wall-clock `evidence_durable`, `job_enqueued`, `job_started`, `candidate_ready`, `approval_received`, `overlay_observed`; retain replay timestamps separately. Use monotonic durations within a process; document clock synchronization for comparisons between server and browser. Provider calls that fail without usage remain unknown. Record interruption after restart even when exact provider charges are unavailable.

**Acceptance:** fixture accounting reconciles every provider invocation for success, abstention, rejection, malformed response, timeout, cancellation, stale completion and restart. Repeated terminal writes are idempotent. No unknown consumption becomes zero. Protected outcomes contain no credentials; public summaries use sanitized aggregates. Failure to persist a run prevents new billable work until the condition is visible/resolved.

**Files:** `engine/contracts.py`, `engine/foundry_workflow.py`, repositories, `services/api/main.py`, `scripts/cloud_multi_smoke.py`; new `engine/outcomes.py` if useful. Avoid an unrelated repository rewrite.

## C01 — Bind claims to exact narrative meaning

**Problem:** current variants cite all four claims without identifying which factual clause each one supports. Free-form false statements can pass lexical/numeric checks.

**Work:** implement the typed contracts in [agent evaluation](agent-evaluation.md). Each clause binds its predicate, entity roles, values, time and comparator to supported facts. Permit only explicit relations such as sequence, conjunction or a verified numerical comparison; prohibit causal/intent/line-break/goal relations without matching evidence types. Names, numbers, units and mandatory qualifications resolve through deterministic rendering. Unknown predicates, missing references, contradictory polarity and unsupported audience focus fail validation even if a model reviewer approves.

Validate the rendered text and its provenance together; do not attach a valid claim ID to arbitrary prose. Model-selected lexical forms must be allowlisted or independently checked against a supported grammar. A short, useful selected fact is preferable to a generic introduction. Detail views must not automatically claim every fact was present in the simple sentence.

**Compatibility:** use versioned package readers (legacy 1.0.0 plus a deliberate v2 version), update JSON Schemas, and preserve exact hashing. Approval references the complete realized package, schema and evidence version. Read old approvals unchanged; new versions require approval. If old application code cannot read v2 documents, isolate new sessions or retain a dual-reader rollback release. Never assume rolling back the container alone restores compatibility.

**Acceptance:** replay the offline contradiction probes against the new contract with a deliberately permissive fake reviewer; both must be blocked or rendered into supported content. Cover wrong actor, negated retention, wrong unit, post-reception/pass distance confusion, false comparison denominator, untranslated roles and unknown IDs. Source correction affects every dependent claim and only its dependent stories. Existing publication/retraction/expiry tests stay green.

**Files:** `engine/contracts.py`, `data/schemas/`, `engine/workflow.py`, `engine/foundry_workflow.py`; add `engine/claims.py` / `engine/narrative.py` if needed; repository compatibility tests.

## E01 — Build a fair evaluation harness before tuning

**Work:** implement [evaluation-plan](evaluation-plan.md). Preserve baseline commit and run manifests; add fresh structural parents, developer-visible examples, and a separately sealed final split. Implement adapters for structured templates, strong single agent and the new workflow. Keep the legacy flow as a historical anchor, explicitly noting its different contract.

**Acceptance:** one command can run the offline subset; a separate explicit option enables a bounded model run. Every attempted case appears in the result, including no-story and failed cases. Seed/reference/hidden labels cannot reach the runtime tools. All arms receive equivalent allowed observations, tools, deterministic facts and renderer for the architecture comparison. Human raters receive randomized outputs without arm labels. Dry-run cost/call limits are visible before model execution.

**Files:** `evals/agentic/` (new adapters, manifest, grader, report), `simulator/` new parents, offline-only reference data; `tests/test_agentic_evaluation.py`. Do not extend `evals/synthetic.py` in a way that mixes template regression with AI evaluation claims.

## C02 — Add spatial facts that make the moment concrete

**Work:** compute signed forward pass displacement from successful release/reception endpoints, distinct from post-reception continuation. Use `attack_sign * (receive_x - release_x)`; display rounding follows raw comparisons. Normalize pitch position to attacking direction; define thirds on actual pitch length `L`: `[0,L/3)`, `[L/3,2L/3)`, `[2L/3,L]`. Classify the observed reception location. An exact-boundary endpoint belongs to the more advanced third by this definition. Out-of-bounds data is invalid, not clamped into a favorable claim.

Say “received in the attacking third” where supported. Do not label all such receptions “final-third entries”; that requires additional start/possession semantics. Retain current eligibility initially so this ticket does not silently change detector precision/recall.

**Acceptance:** mirrored directions produce equivalent normalized facts; endpoints immediately below/at a third boundary behave as specified; unsuccessful pass has no successful reception claim; missing outcome abstains; correction invalidates source dependencies. Simple and detailed views distinguish forward pass displacement from the subsequent team progression.

**Files:** `engine/core.py`, claim builder, schema export, `docs/metrics.md`, generator/evaluation reference cases.

## A01 — Give the agents a consequential, bounded job

**Work:** update Analyst + Editor into Story Director, and Reviewer into Claim Reviewer as specified in [agent evaluation](agent-evaluation.md). Director chooses angle/claim order/audience emphasis; Reviewer checks the final package against independent facts. Proposals may request a bounded tool result or abstain. Return actionable per-clause verdicts. Final repaired output must be reviewed again.

Use a short relevant context instead of the entire roster where possible. Do not strip metadata required for disambiguation, team membership or duplicate names. Tool requests are enforced server-side, independent of model instructions. The pipeline retains deterministic source gates and producer publication authority.

**Acceptance:** actual trace demonstrates at least one useful content decision and one legitimate correction/abstention on a labeled challenge case. No staged challenge is described as a spontaneous model error. Tests cover repeated evidence requests, invalid IDs, future windows, unavailable history, contradictory producer text, injection in names/proposals, call/deadline exhaustion and safe fallback. Current controls and deployment model remain available for comparison.

**Files:** `engine/foundry_workflow.py` (split role prompts/state transitions into focused modules if helpful), tools, provider adapter tests, protected diagnostics UI.

## A02 — Select the architecture by measured results

**Work:** run the discovery comparison: updated single agent vs two-role workflow; evaluate a separate Audience Composer only if output quality indicates a specific composition problem. Keep the same model/version and supported information. Compare factual usefulness, correction behavior, latency, calls and total tokens. Run developer-set ablations for context availability and final reviewer contribution; removed reviewers are never used to bypass production approval.

**Acceptance:** write an architecture decision with all results, examples, rejected options and limitations. Separate the effect of new claims/tools from the effect of role separation. Choose the smallest configuration meeting quality and timing goals. Inconclusive benefit must be described as inconclusive.

**Files:** `evals/agentic/`, `docs/architecture.md`, `docs/next-iteration/decision-log.md`.

## U01 — Make explanation and evidence visible immediately

**Work:** show a concise supported explanation beside the pitch on desktop and above/alongside a compact pitch on mobile. Keep `Show why` visible. Casual mode uses one or two short sentences and focused visual annotations; analyst mode exposes operands, windows, coverage, comparisons and limitations. Show the observed sequence in stages: before release → pass → reception/continuation. Distinguish source-backed facts, proposed wording, producer approval, live display and archive states in plain language.

Trace UI should summarize the selected claim, requested evidence, reviewer objection, final decision and measured timing; detailed technical entries can expand. Display actual fallback/abstention states accurately. Keep live clock running during evidence replay. Full interface translation is optional; translated football copy and recap must be consistent.

**Acceptance:** at 1366×768 and 390×844, explanation and primary evidence action are discoverable without scrolling past a full-height pitch; no overflow; keyboard selection and visible focus work; status is not encoded only by color. Old/new audience comparisons preserve the same evidence and approval. The three-stage replay never shows observations beyond the selected evidence cutoff.

**Files:** `apps/web/components/match-desk.tsx`, `pitch.tsx`, `lib/api.ts`, component CSS and browser tests. Read `apps/web/AGENTS.md` and installed Next.js guidance before editing. Extract focused components/hooks rather than adding more dense inline state handling.

## P01 — Make player selection affect relevant content

**Work:** filter/reorder already approved story history by verified passer/receiver involvement or possession-team membership. Display observed movement during the selected evidence interval, reception location and exact role. Include a clear “No approved involvement in this interval” state and an easy Whole play return. The shared broadcast overlay remains independent of personal selection.

**Acceptance:** unrelated nearby players gain no invented role; duplicate names remain disambiguated by ID/team; archived approval is visible and retractable; retracting a relevant moment removes it from the filtered history and recap. Trail sampling respects source availability and does not infer unseen motion. No model invocation occurs when a viewer changes focus.

**Files:** contribution tool, approved snapshot projection, `AudienceControls`, `StoryPicker`, `Pitch`, recap view; browser race/retraction tests.

## C03 — Implement real bounded previous-pass context (conditional)

**Work:** expose `get_recent_pass_context` returning the last three valid previous completed passes for the same team/period whose resolution precedes the current release and falls within a 120 s lookback. All their observations must be available by the frozen investigation cutoff. Exclude the current pass and deduplicate corrected/retransmitted events. Return pass IDs, raw forward displacement, times, sample count, exact comparison and source IDs. Fewer than three returns `insufficient_history` with a reason. Keep raw-position tools bounded; use a separate aggregate tool instead of silently expanding a 15 s raw scan to 120 s.

The allowed initial statement is “farther forward than each of the previous three completed passes by this team in this replay,” only if strictly greater than all three raw values. For ties or mixed values, choose a precise numeric comparison or omit it. No percentile, superiority probability or match-wide ranking.

**Acceptance:** same current pass with two distinct past histories changes the comparison correctly; two prior passes abstain; future/late/cross-period/opponent passes do not leak; changes to historical comparator evidence invalidate dependent packages and recaps even when current-pass metrics are unchanged. Freeze the comparator set per package; do not recalculate archived narratives against later events.

**Files:** new context calculator, `EvidenceTools`, claim dependency hashing, `materialize_all`, new generator parents. **Stop:** defer if reference cases or source invalidation cannot be completed by Oct 24.

## N01 — Improve editorial selection and recap (conditional)

**Work:** start with a deterministic recommendation among eligible stories, explaining ordering by supported distinctiveness, novelty against recently displayed claims and remaining display time. Define tie-breaks, deduplication and a configurable cooldown after display. The queue still exposes suppressed recommendations and supports audited producer override; a recommendation is never publication.

Recap selects up to three distinct currently approved moments, with chronology, role-aware text and evidence links. Title remains Match so far for partial replay. Prefer concise claim selection over adding a recap model. Recompute dependencies when approval, evidence or selection changes.

**Acceptance:** repeated equivalent stories do not crowd out distinct supported moments; ties deterministic; expired stories cannot revive overlays; producer override respects eligibility; retraction removes the story and any derived recap comparison. R01e must show usefulness over chronological ordering. **Fallback:** keep chronological approved history and current factual recap.

## L01 — Measure and improve continuous-play behavior

**Work:** profile continuous 1× replay without pauses/seeks at one and two active streams. Use timestamped outcomes to locate ingestion, queue, calculation, model and UI delays. Prioritize shorter relevant prompts, removing unnecessary serial handoffs, reusable projections/claim calculations and active-session scheduling. Inspect the current publisher's scan of all historical sessions before expanding test load. Do not claim horizontal scalability from one replica.

**Acceptance:** report every eligible candidate, including ones never queued, missed deadlines and all fallback modes. Aim for P95 evidence-durable→candidate ≤10 s at one stream and ≥90% eligible stories ready with at least 10 s left. Quantify two-stream results separately; do not exclude cold starts/overload silently. A single-stream target failure triggers a documented tradeoff, not a paused demo presented as live proof.

**Files:** transport scheduling, API job lifecycle/outcomes, metrics cache, `scripts/` continuous replay runner and browser timing evidence. Maintain 30 s expiry tied to the original confirmation.

## L02 — Factual-first candidate path (only if L01 justifies it)

**Work:** present an explicitly labeled deterministic supported candidate for human approval while optional richer AI wording runs. AI results become a separately visible proposed revision; they cannot automatically replace, withdraw or modify a published revision. Keep approved and proposed pointers separate. Promotion to a new version is an explicit atomic producer action, followed by existing retraction/expiry semantics.

**Acceptance:** approving the factual version while AI completes does not race, silently change text or remove a live overlay. A stale AI job cannot promote itself; corrections invalidate both dependent versions. Viewer/history/recap show only the explicitly approved version. **Stop:** if this requires an unsafe late migration, keep the existing single-candidate flow and disclose measured replay-assisted use.

## E02 — Final benchmark and release decision

**Work:** freeze the selected configuration and run the sealed evaluation, human content review and final report specified in [evaluation-plan](evaluation-plan.md). Publish exact denominators, all attempted runs, model modes, unknown usage and dataset lineage.

**Acceptance:** no severe unsupported claim or publication invariant failure in the release set; no claim of independent-match accuracy from correlated variants; architecture comparison includes a strong single-agent baseline. After a failing final case is inspected for tuning, it becomes regression data: use new final parents or label the remaining assessment as non-blind. Report inconclusive comparison honestly.

## U02 — Obtain actual product evidence

**Work:** James recruits relevant participants; researcher follows [evaluation-plan](evaluation-plan.md). Separate neutral, uncoached comprehension tasks from timed comparative tasks. Record participant role/expertise, task outcome, errors, wording feedback and individual observed timings. Observe producer approval/retraction and casual understanding, not just visual preference.

**Acceptance:** all critical misunderstandings and accidental publication actions are fixed/retested or explicitly unresolved. Case notes distinguish expert/user evidence from engineering judgment. No generalized percentage time savings or revenue claims from the small formative sample. If recruitment fails, deliver the instrument and report the impact claim as unvalidated.

## Q01 — Integrate and deploy the frozen candidate

**Work:** run backend, data/reference, frontend production build and browser gates appropriate to selected changes. Verify legacy/v2 reads and approval hashes across Cosmos/HTTP. Exercise correction during a running workflow, refresh/reconnect, middle-story retraction, API restart and duplicate delivery. Run actual Azure smoke with measured mode/usage and then a continuous-play rehearsal. Record container digests, schema/metric/prompt/model versions and rollback steps.

**Acceptance:** G1–G6 in [README](README.md) have evidence or a documented claim-limiting exception; correctness failures block release. No additional Azure resource is required. Rollback retains factual fixes and knows how to read any new stored packages; if necessary, route evaluation/demo to isolated new sessions and preserve the old deployment until compatibility passes.

## S01 — Make judging straightforward

**Work:** prepare the public repository under the owner-selected account, confirm license choice, inspect tracked files for credentials/private data, and run actual GitHub CI. Replace stale README statements (for example the repository map still calls runtime data three fixtures). Add a concise problem, audience, actual architecture, measured results, limitations, setup and judging instructions. Update the Innovation Studio entry to match the verified current build; link the public repository, current live demo and a working demo video under two minutes. Check every link from a logged-out browser and remove old claims such as three Python agents or template-only execution unless they still describe the submitted build. Provide judge access through a dedicated documented mechanism without publishing the owner's producer key in source or video.

Record approximately 115 s of functioning product: problem and moving play → concrete explanation/evidence → real review decision → producer approval → distinct audience/player view → approved recap → compact measured proof. Label synthetic data and any replay jump. Keep architecture/trace detail brief. State exact measured limits and use a representative run rather than hiding failures.

**Acceptance:** public project-page, source, live-demo and video links work logged out; CI corresponds to the released commit; visible text is legible at ordinary playback size; export is strictly below 120 s; test access works for judges; release remains available through judging. Do not announce or submit a result before the owner has completed required registration/submission steps. Final description names only implemented technologies and features.

## Suggested commit boundaries

1. Factual attribution and vocabulary fix, with focused tests.
2. Workflow outcome accounting and timing.
3. Versioned claim contracts, renderer and compatibility tests.
4. Evaluation harness and fresh discovery/reference separation.
5. Spatial/context tools (each independently reviewable).
6. Updated agent roles and decision-report evidence.
7. Audience UI and player history.
8. Optional editorial/latency changes, each separate.
9. Final evaluation and deployment manifest.
10. Submission documentation and recording assets/links.

Keep each commit coherent and runnable. Update acceptance evidence alongside the related change. Do not squash away observed failures or change reference labels to conceal them.

### Owner-authorized follow-on: pressure flagship (24 October)

The bounded Pressure Swing pipeline, additive integrated fixtures, relevance and
audience evidence views, overlay hold, current-model smoke and pilot materials
are implemented separately from MC01–MC10's original scene. See
[delivery and remaining human work](../pressure-flagship.md) and
[verification](../../evals/match-coverage/pressure-flagship/verification.md).
No tactical-turning-point, difficulty probability, chaos calibration, human
rating, external publication or deployment is claimed. Do not merge these new
pressure references into the original pass/mixed evaluation denominators.


### Producer walkthrough follow-up (25 October)

Captured during one first-time producer walkthrough. This is a list of observed
questions, not a participant study or evidence that the proposed changes improve
comprehension. Prioritize as a concise terminology, identity and information-
hierarchy pass after the currently committed synthetic-data tickets; retain the
explicit source audit and publication safeguards.

- Show a player's shirt number with their name wherever an insight names them
  (for this replay, Beni Vidal is Harbor City #9; Dani Luna is #11).
- [Implemented locally, 25 October] Rename “Pressure Swing” to “Nearby pressure
  change”; label the before-pass and after-reception windows, forward distance,
  and observed coverage as seconds out of the two-second window. Hide the
  repeated “Why this moment?” pressure summary when it restates “What changed?”;
  retain it when it adds the supported previous-three-pass comparison. The
  measurement still does not establish tactical pressure or cause.
- Rewrite the analyst version as a short, connected reading of the play: name
  passer/receiver with shirt numbers, give the comparison and window in plain
  language, explain what the measurement can help an analyst inspect, then state
  its boundary. Avoid a label-led list of radius, means, drop and coverage; keep
  full audit values in the evidence details. The current analyst text is a dense
  metric list while the “Why this moment?” sentence merely repeats its figures.
  Preserve the same supported facts and qualifications in both languages.
- [Implemented locally, 25 October] Candidates say “Ready for review”; internal
  revision numbers stay on approved status where they identify the published
  wording.
- Keep raw observation IDs and evidence hashes out of the default explanation;
  retain them inside an optional technical audit view. Clearly distinguish
  producer-only evidence from the approved explanation and variants viewers get.
- Make simple/analyst and English/Spanish previews easy to open before approval,
  then show where each appears in the companion. Label the audience package as a
  summary of viewer options if it remains read-only.
- Explain “Select shared overlay” as choosing which approved story is on the
  match broadcast while the other approved stories remain available in the
  companion/history; consider renaming the action to say that plainly.
- [Implemented locally, 25 October] Opening “Processing & review trace” shows
  an opening state and moves keyboard focus and the viewport to the panel after
  it loads. The existing concise role summary leads; timing, token counts and
  call details remain secondary.
- [New, P2] Remove or reduce the large green “Producer review desk” banner.
  The persistent header already identifies the producer console and says live
  stories/evidence are in view. Keep its distinct guidance—that new insights
  join the queue while the selected insight stays in view—as a quiet one-line
  note near the queue or in help. Check that producers still understand this
  behavior without a second prominent status panel.
- Use concise evidence labels: “Before the pass”, “Forward distance”, and “After
  reception”; keep each number and unit together on narrow screens.
- On the viewer companion, make clear that the pitch/replay is the live view and
  approved explanations appear when available; “Catch me up” opens the recap.
  Explain the player/team focus selector and distinguish “no approved story
  involving this focus in this interval” from “nothing happened” or “no stories
  exist”. In the observed screen, Alder Rovers is the selected filter, so the
  empty state means no approved Alder Rovers involvement in that interval; the
  whole-play control clears that filter. Let viewers find approved moments for
  other teams/foci without losing the live match.
- [Implemented locally, 25 October] Make the pitch easier to read: enlarge the
  control, ball and goalkeeper legend, and show a player's name, shirt number,
  team and goalkeeper role on hover and keyboard focus. Provide tap/select on
  touch screens; the browser tooltip alone is too subtle and unavailable to
  touch users. Restrained movement between valid observed positions remains
  separate work below.
- Add restrained movement between consecutive observed player/ball positions so
  the pitch feels continuous. Interpolate only across valid observed intervals;
  preserve missing-data gaps and source positions, avoid invented runs or
  tactical animation, and honor reduced-motion preferences. Movement should
  clarify the play without distracting from its explanation.

Do not add these changes to the SD01–SD04 delivery claim. The continuing human
review remains necessary to determine which explanations and controls people
actually understand.

### Hackathon brief reconciliation (25 October)

This is a scope check against the official challenge description, not a reason
to add every optional example to the current submission. The five-stage pipeline,
continuous synthetic feed, mixed-event coverage, producer-reviewed overlay,
recaps, analyst/casual views, player/team focus, English/Spanish output and
synthetic-data work are already implemented or explicitly tracked in LM01–LM07,
MC01–MC10, SD01–SD08 and the producer walkthrough follow-up above. Demonstrate
those together on one incident; do not create duplicate tickets for them.

The following items are candidates only after the current submission/release
gates. Do not add them to the current delivery claim or displace correctness,
user review, and submission work.

| Candidate | Decision | Reason and gate |
|---|---|---|
| Pass-completion rate | **PQ01 — P2 discovery** | Forward pass distance is already supported. A completion rate is useful analyst context only if the source represents all attempted passes, including incomplete ones, with an explicit team/player and time-window denominator. The 25 October catalog audit found a denominator but weak outcome diversity: most authored fixtures resolve every pass as received, while only two development parents include an intercepted pass. Define the metric and broaden independent cases before adding it; then require football review. Never call one completed pass “accuracy.” |
| “What if?” alternative for a key moment | **CF01 — P2 discovery/prototype** | This is a distinctive optional extension and fits the brief’s request to explain why moments matter, but is not required. Prototype one producer-selected moment only after user research confirms the question is useful. Show observed facts separately from the hypothetical branch, expose assumptions and uncertainty, and prohibit claims that the alternative would have caused a goal or changed the result. Do not show xG deltas or outcome probabilities without a validated model and independent outcome evaluation. |
| Player speed/distance indicators | **Defer** | These are optional and can clutter the live explanation. Revisit only for a player-focused analyst view, with stable sampling, missing-data handling, declared units and reviewed thresholds. No always-on speed overlay. |
| Pass-difficulty rating | **Defer** | No agreed operational definition, calibration set or independent football validation exists. Nearby-opponent counts and distance must not be renamed “difficulty.” |
| Automatic eventing from video | **Out of current scope** | WHY/NOW consumes the hackathon’s synthetic event stream; video detection would require a separate labeled video/vision pipeline and is not needed to demonstrate the five stages. Do not imply that the current product analyzes match video. |
| More languages | **Defer** | English and Spanish are already supported. Additional languages need reviewed football terminology and complete UI/story consistency; language count alone does not improve the product. |

Keep producer approval and the audit trail: they support trust and the broadcast
workflow. Keep their technical detail backstage, and keep the viewer experience
focused on the match and the approved explanation.

### Competitor-inspired discovery (25 October)

PitchPulse's most useful inspiration is the direct path from live match state to
an audience-facing answer. Add **EQ01 — Ask about an approved moment (P2,
discovery first)**: explore a small set of viewer questions answered only from
the exact approved moment and its evidence, with a clear link back to that
moment. Start with questions such as “What changed here?” and “Why is this
shown?”; when the evidence cannot answer, say so. This is not an open-ended
match chatbot, a new source of tactical claims, or a per-viewer model call.
Prototype only after the producer/viewer study; assess whether it helps viewers
understand the match without pulling their attention away from it. Keep the
answer concise, optional, and consistent with the selected language and focus.

Do not copy PitchPulse's always-on metrics panel, extra agent count, voice,
speed thresholds, or breadth of indicators as a checklist. The useful principle
is making the connection between a match moment and its explanation easy to
follow; preserve WHY/NOW's evidence bounds and low-distraction presentation.
