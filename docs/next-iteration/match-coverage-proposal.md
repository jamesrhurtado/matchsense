# WHY/NOW — proposed broader match coverage

Status: historical proposal and scope review, 23 October 2026. James subsequently requested the [implementation plan and MC01–MC10 backlog](match-coverage-implementation-plan.md), which selects the required next-iteration scope. This proposal adds no implemented functionality; use the implementation plan for priorities and acceptance checks.

## Product direction

Help a viewer understand the important events of a match: what happened, what the available evidence shows, and what changed. Preserve inspectable evidence and producer approval while expanding beyond the current pass story family.

The owner's first-use feedback identifies a product hypothesis to test: a companion covering goals, shots, possession and recoveries may be more useful than one focused on selected passes. Validate this through a varied match demo and viewer feedback; breadth alone does not establish usefulness.

## Why the existing plans did not deliver these features

### Original planning notes: broader event coverage was already contemplated

A subsequent review of the five original Obsidian planning notes changes the historical picture. The repository's iteration plans are not the earliest product specification. The original notes cite `Inside the Game.docx` and `Inside the Game Hackathon Ideas 2.pdf` as inputs; those original attachments were not available in the project checkout for this review.

- **01 Project Brief**, lines 42–50: the flagship demonstration explicitly centers on explaining a pass under pressure. It prohibits claiming proof of tactical causation. But its planned-submission data section, line 68, explicitly includes passes, possession changes, pressure and shots.
- **05 Synthetic Dataset Specification and Generation Plan**, lines 54–67: the first working slice requires pass events and possession transitions. The next section, **Extend once the first slice works**, calls for shots and outcomes, tackles/recoveries, pauses and period transitions, alongside longer sequences and feed faults.
- That dataset note, line 189, names later `shot_started`, `shot_resolved`, `tackle` and `ball_recovered` event types and says score should update only when the goal outcome becomes available. This contemplates goal outcomes and score handling, without specifying a complete goal-explanation workflow.
- **02 Technical Implementation and Codex Brief**, lines 190–194: starts with pass, possession-change and play-state events, then calls for coherent shot/recovery/tackle/period extensions.
- **03 Submission Demo**, line 22: allows a later shot but requires the pass insight to be meaningful without a goal. A shot was optional for that recording, not absent from the overall data direction.
- **04 Workflow and Audience Explained** stays centered on pass evidence; possession and score provide context. It does not define separate shot/goal story workflows.

The current runtime event union in `engine/contracts.py` contains pass start, pass resolution, possession change and play-state change. Shots, goal outcomes, tackles and recoveries have no separate typed event support there. Possession changes are already represented as observations, but not as an independent story family or a possession-percentage overview.

**Finding:** the original flagship was pass-focused, but the original data direction was broader. Some planned extensions remain undelivered. Later plans explicitly narrowed/deferred this area; the reviewed history does not establish that the original broader extension list was reconciled item by item. It is therefore too strong to describe every missing feature as merely a new idea or to conclude that all original planning requirements were fulfilled.

### Later repository iterations

- The earlier `README.md` in this directory lists shots/xG under **Defer**, rather than **Commit to these improvements**. It says to revisit them after submission or core gates.
- The later `grand-prize-90-plus-plan.md`, section 3, keeps new event families conditional. Its category-breadth decision proposes possession recovery followed by sustained possession only if user findings justify expansion.
- That plan requires defensible measurements before introducing shots/xG. Neither document commits to a goal-explanation feature.
- The implementation record documents work on the scoped pass workflow, contextual comparisons, rendering, evidence, approval and verification. It does not report completed goal or shot coverage.

The later records support a narrowed scope, but do not establish why each earlier extension was left out. They also do not establish a promised complete goal-explanation feature. A feature mentioned in an AI-written plan can be a commitment, a staged extension, an option, or an explicit exclusion; those statuses must remain visible in future handoffs.

## Proposed feature list

Priority and order below are recommendations, not existing commitments. Each item needs a data contract, examples, validation, producer controls and viewer presentation before it is considered delivered.

