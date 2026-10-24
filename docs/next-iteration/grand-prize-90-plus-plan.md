# WHY/NOW: engineering plan for a 90+ product assessment

> **Scope update, 23 October 2026:** the [broader match coverage plan](match-coverage-implementation-plan.md) is the next implementation handoff. It promotes basic goals/shots, possession overview and recovery/control-change stories from deferred/conditional scope into required backlog. This document remains the earlier quality specification; outstanding verification and research are not marked complete. Advanced xG/tactical claims remain separate work.

**Prepared:** 21 October 2026, America/Lima  
**Product baseline:** version 0.4.0; source `8477c44`; API runtime source `c85f035`  
**Status:** proposed work, ready for engineering handoff; acceptance results below are targets, not completed findings  
**Owner:** James; engineering, QA, football reviewer and research roles to be assigned  
**Scope:** the MVP itself. Deployment availability, repository visibility, submission administration, and video production contribute no points to this plan.

## 1. Objective and definition of success

Build a product that helps a viewer understand a meaningful change in a football sequence and lets a producer verify, select and publish that explanation quickly. The improvement must be apparent in the content and interaction, supported by reproducible evidence.

The current internal assessment is **76/100**. Target **92/100**, providing a small margin above 90. These are subjective product assessment targets, not calibrated judge predictions. Completing tickets does not automatically earn points. Reassess only after the corresponding behavior and evidence exist.

| Category | Current | Target | What must materially improve |
|---|---:|---:|---|
| Technological Implementation | 17 | 18 | Complete timing/disposition accounting, safe historical dependencies, maintainable state handling, reproducible operational tests |
| Agentic Design & Innovation | 13 | 18 | Consequential contextual decisions, useful reviewer interventions, measured advantage or defensible tradeoff against simpler approaches |
| Real-World Impact & Applicability | 13 | 18 | Useful stories, understandable claims, workable producer review time, observed user benefit and a concrete adoption boundary |
| User Experience & Presentation | 15 | 19 | Distinct narratives and titles, concise recap, visible evidence connection, coherent mobile layout and meaningful personal views |
| Adherence to Hackathon Category | 18 | 19 | A complete example of synthetic football events becoming contextual, explainable, accessible and personalized intelligence |
| **Total** | **76** | **92** | **Useful intelligence and demonstrated comprehension are the principal gains.** |

The target is deliberately ambitious. If user research or the agent experiment remains incomplete, describe the product as improved but the 90+ case as unsubstantiated.

### The intended experience

1. A qualifying passage arrives while replay continues.
2. The application computes facts and a bounded comparison with prior completed passes.
3. The Director selects a supported explanatory angle and content for the audience.
4. The Reviewer verifies the facts, comparison scope and usefulness, requesting one bounded repair when needed.
5. The producer sees a distinctive title, a short explanation, why it was selected, a review countdown, and linked evidence.
6. The viewer sees a compact visual and explanation; selecting a player changes the relevant history and emphasis.
7. Catch me up summarizes distinct approved developments and links each to its evidence.
8. A correction withdraws affected material and derived comparisons; unrelated stories remain available.

**Illustrative output, not an observed result:** “The pass advanced the ball 24 m, farther forward than each of this team’s previous three completed passes in this replay. The team retained possession for three seconds afterward.” The comparison is allowed only when those exact facts and the complete comparison population are supported. No claim of chance creation, tactical intent or a defensive line break follows from this wording.

## 2. Starting point: reuse what is already implemented

The [implementation record](decision-log.md) and [QA record](../qa.md) establish the current baseline. Do not reimplement these capabilities as new work:

- Scoped version 2 claims, deterministic English/Spanish rendering, legacy package readers and exact package hashes.
- Director/Claim Reviewer roles, bounded evidence requests and repair, explicit factual fallback, and producer publication authority.
- SQLite/Cosmos workflow outcomes and usage accounting, including abstention and rejection.
- Forward pass displacement, reception zone and corrected receiver/team attribution.
- Explanation panel, approved player/team history, observed trails, evidence stages and isolated retraction.
- Active-first replay transport, durable observations, correction handling and immutable approved versions.
- Evaluation adapters for templates, strong single agent and collaboration, with explicit live-run budgets.

Recorded evidence: 272 backend tests; 14 local browser tests; 168 synthetic regression cases and 594 checkpoints. A bounded two-stream timing run left 19.786 s and 17.490 s before expiry; an earlier run included an 8.753 s miss. These are engineering samples, not a reliable latency distribution. The four agent-harness discovery compositions share one generator backbone and do not constitute an independent final evaluation.

### Concrete remaining gaps

