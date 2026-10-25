# Next product iteration: useful live explanations

Proposed **25 October 2026**, America/Lima. Based on the
[problem evidence and six-project review](../problem-evidence.md). This is a
research-led recommendation, **not an implementation record or release approval**.
It extends the delivered [live-match workflow](live-match-plan.md) and preserves
the [match-coverage requirements](match-coverage-implementation-plan.md).

**Engineering update, 25 October:** the first slice is implemented locally: match-first
live viewing, a shorter producer queue, exact-revision audience preview, readable
selection/review disclosure, interval catch-up and public withdrawal notices.
See the [delivery record](decision-log.md) and
[verification](../../evals/editorial-experience/verification.md).
The specification below remains the research plan; its human study, agent
comparison, partner integration and external release are not marked complete.

## Product choice

Keep the live producer desk and approved viewer companion. Test this promise:
**“Choose the useful story now; help the viewer understand it without losing the
match.”** The candidate differentiation is editorial relevance plus inspectable
corrections and catch-up. Evidence linking, multiple languages and multiple agents
are valuable but already common in the projects reviewed.

The desired outcome is a producer publishing a useful, supported explanation in
time, followed by a viewer correctly explaining the observed change. The outcome
is not the number of generated cards, checked claims or model roles.

## Baseline we must not accidentally rebuild

| Already available locally | Actual unresolved issue |
|---|---|
| Continuous 1× synthetic feed with background work; guided/offline modes distinct | No real provider/video integration; latest iteration not deployed |
| Pass, nearby-opponent Pressure Swing, shot/outcome, goal/corrected score, recovery/control change and possession | Relevance and independent football validity are not established |
| Incident grouping, priority, human approval, suppress/retract, live expiry and history-only approval | Need to know whether a producer can choose and review comfortably during play |
| Source state separate from approved text; immutable revisions and correction invalidation | Existing correctness needs a more understandable correction experience |
| Casual/analyst, English/Spanish, player/team focus, evidence and recap | Audience differences need a clear demo and human comprehension evidence |
| Durable Director/Reviewer outcomes and real-model verification | Consequential decisions are harder to see than raw attempt/status codes; superiority unproven |
| Return-to-live control, explicit segment end and no automatic new match | Catch-up covers the segment; no explicit “since my last visit” interval |

Existing [verification](../../evals/live-match/verification.md) records 21/25
opportunities with at least 15 seconds of review time in each latest dual-stream
scene (84%), below the proposed 95% gate. One scene missed an expected control
change through model abstention/rejection. These are authored related scenes,
not independent matches. Preserve these results; do not relabel them as success.

## Priorities and dependencies

Effort ranges below are rough engineering timeboxes, not delivery guarantees.
Participant availability is separate. Stop adding scope when it threatens the
working submission. No numerical judging-score increase is predicted.

| Order | Work | Evidence / inspiration | Rubric contribution | Effort / dependency |
|---|---|---|---|---|
| P0 · EV01 | Freeze a specific problem, audience and claim boundary; prepare short pitch | E3, E5, E8; The Ninety Labs' concrete framing | Impact, presentation, category fit | 1–2 h; first |
| P0 · EV02 | Run a small paired producer/viewer study and document task failures | E1–E4; no current participant findings | Impact, UX; informs technical priorities | Prepare 1–2 h using existing materials; sessions depend on people |
| P1 · EV03 | Make each selected story an understandable editorial decision, with plain-language evidence | E2, E3, E7, E10; MatchMind's explicit questions | UX, agentic design, implementation | 4–8 h; EV01, then EV02 findings where available |
| P1 · EV04 | Show two audience previews from the same approved facts | E4; Virtual Studio Crew's immediate comparison | UX, personalization/category fit | 2–4 h; EV03; no new model role |
| P1 · EV05 | Add approved catch-up since a stated time, with correction context | E1, E7, E9; a testable extension beyond generic recap | Impact, UX, correctness | 6–12 h; EV03 and frozen correction cases |
| P1 · EV06 | Address actual review bottlenecks and expose meaningful agent decisions | E2, E5; current failed timing gate and competing live workflows | Implementation, agentic design, impact | 4–8 h investigation; code scope depends on measured cause |
| P0 · EV07 | Package and rehearse an honest working submission | Current contest rules and public-demo accessibility gap | All five, especially presentation/category fit | 2–4 h plus authorized release work; baseline can ship without optional P1 items |
| Later · EV08 | Define a small graphics-partner cue export, only with an integration task | Challenge rendering path; PitchPulse/Studio Crew advertised exports | Applicability, technical/category fit | 4–8 h spike; after pilot, not deadline-critical |

