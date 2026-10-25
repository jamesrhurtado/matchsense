# Synthetic football iteration: credible scenes and fair agent evaluation

25 October 2026, America/Lima. **SD01–SD04 implemented and locally verified;
SD05–SD08 remain planned.** Based on the
[source audit and primary research](../synthetic-data-research.md). This plan
adds data and validation to the current live explanation product. It preserves
the governing match-coverage event definitions and current publication rules.

First-slice delivery: six development parents, twelve paired specifications,
twenty-four observation exports, a frozen movement profile, independent checks
and an opt-in application catalogue. See [dataset/startup guide](../synthetic-dataset-v1.md)
and [verification](../../evals/synthetic-vnext/verification.md). Original default
replays and source/package hashes are preserved. No held-out set, new paid model
comparison or participant result is claimed.

## Outcome and scope

First-time viewers should see a coherent football passage: players support the
ball, keepers respond plausibly, possession and attempts have continuity, and
ordinary play does not constantly demand attention. The same source must exercise
all existing families and support a fair test of Director/Reviewer collaboration.

Deliver a versioned constrained scenario generator, observation-only exports,
independent validators, distinct development/evaluation inputs and documented
evidence. Use the existing 2D pitch, source stream, evidence packages, producer
queue, viewer modes and recap. Generation stays deterministic and offline.

No full football video game, new AI roles, training run, real-feed integration,
xG, pass-difficulty probability or tactical-cause detector is included. No public
release, deployment, paid evaluation or participant finding is implied by the
research. Existing model evaluation budget procedures still apply.

## Required boundaries

| Layer | Contains | May reach runtime agents/viewers? |
| --- | --- | --- |
| Authoring/world state | Episode schedule, seed, complete positions/control and future outcomes | No. Generator/evaluation only. |
| Observed source | Supported existing observations, identities, occurrence time, availability, revisions and explicit missingness | Yes, only through existing delivered-time source access. |
| Evaluation key | Expected facts/coverage, permitted claims, forbidden implications, earliest knowable time, expected correction effects | No. Separate files and imports; tests enforce boundary. |
| Approved package | Exact evidence-bound explanation and audience variants | Existing producer approval and source-validity policy only. |

Never expose scenario names such as “pressure escape” or hidden outcomes through
runtime IDs/metadata as shortcuts. IDs remain opaque. Authored scenario meaning
does not authorize a causal statement in output. Unknown control is not observed
contested control. Goals and scorer/assist/recovery attribution require the
existing explicit observations.

## Ordered tickets and exit conditions

Estimates are engineering planning ranges, not commitments or measured delivery
times. SD01–SD04 are the first useful slice. SD05–SD08 complete the evaluation
and product handoff; participant work has its own status.