- `engine/workflow.py::compare_prior_window` always returns insufficient history.
- `engine/narrative.py` uses the same title for every story. Narrative angle is stored but does not define a distinct presentation structure.
- The recap can repeat nearly identical sentences for different moments.
- Personalization filters relevant history but usually appends a role sentence to a general explanation.
- The trace exposes technical steps more clearly than editorial choices and corrections.
- Detailed text and expanded history push the pitch down the mobile page.
- “Follow the escape” and some pressure/bypass labels imply more tactical meaning than the measurements establish.
- Workflow completion and later package acceptance are not fully reconciled; exact durable-evidence-to-browser timing remains missing.
- No completed fair agent comparison, independent sealed benchmark, or formative user study establishes product benefit.

## 3. Scope and prioritization

**P0:** required for the proposed 90+ reassessment. **P1:** selected only after evidence identifies a benefit. Fixing a safety regression always takes precedence.

Promote the earlier conditional historical-context ticket C03 into this iteration’s P0 work, subject to its factual definition and dependency tests. Promote concise recap and distinguishing titles into P0. Keep automated editorial ranking/cooldown, a third agent, new event families, and a factual-first publication path conditional. This document supersedes the earlier plan for the next product iteration; the earlier plan remains historical context.

No new Azure service, hosted-agent migration, generic chatbot, speech generation, xG model, tactical-intent inference, real-match footage, or full-match simulation is required. Use the existing model first. A model change is a separately measured experiment.

## 4. Category 1: Technological Implementation — 17 → 18

### T01 — Complete lifecycle and end-to-end measurement (P0)

**Problem:** a produced workflow can later be discarded as stale; package-level success and model execution success are different. Current timing begins when evidence is observed by scheduling, not when its prerequisites became durable or its content reached the browser.

**Changes:**

1. Preserve immutable workflow terminal records. Add an append-only disposition record linked by run ID and package revision: accepted, discarded stale, superseded, persistence failed or expired before acceptance. Do not rewrite a terminal `produced` outcome into another state.
2. Track every detected opportunity independently of whether a model job is scheduled. Record capacity deferral, insufficient history, expiry, retry and final disposition. Keep expected-but-never-detected opportunities in the evaluation ledger so they cannot disappear from the denominator.
3. Record server UTC timestamps for observation durability, prerequisite evidence readiness, enqueue, start, candidate completion, package acceptance and approval receipt. Retain replay times separately. Store monotonic durations within a process.
4. Define evidence readiness as the latest durable availability time among all required current and selected historical dependencies. Also retain actual detector/scheduler observation time so scheduling delay is visible.
5. Add a browser acknowledgment after an approved revision is rendered, with session/story/revision/event identity. Deduplicate and rate-limit it. It is telemetry, never approval authority. Do not collect personal identities or treat an acknowledgment as proof the user read the content.
6. Record browser paint intervals with a browser monotonic clock; document clock offset/uncertainty for any server-to-browser comparison. Missing acknowledgment means missing data, not zero latency.
7. Preserve known provider usage after errors. Unknown usage retains its reservation. Include full model deployment/version and prompt/tool/schema/renderer identifiers in the run manifest.

**Files:** `engine/outcomes.py`, `engine/repository.py`, `engine/cloud_repository.py`, `services/api/main.py`, `scripts/measure_replay.py`, `apps/web/lib/api.ts`, viewer state/render hooks; proposed `engine/dispositions.py`.

**Acceptance:** success, rejection, abstention, fallback, timeout, stale completion, restart interruption, persistence failure and never-scheduled expiry reconcile without lost or double-counted attempts. Test duplicate acknowledgments, out-of-order events, cross-story identities and absent clients. A stale completion cannot publish; accounting retains its model usage.

### T02 — Historical dependencies and compatible packages (P0)

**Problem:** a comparative story depends on prior passes and on which passes belong in the comparison population. Hashing only the current pass would allow stale comparisons to remain approved.

**Changes:**

- Add a versioned context record containing current pass ID, team/period, release time, cutoff, lookback, selection-rule version, ordered comparator IDs, raw measurements, units, source IDs and source hashes.
- Bind the historical selection population and its corrections, including information that determines whether a pass was eligible or excluded. A late event may change the comparator set even when the previously selected passes did not change.
- Maintain a dependency index from relevant source/window revisions to affected context packages. Recompute only those dependencies; bound the retained index and document its lifecycle.
- When history changes, invalidate affected approval/overlay/recap projections through the existing audited path. Preserve original immutable packages and create a newly reviewed revision when appropriate.
- Choose and document a compatible package version before implementation. Preserve readers for stored v1 and v2 packages; never migrate approved text silently. New contextual fields must participate in hashing and schema validation.

**Files:** `engine/contracts.py`, `engine/core.py`, `engine/narrative.py`, both repositories, API materialization, `data/schemas/`; proposed `engine/context.py`.