EV02 can recruit/run while independent engineering work proceeds, but its outcomes
must remain pending until actual participation. Do not fabricate a favorable
research conclusion to unlock a feature. EV07 runs throughout; unfinished P1 work
must not delay an honest baseline submission.

**Recommended deadline cut:** complete EV01, prepare/run EV02 where people are
available, and finish EV07 against the working baseline. Take EV03's copy/evidence
clarity and EV04's preview as the first small engineering slice. EV05 is the next
substantive feature; include it before submission only if its correction tests and
regressions finish in time. EV06 begins with measurement of existing records;
do not launch a broad agent experiment or cloud migration at the expense of a
working submission. EV08 and the deferred features stay out of this deadline cut.

## EV01 — Explain the problem in product language

Use the pitch paragraph in the evidence brief as a starting point. Identify the
primary operator as a producer/editor; the viewer is the recipient, not someone
expected to approve evidence. Name the source as simulated live data.

Replace vague “moments” with “suggested explanations” where appropriate. Explain
the decision with an actor and change: “Fewer opponents nearby after this pass,”
not only a distance or an arbitrary importance label. Keep the qualification that
nearby opponents are a proximity measure.

**Acceptance:** a first-time reviewer can state who uses the product, what arrives
automatically, what needs approval, and that the demonstrated match is synthetic.
Capture their own words before explaining. A developer reading the page is not
participant evidence. Keep model details/access help in a disclosure; retain a
short visible simulation label and truthful AI/fallback status.

## EV02 — Test a job, not whether someone likes the idea