| Ticket / priority | Work and main locations | Dependencies / evidence to finish |
| --- | --- | --- |
| **SD01 · P0: Freeze definitions, profiles and ancestry** | Add a vNext dataset card and manifest. Record units, 10 Hz observation sampling, period direction, scenario assumptions, movement profiles, event outcomes, family coverage, lineage groups and split rules. Snapshot original runtime/package hashes. | First. Explicit design bounds and licensing/provenance decisions; old regression untouched. Suggested 1–2 h. |
| **SD02 · P0: Shared episode state and coherent movement** | Add a new generator module beside existing modules. Reuse contracts/serialization, with possession/support/flight/loose/dead/unknown states, ball-linked roles, ball-responsive keeper paths and bounded smooth trajectories. | SD01. Two physically distinct developer passages render coherently, pass independent checks and reproduce exact export hashes. Suggested 5–9 h. |
| **SD03 · P0: Independent validation** | Extend `simulator/validate.py` additively or add a separate vNext validator; independent calculations and failure reports. Add acceleration/turning diagnostics, event/actor/ball alignment, state transitions, period direction and observation-cutoff checks. | SD01; develop alongside SD02 against frozen valid/invalid examples. Every deliberate defect is detected by its intended check, not a coincidental schema error. Suggested 3–5 h. |
| **SD04 · P0: Diverse developer parents and behavioral pairs** | Add six distinct authored developer parents, each with two controlled case specifications; build clean and fault views. Maintain separate episode ancestry and transformation metadata. | SD02–03. Twelve specification cases with all supported families and quiet/unknown cases, independent expected facts and full coverage report. Suggested 3–5 h. |
| **SD05 · P1: Held-out set and fair comparison** | Freeze six further structural parents and twelve case specifications before tuning to them. Adapt existing T/S/M comparison harness to the mixed-event workflow, same evidence/rendering/guardrails and adequate single-agent self-check. Optional Director-only ablation stays evaluator-only. | SD03–04. Unseen-input provenance, all terminal outcomes, matched conditions, repeated trials and honest result. Model run follows existing verified-rate/cost controls. Human editorial ratings remain pending until participants. Suggested 3–5 h harness work, run time separate. |
| **SD06 · P0 for changing the default: Two coherent live demos** | Compose two distinct 4-minute scenes from developer material: a restrained normal match passage and a labelled correction/fault demonstration. Export new IDs/catalogue entries. | SD03–04. Every family works through producer/evidence/approval/viewer/recap; desktop/mobile continuous 1×; old IDs remain unchanged. Default selection changes only after these checks. Suggested 2–4 h. |
| **SD07 · P1: Review and useful agent demonstration** | Prepare concise football/Spanish review packets; retain authentic Director/Reviewer intervention traces and acceptance/rejection outcomes. Use existing producer review UI. | SD05–06. Engineering prepares packets and reproduces records. People must supply realism/usefulness judgments. If no actual intervention is observed, report that; injected faults stay labelled tests. Suggested 1–2 h preparation. |
| **SD08 · P0: Compatibility and delivery record** | Run original regression separately from new data checks, build and relevant browser checks. Update dataset card, README/demo instructions and decision log with actual counts, unresolved failures and limits. | All shipped tickets. No rewritten original expectations, stored package mutations or unsupported superiority claim. Suggested 1–2 h. |

The complete engineering estimate is roughly 19–34 h, plus evaluation running
time and participant availability. With the submission deadline close, prioritize
SD01–SD03 and a small SD06 developer preview. Do not claim the full 24-case
library, independent validation or comparative results from that smaller slice.
No last-minute simulator replacement should displace submission access/video work.

## Movement and match coherence

- Use explicit initial formations and contextual support targets. Team shape may
  shift with the ball/episode; all players must not orbit a fixed location or
  chase the ball together. Treat authored roles as movement instructions, never
  inferred tactical intent in explanations.
- Use velocity-continuous paths with bounded acceleration and deceleration.
  A smoothing pass must preserve event contact points, timing, control and
  measurement windows. Recheck proximity and pass context after smoothing.
- Define speed/acceleration/turn limits as documented **generator profile choices**
  before assessment. They are not universal human limits or FIFA standards.
  Keep existing legacy 10 m/s player and 30 m/s ball checks as legacy behavior;
  the new profile may be stricter and must distinguish ball flight from player motion.
- Keepers support build-up, adjust angle and depth, and approach explicitly
  scripted saves/collections. Legal sweeper movement is allowed. Flag implausible
  keeper behavior for scene review; do not impose “always inside the goal area.”
- Script passer release, ball flight and receiver contact as a continuous episode.
  Explicitly distinguish opponent interception, loose-ball collection and restart.
  A touch/contact may create close players; overlap duration/proximity is a
  diagnostic with a declared tolerance, not a blanket ban on proximity.
- Saved shots have a coherent defending intervention and follow-up state. Blocks,
  off-target exits, rebound or stopped ball have matching paths and source events.
  Keep unknown shooter/outcome cases. A source-confirmed goal stays distinct from
  geometric plausibility; corrections may change what the source believed earlier.
- Maintain physically continuous dead-ball/restart time or explicitly label a
  discontinuity. Avoid moving a ball through the pitch while calling it a carried
  live ball. End-of-segment is distinct from the end of a full football match.
- Include routine circulation and recovery periods without a forced highlight.
  Event and suggestion rates are measured design properties of this small set,
  not claimed representative league averages. Viewer quiet mode remains unchanged.

## Parent and case matrix