**Acceptance:** selected-pass correction, previously excluded-pass correction, late insertion into the latest-three set, retransmission, ties and cross-period boundaries behave correctly. A historical correction changes only dependent stories; unrelated approvals survive. An old package remains readable and its hash unchanged. Document a rollback reader that can read all packages produced by the candidate build.

### T03 — Readable state handling and operational boundaries (P0)

**Changes:**

- Extract snapshot/subscription state, selected-story requests and audience preferences from `match-desk.tsx` into focused hooks. Separate producer review, trace summary, evidence and recap components. Keep the existing stale-response protections.
- Expand dense control flow in publication and repository code into readable operations. Introduce formatting/lint rules scoped to changed modules; avoid an unrelated whole-repository rewrite.
- Profile API-wide lock hold time before changing locking. Move network reads outside shared locks only with documented transaction/revision checks. Retain the single-worker assumption until concurrency behavior is established.
- Add a documented incoming-feed boundary: required events, clock ordering, IDs, corrections, units and validation failure behavior. Implement a small adapter contract test using an independently authored feed with different IDs; broad vendor integration is outside scope.
- Test role boundaries with the existing producer credential: a viewer cannot mutate, access protected traces or cause model work through preference changes. Document the shared-credential/single-operator limitation; enterprise identity is not implied.

**Acceptance:** existing selection-race, approval, expiry and correction tests pass; changed modules are readable and linted; profiler evidence identifies actual bottlenecks. Malformed or incorrectly scaled adapter input is rejected with a useful reason. No performance improvement is claimed from refactoring alone.

## 5. Category 2: Agentic Design & Innovation — 13 → 18

### A01 — Implement bounded, useful historical context (P0)

Add `get_recent_pass_context(current_pass_id)` as an aggregate read tool. Do not expand the existing raw-position window to expose unrestricted history.

**Initial contract:**

| Rule | Required behavior |
|---|---|
| Candidate population | Successful received passes from the current team and period, resolved strictly before the current pass release |
| Availability | Required observations and corrections were available by the frozen investigation cutoff |
| Window | Prior resolutions within the preceding 120 s; define the lower boundary as inclusive |
| Selection | Latest three by resolution time, then stable pass ID for ties; exclude the current pass and deduplicate corrected/retransmitted events |
| Measurement | Raw signed forward displacement under each pass’s period attack direction; metres |
| Coverage | All required release/reception endpoints valid; missing relevant history produces explicit incomplete/insufficient status |
| Output | Status, selected IDs/times/values, sample count, exact relation, dependencies and limitation text |
| Allowed comparison | “Farther forward than each of the previous three completed passes by this team in this replay,” only when strictly greater than all three raw values |
| Unsupported conclusions | Best pass of the match, chance creation, tactical superiority, percentile, sustained control, causal impact |

Fewer than three valid passes means no comparative claim. Equal or mixed values can support a precise neutral comparison only if a separately defined renderer exists; otherwise omit the comparison. Incomplete feeds must not quietly present the latest three observed passes as the true latest three: qualify the population or abstain under the frozen completeness rule.

**Research spike:** before finalizing, author paired scenes with identical current passes and contrasting prior histories. Review whether the wording is useful and understandable with a football reviewer. If the definition changes, version it and regenerate independent reference expectations before tuning.

**Acceptance:** distinct histories change only the supported contextual interpretation; all selection, cutoff, direction, correction, incomplete-history and tie boundaries are tested. Every comparison can be reconstructed from its visible evidence. This is prerequisite work for A02, not an optional decorative tool.

### A02 — Make agent decisions consequential and inspectable (P0)

Keep Director → Reviewer as the candidate topology. Update existing agents rather than adding a role by default.

| Component | New responsibility | Explicit limits |
|---|---|---|
| Evidence/context builder | Compute facts and a cheap availability summary for bounded context | No generated measurements, hidden labels or future observations |
| Story Director | Choose an explanatory question/angle, request relevant context, select facts, choose audience emphasis and a supported title pattern, or abstain | Allowed claim/structure IDs only; no arbitrary causal prose |
| Claim Reviewer | Independently check canonical facts and comparator selection; assess factual support separately from editorial relevance; request targeted repair or reject | Director rationale is not evidence; same-model agreement is not independent truth |
| Renderer/validator | Realize bilingual claims, title, visual bindings and qualifications | Unsupported combinations fail validation even if the model approves |
| Producer | Decide whether the proposed package should be published | No agent can approve, silently replace or retract on editorial grounds |

**Narrative plan additions:** angle ID, audience goal, lead claim, supporting claims, optional comparison ID, title pattern ID, visual bindings, and a short public decision summary. Define schemas and limits before prompt changes. Angle must change the organization/emphasis of the explanation, not merely metadata. Supported first angles: spatial change, verified reception, and historical contrast. A historical angle requires valid comparative evidence.