Reuse [the short live guide](../live-match-demo.md#five-minute-reviewer-task) and
existing [reviewer materials](../reviewer-pack/README.md); do not create another
competing study pack. Start with two football-content producers/editors if
available, four first-time viewers with different football familiarity, and a
Spanish/football reviewer. Record overlapping roles; do not count them as extra
independent people. This is formative research, not a statistically powered trial.

Ask producers to select one explanation worth airing from competing incidents,
check it, and approve or dismiss while the feed continues. Use a matched baseline
of the same synthetic facts/timeline without suggested explanations. Counterbalance
the order and use equivalent scenes to reduce answer memorization. Ask whether
their actual existing tool would already solve the task better.

Ask viewers to describe what changed and identify the involved players, then
rejoin after missing an interval. Compare the explanation with a bare-stat view.
Ask what the observation cannot establish; include a corrected goal and an unknown
shot outcome. Observe whether checking evidence causes them to lose the live play.

Record per-person task completion, assistance, time, edits, reasons for dismissal,
unsupported interpretations, match events missed during reading, and preference.
Record AI/template/fallback mode, scene, version and actual model provenance.
Report counts and paired observations, not generalized time savings or retention.

**Decision rules:** any critical score/publication misconception blocks a readiness
claim. Repeated confusion in two sessions triggers a content/UX revision. If both
producers prefer their existing workflow, investigate integration before expanding
the desk. With too few participants, report the limitation and keep the impact
claim pending. Freeze prompts and scoring before final sessions.

## EV03 — Show why this story deserves attention

Refine the existing queue and evidence view; grouping, approval, history and
return-to-live already exist. A selected card should answer:

1. **What changed?** One supported, audience-readable sentence.
2. **Why highlight it now?** A bounded contrast or observed outcome. If there is
   no useful comparison, say so or keep it as a factual update; do not invent one.
3. **What supports it?** The existing before/event/after visual, named actors,
   explicit interval, measurement and missing-data qualification.
4. **What can I do?** Approve the exact version for live/history, dismiss, or inspect.

Show exact evidence codes/hash under “Technical source details.” The first layer
should say what was observed and what changed after a correction. Do not hide
missing coverage to simplify the screen. Preserve unknown versus observed
contested possession. The shared clock stays visible during inspection.

Expose a compact existing-workflow decision: Director's selected angle, Reviewer's
accept/change/reject decision and the supported fact involved. An injected failure
must be labeled as an exercise. This is a decision summary, not private reasoning
or a new conversational agent.

**Acceptance:** desktop/390 px phone and keyboard checks; English/Spanish actor,
unit, interval and qualification parity; no overlapping ball/player numbers;
all families including unknown outcomes; correction and stale-approval exercises.
Blind football reviewers judge supported relevance separately from fact accuracy.

## EV04 — Make personalization visible immediately

Add an optional producer preview of **Casual viewer** and **Analyst** side by side
for the selected revision, with a Spanish toggle. On phones, use a compact toggle.
Reuse validated variants; preview must never publish a draft. Indicate draft or
approved status and preserve exact package/revision binding.

**Acceptance:** a reviewer can see a meaningful difference in detail, explain that
both use the same facts, and approve only once. Viewer focus still filters relevant
approved material. No new model calls are required just to switch previews.

## EV05 — Catch up without retelling the entire segment

Extend the existing approved recap with “Since I joined” / “Last minute” choices,
an explicit from/to interval and current source score. Let the viewer choose the
interval; local last-visit state should not require an account. A share link must
not expose another viewer's history or preferences.

Select only approved, currently valid explanations; reuse grouping and immutable
facts. Explain an empty result as “No approved explanations in this interval,”
not “Nothing happened.” Clearly separate source-confirmed score updates from
producer-approved explanation text. Do not count uncovered time as no incidents.

Add a concise correction notice when previously displayed approved material was
withdrawn. Show the supported change and time; show a reason only if the source
provides it. Do not leave old wrong text in an accessible “corrected” summary.
Keep full technical lineage behind evidence details. Preserve an appropriate
private audit trail separately from public withdrawn content.

**Acceptance:** join late; refresh/reconnect; unknown last-visit time; interval with
no approvals; duplicated/late events; scorer/score correction after approval;
correction outside the selected recap window affecting a story inside it;
player/language changes; API restart; segment end. No future observations, stale
claims or new causal links may enter the recap. Readers of old packages and their
hashes remain unchanged.

## EV06 — Make live usefulness measurable

Use current durable traces to separate evidence availability, queue wait, model
time, review time and display time. Add a missing measurement only when needed;
do not confuse occurrence time with receipt or browser display. Inspect misses by
family and reason before changing scheduling or thresholds.

Compare current suggestion volume with a more selective editorial policy on
frozen scenes. Count useful accepted stories, dismissed duplicates, expired work,
missed important updates, viewing interruption and model cost. Keep every supported
family available; reducing editorial noise must not silently remove recoveries,
shots or possession. Unselected source events remain visible as source state where
appropriate, never automatically published explanations.

Retain the existing 95%/15-second target and failed baseline. If producer evidence
justifies a different expiry/review policy, document it before a new run and report
old/new policies separately. Never lengthen expiry after observing failures and
declare the original gate met.

Use the same tools/facts/budgets to compare deterministic selection, a substantive
single-agent baseline and Director/Reviewer on a small independently reviewed
set. Count abstentions, false rejection and invalid selections as well as repairs,
latency and cost. Existing model roles can improve the result; role count alone
does not establish that. Reuse the prepared comparison harness and human packets.

**Acceptance:** continuous 1×, no pauses/seeks/auto-approvals, separate per-family
results; missing observations, corrections, disconnect/restart and model failure;
old package compatibility; original regression reported unchanged; no usefulness
or multi-agent-superiority claim without the corresponding independent evidence.
Paid evaluation needs an explicit bounded run budget; this research does not start it.

## EV07 — Deliver the story inside the deadline

The [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md)
close submissions on 27 October 2026, 23:59 Pacific. Treat public source, judge
access and a functioning video under two minutes as delivery work, not feature
work. Keep deployment, repository visibility and publication separately authorized.

Recommended 110-second structure:

| Time | Show | Point |
|---|---|---|
| 0–15 s | One qualified research finding and the producer/viewer job | Why this is a real task, without claiming product-market fit |
| 15–30 s | Synthetic live clock advances; AI suggestion arrives | Facts continue while AI/editorial work happens |
| 30–55 s | One before/after explanation, useful evidence, Director/Reviewer decision | Explain a specific observed change; no tactical-cause claim |
| 55–75 s | Human approval → viewer output → casual/analyst and Spanish | Controlled publication and meaningful personalization |
| 75–95 s | Source correction and recap/catch-up | Accountability after publication; use existing recap if EV05 is unfinished |
| 95–110 s | Architecture, measured result and remaining limitation | Microsoft technology tied to behavior, honest pilot status |

Use an uninterrupted live excerpt where feasible. Disclose cuts, time jumps,
accelerated simulation and prerecorded demonstrations. A four-minute source segment
does not need to run in full in the submission video. Do not present a sped-up
demo as a real-time latency measurement.

Before release, make the README clearly identify which build is current, how to
run it, which paths make AI calls, and what remains unverified. Remove conflicting
historical instructions from the main path without deleting delivery evidence.
Verify the judge entry route on a fresh browser and phone. Do not direct judges
to the older Azure build as if it contains the latest live iteration.

## EV08 — Conditional partner output

An existing web overlay/state endpoint is not a certified graphics integration.
If a producer needs this, define a versioned cue carrying match/period clock,
story/revision/hash, approved text, slot, priority, eligibility, hold duration and
withdrawal/replacement semantics. Validate it with a tiny consumer and reconnect/
correction tests. Do not claim OBS, Vizrt or TV synchronization from JSON alone.

## Add, improve, simplify, defer

| Decision | Scope and reason |
|---|---|
| Add next | Optional audience preview; interval-specific approved catch-up and visible correction context, subject to the pilot and deadline |
| Improve now | Specific problem/pitch; bounded “why selected” wording; readable evidence; meaningful agent-decision summary; measured review bottlenecks |
| Simplify | Keep technical IDs, source hashes, model plumbing and access instructions in details; reduce repetitive suggestions and jargon; avoid implying every event is a highlight |
| Preserve | All required families, explicit unknowns/coverage, immutable packages, approval policy, current source state, English/Spanish, focus, audit and offline mode |
| Defer | Full chat, auto-eventing/vision, xG/counterfactuals, Chaos Index, calibrated difficulty, tactical turning points, 3D redesign, extra agent roles and extra cloud services |
| Conditional later | Read-aloud of approved copy after accessibility interviews; independently defined ball/shot speed if users ask for it and source sampling supports it; graphics cue export with a real integration task |

Speech can be useful, but generic text-to-speech is not proof of an accessible
football description service. Ball speed can be measured, but a synthetic 2D
trajectory is not enough to claim a real 3D shot-speed product. Neither should
displace the core workflow before the deadline.

## Completion and limits

For this proposed iteration, retain engineering correctness and add evidence of
task usefulness: a first-time producer publishes a supported story during play;
a viewer understands its bounded meaning; missed time and corrections remain
clear. Log failures and participant outcomes separately from automated tests.

Without people, we can complete engineering, preparation and a truthful demo,
but must leave usefulness and adoption unvalidated. Without an authorized release,
we can prepare the submission but must leave public hosting/publication pending.
These recommendations do not supersede source availability, publication,
correction or compatibility rules in the governing implementation plans.