Minimum full target: **12 structurally distinct parents**, six development and
six held-out. Each has two controlled specifications, for **24 cases** total.
Keep names below in authoring/reference files only. Two live demos are composed
from development material and are not additional independent parents.

| Parent type | Developer example and paired question | Held-out construction must change |
| --- | --- | --- |
| Support and release | Multi-player circulation, observed nearby-opponent change; same pass geometry with different available opponent evidence | Participant sequence, support movement, ball route and timing, not just shirt/name/seed |
| Interception and retained control | Opponent pass intercepted and retained versus a loose ball collected after unknown control | Origin, acquisition player/zone, preceding possession and next action |
| Shot and second phase | Saved shot with rebound/collection versus blocked attempt with a different follow-up | Shooter/keeper paths, event order and resulting control; avoid mirrored replay |
| Goal and revision | Pending → confirmed goal versus later cancellation/attribution correction using valid lineage | Different build-up, shot location, delivery timing and restart geometry |
| Possession and quiet play | Ordinary circulation and an explicit summary window; paired missing observations reduce coverage | Different durations/handovers and unknown/dead-ball interval placement |
| Competing stories and limits | Two close incidents with sufficient evidence versus incomplete/late observations; preserve uncertainty and relevant history | Different historical sequence, actors, opportunity spacing and availability |

Pairs belong to the same parent and are not independent samples. A name change,
reflection, timing jitter, parameter seed or delivery fault never creates a new
parent. Different parents may share low-level interpolation/serialization; they
must not share the authored episode/trajectory skeleton. Report this procedural
relationship even after structural separation. Independently authored here means
separate scene constructions; it does not mean independently reviewed by experts.

Freeze the group split before expansion. Author held-out inputs without model
feedback or prompt tuning on them. If the same developer authors both splits,
disclose it. Once inspected for tuning, a held-out set becomes development data;
a new final set is required. SD01–SD04 now deliver the six development parents;
the six held-out parents remain uncreated. The research itself authored neither.

Across these specifications include a period transition with explicit period
metadata and attack-direction change, and an excerpt with a declared initial
score. A boundary excerpt must start near the real period boundary or explicitly
represent a declared discontinuity; never compress an entire half into four
minutes and describe it as continuous 1× football. Retain shot outcomes beyond
saved/blocked/goal, including off-target and unresolved, and recovery cases with
unknown previous control or no attributable player.

### Controlled behavioral changes

Keep separate expected relations instead of expecting every case to produce an
identical sentence:

| Change | Expected relation |
| --- | --- |
| Reflect pitch and attack direction together | Distances and forward progression invariant; actor IDs remain correct |
| Rename players, including duplicate display names | Measurements and factual identities invariant; presentation disambiguates teams |
| Remove relevant opponent observations | Coverage/claim confidence boundary changes; no invented pressure value |
| Team retains ball but receiver passes it onward | Team retention remains true; receiver's individual control duration changes |
| Delay shot resolution or goal confirmation | Outcome/score unavailable before delivery; no future leakage |
| Retransmit an exact event | One logical incident, explanation and score effect |
| Correct a previously published fact | Dependent approval invalidates; viewer/history/recap remove stale text |
| Keep outcome unresolved | Unknown outcome or abstention, never fabricated scorer/assist/cause |
| Add routine circulation | No mandatory story for each action; measure editorial false positives |

Fault injection operates on exported observations separately from world motion.
It must not make arrival-order coordinates look like physical jumps. Define any
intentional corrupted observation as an invalid/stress case; do not include it
in a clean-scene realism score. Use existing source-revision semantics.

## Validation and acceptance

Three independent result groups are required:

1. **Dataset integrity:** schema, unique identities, reproducible byte hashes,
   legal lineage, roster/profile/units, no reference/seed/future leakage, no
   developer/final parent overlap. Original exports/packages retain their hashes.
2. **Football/observation coherence:** all clean new scenes pass declared movement,
   actor/ball/event timing and state checks. Report derivative distributions and
   joins, missingness/coverage and event counts. Use standalone calculations,
   not the production detector as the reference oracle. Numeric check success
   remains distinct from football reviewer acceptance.