The Director may request context when it could resolve a useful question. Tool-call count is not a success metric; supplied adequate evidence should avoid redundant calls. The Reviewer must see the exact rendered content and have independently recomputable facts, including context completeness, rather than relying on the Director’s description of the tool result.

Retain the initial six-call/twelve-tool/15-second workflow ceiling and bounded repair. Any proposed change requires a recorded latency/cost tradeoff. If a context tool fails, omit the comparison or fall back honestly; do not invent one. Re-review repaired content.

**Acceptance:** traces show useful selections on varied cases, at least one legitimate labeled repair/rejection, and at least one appropriate context abstention. Distinguish deliberately injected challenges from spontaneous model errors. Test wrong actor, false comparison denominator, unsupported implication, false rejection of a true but routine fact, instruction injection, missing context, repeated tool requests and deadline exhaustion.

### A03 — Run the architecture experiment (P0)

Use the existing `evals/agentic` harness and extend it; do not create a second incompatible evaluator.

- **T3:** deterministic selection over the same new facts/context/renderer.
- **S3:** strong single agent with the same tools, facts and meaningful self-check/repair.
- **M3:** Director plus independent reviewer context with the same ceilings.
- **Ablations on discovery data:** context on/off and reviewer on/off. No-review variants are evaluation-only and never bypass production publication controls.

Freeze configuration and interleave arm order. Use the same model/version and evidence cutoffs. Log actual spend, tokens, calls, fallback and all failures. Blind human raters to arm. Report paired results by structural parent, not by audience variant or repeated trial.

**Selection rule:** M3 needs either at least a 10 percentage point descriptive improvement in useful accepted opportunities or at least 20% fewer substantive edits versus S3, without a severe correctness regression and while meeting the operating timing target. Report uncertainty and disagreements; these are project decision thresholds, not statistical proof. If results are inconclusive, retain the simpler passing architecture and do not claim multi-agent superiority. The 18/20 target may remain unmet despite a technically correct implementation.

**Deliverable:** `evals/agentic/REPORT.md` with all arms, context ablations, counterexamples, reviewer false-rejection rate, cost per accepted story, timing, limitations and architecture decision. No final decision based solely on an LLM judge.

## 6. Category 3: Real-World Impact & Applicability — 13 → 18

### I01 — Independent scenarios and explicit product questions (P0)

Primary workflow: a producer decides whether a short explanation helps viewers understand a passage while play continues. Secondary workflow: a casual viewer or analyst explores approved moments. Do not claim validated broadcaster adoption from developers acting as producers.

Build 8–12 new discovery structural parents and a target of 24 separate final parents: 16 eligible opportunities and eight quiet/ineligible/insufficient situations. Use genuinely different event structures/history, not renamed players or seed perturbations of existing parents. QA authors or reviews expected results independently of production metric code. The final set is sealed before tuning; changes informed by it require a fresh final set or explicit relabeling as regression.

Required challenge dimensions: different preceding histories with the same current pass, successful but ordinary play, missing history, delayed correction, onward receiver pass, duplicate names, both attack directions, near-boundary distance, repeated similar moments, distinct later moment, expired opportunity and unsupported suggested wording. Keep reference answers and generator plans outside runtime images and model tool access.

**Acceptance:** lineage and split audit, independent references, leakage tests, all expected opportunities retained, football realism review status explicit. Existing 168-case regression remains unchanged. Synthetic data is appropriate; the missing evidence is structural coverage and human interpretation.

### I02 — Observe producer and viewer benefit (P0; participant dependency)

Use and update `docs/user-study.md`. James arranges participants; the engineer supplies a stable build, neutral tasks and data capture. Target 3–5 relevant producers/analysts and 5–8 casual viewers, plus a football reviewer and a competent Spanish reviewer. Roles may overlap if disclosed. Start recruitment while engineering runs; no fabricated users, ratings or testimonials.

Pilot once, freeze tasks, then use counterbalanced baseline/candidate scenes. Collect uncoached task observations before retrospective questions. Keep think-aloud discovery separate from clean timing measurements.

**Tasks:** explain what changed; distinguish team retention from receiver control; identify what cannot be concluded; find a selected player’s relevant moment; verify a comparison; decide whether a candidate is worth showing; approve while replay runs; retract an older moment; use recap to identify distinct developments.

**Product decision thresholds:**