| Feature | Viewer value and example | Required support | Proposed stage |
|---|---|---|---|
| Match state and event timeline | Know the period, match clock, confirmed score and selected events | Explicit match-state and score events, stable IDs, correction handling; keep match clock distinct from demo playback | 1 |
| Goals and score changes | Understand who scored, when, and the confirmed new score | Explicit goal attribution and confirmation/reversal status; update affected stories and score on correction | 1 |
| Shots and outcomes | Follow attempts even when they do not become goals | Explicit shot event, actor, team, time, location when available, and provider-defined outcome such as saved, blocked or missed | 1 |
| Possession overview | Understand who had the ball over a clearly stated interval | Defined team-control intervals, treatment of loose/dead/unknown time, denominator and coverage shown with any percentage | 1 |
| Recoveries and turnovers | Understand when possession changed and what followed | Explicit event or separately validated control-change rule; distinguish a recovery from a restart and confirm subsequent possession | 1 |
| Connected attacking sequences | Revisit the observed passes, carries and shot leading to a selected event | Sequence boundaries and event links; qualify as observed buildup without claiming a particular action caused the goal | 2 |
| Set pieces | Follow corners, free kicks and penalties with confirmed outcomes | Typed awarded/taken events and links to subsequent play; avoid treating every restart as a significant story | 2 |
| Fouls, cards and substitutions | Understand interruptions and changes in personnel | Authoritative event attribution, status and corrections; lineup validity over time | 2 |
| Match-wide catch-up | Receive a varied account of confirmed goals, attempts and other selected moments | Approved mixed-event history, correction-aware score, transparent selection rules and links to evidence | Basic version in 1; richer version in 2 |
| Editorial selection and alert limits | Receive a manageable set of useful moments instead of a story for every action | Versioned selection, duplicate grouping, producer overrides and bounded alerts; test usefulness with viewers/producers | Basic version in 1; tuning in 2 |
| Advanced chance/tactical analysis | Potential later explanations of chance quality or tactical patterns | New definitions, suitable data, independent validation and, for xG, an appropriate evaluated model | Later research |

Possession already appears in current pass evidence as a bounded retention check. The proposed possession overview and independent recovery stories are additional features. A goal report can be useful without xG or a tactical explanation.

## Implementation sequence

### Stage 0 — establish the event foundation

1. Define a versioned common event envelope: match, period, occurrence time, availability time, event ID, type, actor/team, source, revision and status. Preserve unknowns.
2. Add event-specific contracts for shots, goals, possession intervals and control changes. Keep provider confirmation separate from producer publication approval.
3. Extend the current observation-only runtime, repository and narrative contracts deliberately. The current incoming-feed boundary does not already accept these event families.
4. Author varied synthetic fixtures with unsuccessful attempts, goal reversals, missing data, duplicate events, delayed outcomes and corrected attribution. Keep evaluation answers separate from runtime observations.
5. Preserve existing pass packages and their approvals. Document migration and compatibility before replacing any stored format.

### Stage 1 — demonstrate a recognisable passage of football

Implement match state, goals, shots, possession and recoveries, with a mixed-event timeline and basic approved recap. Demonstrate a varied short segment: possession change, buildup, an attempt without a goal, and a separately confirmed goal. The producer should see event-specific evidence rather than a pass-specific panel reused unchanged.

Acceptance checks:

- Every supported event type has positive, negative and correction examples.
- A shot does not imply a goal; an uncertain outcome stays uncertain.
- Goals and scores reconcile with confirmed source events, including reversals. Unapproved narrative content remains protected.
- Possession calculations expose the interval, coverage and denominator; incomplete data does not produce a misleading percentage.
- A recovery is distinct from a pass reception or a routine restart.
- Corrections invalidate affected narrative approvals and recaps without changing unrelated stories.
- English and Spanish explain the same approved facts, with relevant player/team focus.
- The viewer sees a varied recap without repeated descriptions of one shot/goal sequence.
- Continuous playback checks establish that the wider event workload remains reviewable.
- First-time viewers can identify what happened, inspect its evidence and explain why the selected story helped them. Record failures as well as successes.

### Stage 2 — deepen coverage based on findings

Add connected sequences, set pieces, disciplinary events and substitutions according to data availability and observed user needs. Improve selection and recap variety using the Stage 1 findings. Real-feed integration is a separate track: synthetic coverage must not be described as working vendor integration.

### Later research

Consider xG, tactical intent, defensive line breaks and broader tactical claims only with their own measurements and validation. They are not prerequisites for reporting confirmed shots, goals and score changes.

## Planning and handoff rules

For each selected feature, create an implementation ticket with an owner, dependencies, supported facts, excluded claims, UI behavior, acceptance checks and evidence of completion. Track **proposed**, **committed**, **implemented**, **verified**, and **deployed** separately. An AI-written plan is a specification to review and execute, not evidence of delivery.

The selected scope is now recorded in the implementation plan, active backlog pointers and decision log. The broader optional feature list here remains historical context; it is not all required for the next iteration.

## Source documents

- [Earlier scope: committed, conditional and deferred work](README.md)
- [Current improvement plan](grand-prize-90-plus-plan.md)
- [Implementation record](decision-log.md)
- [Existing pass and possession metric definitions](../metrics.md)
- [Current incoming observation boundary](../incoming-feed.md)