3. **Product behavior:** all existing families appear across the set with relevant
   evidence and focus, English/Spanish variants, approval and recap. Test quiet
   intervals, unknowns, duplicate/delay/correction, restarts and uninterrupted
   desktop/mobile playback. Source clock/score must advance without AI or approval.

Store a case-level report with denominator, exact failure, source/profile version,
hash and ancestry. Some intended-negative cases should fail validation; report
their expected rejection separately from clean-scene passes. Keep software unit
coverage separate from model-quality and human findings.

Do not lower the existing 95% / at-least-15-seconds review target to make new
scenes pass. Report eligibility-window conflicts explicitly, alongside delivered
evidence readiness, worker queue, model workflow, producer review and browser
display timings in their appropriate clock domains.

## How this strengthens the agentic entry fairly

Reuse the existing template baseline, strong single-agent self-check and
Director/Reviewer approaches. Give them the same delivered observations, tools,
factual renderer, validators, publication policy and declared resource ceiling.
Record actual consumption and opportunity cutoff; never reduce the baseline's
evidence or self-check to create a multi-agent win. Keep the one-role ablation
evaluation-only. New-family strategy support must be verified before claiming
these adapters already compare the current live product.

Run at least three trials per selected case/approach for an initial repeated
comparison, with case/arm order counterbalanced. At the full target that is 216
outcomes for 24 cases and three main approaches; these remain 12 parent groups,
not 216 independent football situations. Verify the deployed model/version,
current rates, maximum calls/tokens and spending cap before any paid execution.
Run deterministic smoke and contract checks first. A smaller run is acceptable
with its reduced scope explicitly reported.

Report supported-claim failures, missing useful facts, appropriate abstention,
false rejection, deadline misses, fallback, cost, calls and repeated-run stability.
Count a Reviewer intervention only when it changes the proposal or disposition;
separate a meaningful supported correction from cosmetic edits and deterministic
guard rejection. Reviewer's changed output is not automatically an improvement.
Measure accepted/rejected intervention correctness against independent facts and
blind editorial ratings where required. Do not expose the key to either agent.

No mandatory win rate is invented after observing results. A superiority claim
requires an observed, repeatable benefit on a prespecified outcome with its
latency/cost tradeoff and grouped uncertainty disclosed. If no benefit appears,
record it and examine complementary agent responsibilities; do not manufacture
errors or add agents for appearances. Synthetic actor/role complexity alone
cannot establish sophisticated orchestration.

## Human review and demo handoff

Prepare side-by-side clips or pitch replays with source facts and neutral prompts:
“What seems physically implausible?”, “What can be concluded now?”, “What should
the producer explain, if anything?” Ask football reviewers about continuity and
unsupported tactical implications. Ask producers about review time, and viewers
about understanding and missed match action. Review Spanish separately.

Recruitment, ratings and findings stay pending until people participate. A human
can accept a useful story from any comparison arm; the evaluation must allow it.
Avoid feeding the desired “multi-agent wins” conclusion to reviewers.

For the later submission, show one new coherent passage, one substantive observed
agent decision (if available), audience choice and correction handling. Credit
the dataset as original constrained synthetic sequences and show reproducibility
briefly in the submission material. Do not describe it as a validated full-match
simulator, calibrated tactics or successful real-feed integration.

## Judging connection and stopping rule

| Criterion | Evidence this iteration can add |
| --- | --- |
| Technology | Reproducible generator, independent checks, compatibility and explicit data-quality report |
| Agentic design | Genuine evidence-sensitive decisions and fair comparative traces, rather than role count |
| Impact | Better material for participant tasks; benefit claims still depend on those tasks |
| UX | Believable movement, understandable varied play and intentional quiet periods |
| Category fit | Documented creative football-realistic data through all five existing pipeline stages |

Stop expanding the library once the declared target and important failure classes
are covered. A smaller verified slice is preferable to claiming an unfinished
full library. Preserve time for live review, participant testing and the required
submission. Update ticket status with actual evidence. SD01–SD04 are delivered as
the development-data slice; SD05–SD08 retain their planned status. Necessary
compatibility/build/browser checks were run for this slice without claiming the
broader final evaluation or release gates complete.