- Zero unresolved critical misconceptions introduced by the interface, such as believing a defensive line break or goal chance was established.
- At least 80% of the observed viewer task attempts correctly identify the primary change and relevant actor; report counts and participant-level outcomes alongside the fraction.
- At least 80% of observed key tasks completed without moderator rescue; revise any consistently confusing task.
- At least 70% of eligible candidate opportunities accepted by producer raters as useful and supported without substantive editing, counting failures/misses in the denominator.
- Show paired baseline/candidate observations for comprehension and review effort. Small samples support formative decisions, not generalized ROI claims.

Thresholds must be frozen before final sessions. If they fail, fix the observed cause and retest affected tasks. Missing participants leave this gate open; engineering completion cannot substitute for it.

### I03 — Establish a credible live operating envelope (P0)

Extend `scripts/measure_replay.py` to cover at least 20 distinct eligible opportunities across varied parents at 1× continuous replay, first one active stream and then two. Retain never-scheduled, missed and expired cases. Capture T01 stages and cold/warm conditions. No pause or seek may improve the measured candidate deadline.

Targets: one-stream evidence-durable→candidate P95 ≤10 s; at least 90% of eligible opportunities ready with ≥10 s before the original expiry. Measure two-stream results separately against the same readiness goal, reporting any degradation. Do not present percentiles from 20 samples as a stable production distribution. Human review and browser display are separate measured intervals.

Add a stub-model delivery test with 10 viewers to isolate frontend/API delivery load; clearly distinguish it from real-model timing. Verify a transport interruption and restart with replay recovery and no duplicate publication. Calculate model cost per accepted story from all attempts, including failures; separate infrastructure allocation and unknown usage. Verify actual pricing immediately before any paid run and enforce explicit call/token/cost reservations and deadlines.

**If timing fails:** profile ingestion, lock contention, queueing and prompts first. Consider an explicitly labeled factual candidate while AI completes only through a separate design: approved and proposed revisions must be separate, promotion requires producer action, and late AI must never replace an approval automatically. This conditional path is not included in the core estimate.

## 7. Category 4: User Experience & Presentation — 15 → 19

### U01 — Distinct story titles, explanations and safe editorial choices (P0)

Replace the fixed title with validated templates populated from supported facts. Examples of allowable patterns: “18 m forward to Jori Luna” or “Farther forward than the previous three passes,” when their evidence exists. Titles participate in package validation/hash and cannot introduce a stronger interpretation than the body.

Casual view: one or two short sentences describing the primary change and confirmed outcome; aim for ≤45 English words, allowing localization to prioritize clarity. Detail view: grouped facts and comparison scope with expandable operands/limits, rather than one long paragraph. Do not reward extra facts simply because they are available.

Revise “Propose an edit” into choices that match the grammar: emphasize movement/reception/context, choose shorter/detail emphasis, or submit a suggestion with an explicit explanation of accepted changes. Show supported selections and rejected requests. The producer must see the new exact proposed revision before approving it; already approved text remains immutable.

**Acceptance:** different moments have distinguishable factual titles; unsupported title claims fail validation; English/Spanish preserve actor, polarity, comparator and units; a chosen angle creates a visible content difference. Test revised proposal approval races and a suggestion that cannot be represented safely.

### U02 — Explain the evidence visually on desktop and phone (P0)

On desktop, keep the explanation next to a compact evidence view. On mobile, place the short explanation, compact pitch and Show why action in the initial flow; move detailed history below and collapse it by default. Switching to detail must not require scrolling past the complete history to reconnect text and play.

Bind clauses to visual annotations: pass displacement to an arrow, reception zone to an outlined region, team retention to the observed interval, and historical comparison to a small three-pass strip/table with dates/times and distances. The viewer selects a fact to highlight its evidence. Distinguish the live clock from the selected evidence clock without relying on color.

Use factual labels such as “Replay the sequence,” “Nearby opponents,” and “Longitudinal positions.” Remove unsupported tactical implications throughout titles, helper text and evidence controls. Translate core viewer controls and states into Spanish alongside the explanation so the language choice produces a coherent experience.

**Acceptance:** 390×844 and 1366×768 layouts, no horizontal overflow, keyboard operation and visible focus, accessible names and selected states, meaningful contrast, and no color-only statuses. Test mobile history growth with at least five approved moments. Focus trails respect missing-frame gaps and cutoffs. No new inferred trajectory is presented as observed data.

**Files:** `apps/web/components/audience-panel.tsx`, `match-desk.tsx`, `pitch.tsx`, `ui.tsx`, `apps/web/lib/api.ts`, new focused components/hooks and browser tests. Read `apps/web/AGENTS.md` and relevant installed Next.js docs before changing framework behavior.

### U03 — Make personalization and recap substantively useful (P0)

Use the existing verified role/team filtering. Lead a passer view with the supported release/movement contribution and a receiver view with reception/location; keep later possession attributed to the team. Preserve an easy Whole play return and an honest empty state. No viewer preference change triggers a model call.

Build a deterministic recap projection over approved packages. Select up to three distinct developments, retaining chronology. Group repeated equivalent facts using a versioned signature based on predicate, actor/team, relation and defined measurement buckets; define buckets with examples before implementation. Grouping cannot turn approximate similarity into an unsupported trend claim.

Each recap item includes a distinguishing title, short supported statement, replay time and evidence/story links. If multiple moments are grouped, expose their IDs and say only that similar approved moments exist; do not infer sustained dominance. Offer access to all approved history. Selection reasons remain inspectable, and current focus filters candidates before selection.

Retraction or correction immediately removes affected items and recomputes any grouping/count. A recap can include an expired-but-approved archive, clearly labeled; it cannot revive an expired live overlay. Bind the recap projection to its input package revisions and selection-rule version. Models need not generate a recap.

**Acceptance:** repeated moments do not produce duplicate paragraphs; a distinct later development is discoverable; grouping and tie-breaks are deterministic; player switching changes relevant content without stale responses; retraction updates visible recap and counts. Test empty, one-item and many-item histories and duplicate names.

### U04 — Show why the agents made their choices (P0)

Add a concise producer-facing decision summary above technical trace details:

- Selected angle and the supported fact that motivated it.
- Context available, requested or insufficient, with the exact sample scope.
- Reviewer concern and the resulting change, if any.
- Final proposed explanation and any fallback reason in plain language.

Use structured observable decisions and evidence references. Do not expose private chain-of-thought or pretend the summary is a literal internal thought process. Redact provider/credential details. Reviewer rejection or abstention must be inspectable even when no publication package exists, using the outcome ledger.

**Acceptance:** a producer can identify what changed after a repair, which fact supports the comparison and why fallback occurred. Empty/failed outcomes appear honestly. Detailed calls/tokens/timestamps remain expandable for engineers.

## 8. Category 5: Category fit — 18 → 19

### C01 — Demonstrate the complete product capability chain (P0)

The Grand Prize description values meaningful, explainable match intelligence, narratives, context and personalized access. Map that to functional acceptance rather than submission assets:

| Required capability | Product proof | Tickets |
|---|---|---|
| Football-realistic synthetic events | Independently reviewed structural scenarios, quiet negatives and corrections | I01 |
| Contextual intelligence | Same present play, different history, different justified explanation | A01/A02/T02 |
| Explainability | Click a clause and inspect the exact observations/comparator population | T02/U02/U04 |
| Accessible storytelling | Short casual view, meaningful detail view and coherent English/Spanish controls | U01/U02 |
| Personalization | Relevant player/team emphasis and history without invented involvement | U03 |
| Producer control | Fast evidence review, exact revision approval, correction and isolated retraction | T01/T03/I03 |
| Purposeful collaboration | Measured correction/usefulness contribution with all arms and failures retained | A03 |

Create three end-to-end product acceptance scenarios: a meaningful historical contrast; insufficient history with a useful qualified explanation; and a historical correction invalidating one contextual story while preserving an unrelated one. Run each through both producer and viewer flows. These are functional tests, not a video plan.

**Category breadth decision (P1):** after I02, consider one new explicitly defined story family only if users repeatedly find the existing scope insufficient. Candidate: observed possession recovery followed by sustained team possession, using available events and confirmed intervals. Before implementation, require a separate metric contract, positive/negative examples, independent references, cost/timing analysis and renderer/approval integration. Do not introduce shots/xG, “press beaten,” or match-control claims without their own defensible measurements. A deeper successful passage workflow is the core commitment.

## 9. Engineer work packages, dependencies and estimates

Hours are hands-on estimates for an engineer familiar with the repository. They include focused tests and documentation within each ticket. Final integrated evaluation is budgeted separately. Re-estimate after the context/dependency spike; uncertainty is approximately ±35%.

| Ticket | Owner discipline | Depends on | Hours | Delivery artifact |
|---|---|---|---:|---|
| T01 | Backend/QA | Baseline snapshot | 8–12 | Opportunity ledger, dispositions, timestamps and browser acknowledgments |
| T02 | Backend/data | A01 contract spike | 8–12 | Versioned context dependencies, invalidation and compatibility |
| T03 | Backend/frontend | Baseline snapshot | 6–10 | Focused modules, adapter contract, operational boundary tests |
| A01 | Data/backend | I01 discovery examples | 8–12 | Context calculator/tool, references and metric glossary |
| A02 | AI/backend | A01, T02 | 8–12 | Updated plan/agents/renderer and observable decisions |
| A03 | Evaluation/AI | A02, I01, T01 | 8–12 | Fair experiments, blinded packets and architecture decision |
| I01 | QA/data | Frozen product questions | 10–16 | Discovery/final parents, independent references and split manifest |
| I02 | Product/QA | U01–U04 stable slice | 4–6 | Study integration and anonymized findings; participation time below |
| I03 | Backend/QA | T01, A03 | 8–12 | Continuous timing, failure exercise and cost report |
| U01 | Frontend/AI | A02 contract | 6–8 | Distinct titles, audience structure and editorial controls |
| U02 | Frontend | U01 fixture contract | 8–12 | Responsive evidence layout and core viewer localization |
| U03 | Frontend/backend | U01, T02 | 8–12 | Personalization, deterministic recap and dependency tests |
| U04 | Frontend/AI | T01, A02 | 4–6 | Plain-language decision/repair summary |
| C01 | QA/product | Selected implementation | 3–5 | Complete product acceptance scenarios |
| Final integration | QA/engineer | All P0 behavior | 8–12 | Regression, frozen evaluation and reassessment record |
| **Total** | | | **105–159 h** | Excludes conditional features and participant waiting |

Allow an additional 10–16 hours of researcher/reviewer participation, plus recruitment/calendar time. Two experienced engineers can overlap frontend and backend work after contracts stabilize; the QA/reviewer work has real human dependencies. One engineer should plan multiple weeks of focused work. Compressing the schedule requires explicit scope reduction and may leave the 90+ evidence case incomplete.

### Delivery order

1. **Foundation:** preserve baseline outputs/configuration; prepare discovery scenes; define context, dependencies, opportunity accounting and the participant instrument. Start recruitment.
2. **Context and agents:** implement A01/T02, then A02. Use paired histories and negative cases before UI expansion. Complete T01 in parallel once event contracts are agreed.
3. **Audience:** U01/U02 against frozen fixtures; U03/U04 once real revised packages/outcomes are available. T03 refactoring must preserve behavior and avoid mixing with schema changes in one commit.
4. **Discovery decisions:** A03 and pilot user sessions. Fix errors and choose architecture before final measurement. Decide whether any P1 feature has demonstrated necessity.
5. **Freeze and verify:** final independent cases, I03 continuous operation, I02 sessions, C01 integrated scenarios, regression and documented score reassessment. A failed final set becomes regression after tuning.

Commit one reviewable concern at a time: contracts; context computation; invalidation; agents; titles/editorial UI; mobile/evidence; recap; accounting/timing; evaluation evidence. Keep the private repository private under the existing owner instruction. This plan does not request publication or infrastructure provisioning.

## 10. Evaluation protocol and release gates

Use the existing [evaluation protocol](evaluation-plan.md) as method background. This document supplies the current baseline and overrides outdated implementation status or submission tasks there.

For final quality comparison, target 24 parents with two model trials per parent for S3/M3 and one deterministic T3 run. Sixteen eligible parents × two trials × two model arms = 64 expected eligible workflows, with a maximum of 384 model calls at the current six-call ceiling. Unexpected calls on negative cases consume the same budget and count as failures. A stricter global budget stops scheduling and marks remaining cases unrun. Provider retries, model graders and discovery runs need explicit allocations; never silently exceed the reservation. Verify deployed-model input/output rates immediately before execution.

Grade factual support, useful specificity, audience comprehension, editorial acceptance and reviewer contribution separately. Use all eligible opportunities for useful coverage, including misses, failures and abstentions. Report correct abstention on negatives separately. Count repeated trials and variants as repeated measurements, not independent scenes. Human raters receive blinded outputs with the same evidence. An independent second rater checks all severe/suspicious cases and at least 25% of the rest; retain disagreements and adjudication.

| Gate | Pass condition | Failure response |
|---|---|---|
| Safety and compatibility | Zero observed unapproved/future/stale/cross-story leaks; v1/v2 compatibility and new-schema validation pass | Block new capability; repair and rerun affected tests |
| Context correctness | Exact comparator population, source scope, units and corrections reconstruct correctly | Disable comparative wording until fixed |
| Semantic quality | Zero severe unsupported claims in the reviewed final sample; all lesser defects reported | Fix offending capability; replace contaminated final cases |
| Accounting | Every expected opportunity and actual attempt has an explicit disposition; unknown usage visible | Do not calculate misleading success/cost aggregates |
| Agent benefit | A03 practical threshold or documented defensible tradeoff, with uncertainty and all arms | Choose simpler passing design; withhold superiority claim |
| Live operation | I03 targets met at one stream; separate complete two-stream report and explicit operating limit | Profile/fix; investigate conditional factual-first design |
| User usefulness | I02 thresholds and no unresolved critical misunderstanding/publication error | Fix and retest; do not claim impact based on engineering tests |
| UX | U01–U04 responsive, language, keyboard, history and repair behaviors verified | Fix the observed interaction failures |
| Category completeness | All three C01 scenarios pass through producer and viewer | Resolve broken capability chain |
| 90+ reassessment | Independent review of working behavior and evidence against all five categories | Record actual score/gaps; no automatic uplift for ticket completion |

## 11. Risks, decision rules and owner dependencies

| Risk | Early signal | Required response |
|---|---|---|
| Comparison is accurate but boring | Users understand it but do not value it | Revisit explanatory question with reviewer; do not add exaggerated tactical language |
| Multi-agent benefit is negligible | S3 and M3 have similar accepted coverage but M3 costs more | Prefer simpler architecture or retain only a specifically demonstrated reviewer benefit |
| Reviewer rejects routine true facts | Unsupported verdicts driven by relevance | Keep factual support/relevance separate; evaluate false-rejection cases |
| Context makes corrections unsafe | Unrelated history changes leave stale comparisons or invalidate everything | Fix dependency population/index before exposing context |
| Richer explanation misses expiry | More context/tools increase readiness delay | Trim payloads and redundant calls; preserve deadlines and full miss accounting |
| Repetition survives recap grouping | Similar items crowd out distinct developments | Tune the disclosed grouping rule on discovery data and retest |
| Human reviewers unavailable | No confirmed session dates | Continue engineering/offline evaluation; mark impact/semantic review incomplete |
| Scope expands into tactical analytics | Proposed claims exceed the data | Require a separate definition/reference/review project; keep core scope |

**James:** arrange football/Spanish review and participant access, clarify the initial producer setting, and decide any business assumptions needed for pilot adoption. **Engineer:** implement the approved contracts, tests and instrumentation; produce working study tasks and a reproducible benchmark. **QA:** independently author/review expectations and hold the final split. Recruitment and study completion are not assumed.

No new permission question is needed for routine implementation already authorized in the project. Paid evaluation must have a concrete bounded configuration using verified rates before dispatch; if a missing budget decision materially changes spend, present that specific decision rather than requesting blanket permission to proceed.

## 12. Handoff deliverables and completion checklist

Keep implementation evidence in the repository without credentials or participant identities:

- `docs/metrics.md`: new context definitions, completeness rules and counterexamples.
- `docs/architecture.md`: actual chosen topology, dependencies, lifecycle and tradeoffs.
- `docs/next-iteration/decision-log.md`: ticket status, experiment decisions and scope changes.
- `evals/agentic/manifest.json`: frozen commit/model/configuration, lineage, budgets and split identifiers.
- `evals/agentic/REPORT.md`: all comparison arms, errors, accepted coverage, cost, latency and uncertainty.
- Proposed `docs/product-validation.md`: anonymous study results and concrete fixes.
- Proposed `docs/runtime-performance.md`: every timing opportunity, stages, misses, concurrency and failure recovery.
- Proposed `docs/product-score-reassessment.md`: category-by-category assessment using actual final behavior and evidence.

### Engineer definition of done

- [ ] Working tree/baseline recorded; old successful and failed measurements retained.
- [ ] Context contract and independently checked examples agreed before prompt changes.
- [ ] Historical population dependencies and versioned invalidation work.
- [ ] Director choices alter useful content; Reviewer corrections are traceable.
- [ ] Template/single-agent/multi-agent comparison is fair and honestly reported.
- [ ] Titles, mobile evidence, audience emphasis, recap and editing affordances match actual behavior.
- [ ] Timing includes missed and never-scheduled opportunities; usage/disposition reconciliation passes.
- [ ] Human findings are recorded as actual observations, with unavailable evidence explicit.
- [ ] Existing regression and relevant browser/compatibility tests pass without weakened expectations.
- [ ] Three end-to-end category scenarios pass.
- [ ] Documentation describes implemented behavior; proposed work remains labeled.
- [ ] Final category scores are reassessed rather than copied from the target table.

## 13. Sources and rationale

- [Microsoft official hackathon rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md): the Grand Prize emphasizes explainable football intelligence, contextual narratives and accessible personalized experiences. The multi-agent category specifically values purposeful collaboration and effectiveness relative to a single agent. Submission requirements are excluded from this plan.
- [Microsoft agent orchestration patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns): orchestration adds coordination, latency and cost; choose the least complexity that reliably meets the task. This supports the measured T3/S3/M3 comparison and conditional treatment of additional roles.
- [Existing research decisions](research-decisions.md): football vocabulary, evidence limits and user-research rationale, with original primary sources.
- [Current implementation record](decision-log.md), [QA evidence](../qa.md), and [agent evaluation status](../../evals/agentic/REPORT.md): source of current capabilities and measured limitations.

All numerical improvement thresholds, effort estimates and score targets in this handoff are project decisions. External sources support the design rationale; they do not validate the proposed product outcomes.
