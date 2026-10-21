# Evaluation and user research protocol

**Status:** proposed protocol, not completed results. Freeze case definitions, acceptance rules, model versions and budget before the corresponding run. The completed audit is in [agent-evaluation](agent-evaluation.md).

## 1. Questions to answer

1. Does the explanation convey specific, supported information beyond the current template?
2. Does a separate reviewer improve useful correctness compared with a strong single agent using the same evidence and tools?
3. Can a producer obtain and approve the explanation while continuous replay is still inside its display window?
4. Can casual viewers explain the passage correctly, and can analysts inspect its evidence?
5. Does player focus improve relevant discovery without inventing involvement?

Treat these as separate questions. Passing a publication test is not proof of comprehension; a good human rating is not proof of factual grounding.

## 2. Baseline and evidence preservation

Preserve `e62c043` and the three recorded cloud outcomes. The existing 196 backend tests, nine browser tests and 168 synthetic cases remain regression gates. Their passing counts cannot be presented as fresh model quality results.

Every run manifest records: commit, image digest where applicable, model/deployment/API version, prompt/tool/metric/renderer/schema versions, dataset/reference hashes, parent lineage, arm, trial seed if supported, temperature, budgets, start/end timestamps and configuration. Store raw test outputs securely with sanitized public summaries. No API keys or producer tokens belong in result files.

## 3. Fresh dataset design

**Discovery set:** 8–12 newly authored structural parents, visible to developers. Use these to diagnose and tune. These are not renamed or perturbed versions of the six existing parents.

**Final set:** target 24 distinct new structural parents, reserved before tuning: 16 eligible narrative opportunities and eight quiet/ineligible/insufficient cases. Run two trials per model configuration to observe variability. This is a small engineering comparison; it does not establish real-match generalization or population accuracy. The QA owner holds expectations outside runtime access. Repeat variants within a parent are not independent samples.

If authoring/review capacity only permits fewer parents, report the actual size and reduce conclusions. Do not inflate the denominator with 100 audience variants or repeated stochastic outputs. If testing causes tuning on the final set, seal fresh parents for the next final run or label the assessment as regression.

Include these case classes, with several attributes combined per parent:

| Class | Required challenge |
|---|---|
| Useful positive | Successful forward passage with supported retention; varied actors, distances, zones and geometry |
| Quiet negative | Ordinary/lateral/intercepted/missing-evidence situations; no unnecessary story/model invocation |
| Attribution | Receiver releases to a teammate while team retains possession; duplicate names across teams |
| Semantic contradiction | Proposed failure despite successful retention; unsupported line break/intent/chance/goal; polarity and subject changes in Spanish |
| Temporal correctness | Late outcome, missing confirmation, future-looking tool request, delayed correction, expired opportunity |
| Comparative context | Same present pass with different histories; two vs three valid prior passes; cross-team/period exclusion; historical source correction |
| Editorial usefulness | Similar consecutive eligible moments, a materially distinct moment, cooldown/remaining lifetime if implemented |
| Personalization | Relevant and irrelevant player focus; retracted/archived history; team identity ambiguity |
| Instruction isolation | Untrusted names/proposed wording containing instructions; invalid IDs/window expansion |

A football reviewer checks realism and claim meaning. Reference expectations are calculated independently of the production detector and reviewed against the generated observations; copying implementation outputs into expected answers would defeat the evaluation. Parent manifests and answers are evaluation-only.

## 4. Comparison arms and fairness

| Arm | Definition | Role in conclusions |
|---|---|---|
| T2 | Deterministic claim selection/rendering over the new allowed facts | Measures value beyond the structured factual baseline |
| S2 | Strong single agent with the same facts, read tools, structured renderer and bounded self-check/repair | Main comparator for orchestration benefit |
| M2 | Candidate Director + Claim Reviewer, with the same facts/tools/renderer | Tests independent role-context contribution |
| L1 | Frozen current workflow at baseline | Historical product anchor; different contract means this is not a pure role-count ablation |

Use T2/S2/M2 for the matched architecture comparison. L1 is run only on compatible scenarios and reported separately. Do not attribute every improvement over L1 to more/better collaboration when geometry, rendering or tools also changed. Report paired component ablations on discovery data: context on/off; reviewer present/absent; optional third Composer. Production still requires all approval guards.

Use the same underlying model/version, evidence cutoff, tool capabilities, mandatory deterministic checks and total token/call ceiling for S2 and M2. Permit S2 a competent prompt, equivalent tool access and meaningful self-repair; do not cripple it to favor multiple agents. Log actual resource use, not only equal maximums. A secondary equal-cost comparison is useful if the initial resource use differs substantially.

Randomize or interleave arm execution to reduce systematic effects from provider load. Separate cold/warm behavior. If shared quotas cause contention, serialize the quality benchmark and run concurrency as a separate capacity exercise. Capture complete rendered outputs, terminal outcomes, tool requests/results and observable decisions; private chain-of-thought is neither needed nor collected.

## 5. Run stages and spending bounds

1. **Offline smoke:** fake-provider contracts, contradiction probes, dataset leakage checks and all terminal outcome accounting. Zero model calls.
2. **Model discovery smoke:** four varied discovery parents, S2/M2 and compatible L1, one attempt each. Inspect all traces, usefulness and accounting. Stop on severe claim errors or usage gaps before a larger run.
3. **Discovery comparison:** expand to 8–12 parents and test only the architecture variants needed to resolve a specific question. Record all attempts, including experiments later rejected.
4. **Frozen final comparison:** 24 parents × two trials for S2/M2; T2 once per case. L1 is an optional compatible historical anchor, reported separately.
5. **Cloud integration/live timing:** small, separately counted release exercises; do not rerun the entire offline corpus through paid models.

With 16 eligible parents, two trials and two model arms, the final comparison schedules 64 eligible model workflows; at a shared six-call ceiling that is at most 384 model calls, before optional L1 or evaluator calls. Negatives should be gated with zero model calls; unexpected calls count as failures and still count toward the cap. A 32,000-token reservation per eligible workflow bounds that batch at approximately 2,048,000 reserved tokens, not a prediction of actual usage or a provider billing guarantee. L1 retains its historical eight-call bound and is budgeted separately.

Before execution, create a run manifest with `max_model_calls`, input/output token reservations, `max_estimated_cost`, rate-source/date/currency, deadline and concurrency. Include judge calls, failed requests and retries. Use current verified rates for the actual deployment and a conservative input/output mix. Reserve before dispatch, reconcile after, and stop scheduling when the budget is exhausted. Unknown usage consumes the reserved allowance until reconciled. Dollar amounts must not be inferred from the existing subscription credit balance. This planning handoff creates no recurring monitor or new paid service.

## 6. Grading and denominators

### Deterministic checks

Verify exact entities, predicate polarity, raw measurements/units, temporal scope, required qualification, complete source dependency, correct comparator set, valid clause references and absence of hidden/future data. Check approval/revision/hash, retraction, expiry and recap state separately. An output can be fluent and still fail.

### Human content review

Blind raters to arm and randomize presentation. Supply the same observation/evidence reference for each case. At least one reviewer understands football; a second independently grades all suspicious/severe cases and at least 25% of the remaining sample. Record disagreements and adjudication. A model judge may triage, but cannot be the sole authority for correctness, football usefulness or Spanish semantics. Calibrate any model grader against human examples on discovery data first.

Use a 1–5 rubric with anchors: **1** wrong/unusable or generic without useful facts; **3** accurate and understandable but routine; **5** concise, specific, supported and useful to the intended audience. Rate factual support, useful specificity, comprehension, audience distinction and editorial worth separately. Severe error flags override average scores. Do not reward more words, more tools or more agents.

| Measure | Denominator / reporting rule |
|---|---|
| Supported-claim precision | Correctly supported factual clauses / all factual clauses; report severe errors and case counts alongside it |
| Useful-story coverage | Eligible opportunities receiving a useful supported package / all eligible opportunities; fallback/abstention cannot improve precision by disappearing |
| Appropriate abstention | Correct no-story decisions / expected no-story opportunities; show missed useful opportunities separately |
| Reviewer contribution | Verified errors corrected/rejected, supported claims wrongly rejected, and unnecessary revisions; use labeled challenge cases |
| Tool use | Valid requests, correct input scopes, correct result use, errors and unnecessary repeats; a no-tool path can be correct |
| Mode reliability | AI-composed, factual fallback, explicit abstention, rejection, timeout, failure and stale completion counts / all starts |
| Usage | All provider input/output tokens, incomplete usage, retries and judge work; report unknown consumption explicitly |
| Acceptance without substantive edit | Human-reviewed packages accepted as useful/correct / all eligible opportunities, including failures; define cosmetic vs substantive edit before rating |
| Cost per accepted story | Total measured generation/repair/failure cost for a run / accepted stories; infrastructure allocation shown separately; if zero accepted, report undefined |

For S2 vs M2, show paired outcomes and differences grouped by parent, plus uncertainty rather than treating repetitions/variants as independent. A descriptive improvement of ≥10 percentage points in acceptance or ≥20% less substantive editing is an initial practical selection threshold, not statistical proof. Quality cannot worsen on severe errors. If the small sample leaves the difference uncertain, report that and choose based on simpler operation and measured latency/cost. Do not promise a score increase from crossing an arbitrary threshold.

## 7. Continuous-play validation

Use at least 20 distinct eligible opportunities across varied parents at continuous 1× replay; label the resulting percentiles as a small-sample engineering measurement. Run one active stream, then two. Add a separate model-stub load test for 10 viewers to isolate delivery cost; do not mix that with real model latency. Record cache/cold-start conditions.

Measure ingestion lag, queue wait, workflow duration, candidate readiness, human approval and browser display separately. Count eligible stories never scheduled, late completions and expired opportunities. Target one-stream evidence-durable→candidate P95 ≤10 s and at least 90% ready with ≥10 s remaining before expiry. Human approval time is an observed separate value, not subtracted to make the system look faster. Verify two-stream behavior even if it fails the single-stream target.

Replay cannot pause or seek during this measurement. Video rehearsal may use disclosed navigation, but cannot serve as evidence that continuous operation meets the target. Simulated load cannot establish real football accuracy or production scale. Report missed deadlines and recovery behavior alongside the successful median.

## 8. Formative user study

Recruit approximately 3–5 people with relevant football production/analysis experience and 5–8 casual viewers, if feasible. Label actual expertise; developers playing producer are engineering testers, not broadcaster validation. Obtain consent for recordings/quotes and store identifiable information outside the public repo. James owns recruitment; this plan sends no invitations.

Pilot the instructions once, then freeze the instrument. Avoid coaching or naming the intended interpretation. Use distinct matched scenes for baseline and candidate, counterbalance their order, and collect silent timed task observations before a retrospective discussion. Think-aloud observations are useful for discovery but must not be mixed with clean task-time claims.

### Producer tasks

1. Find a passage worth explaining and decide whether to show it.
2. Inspect the supporting evidence and identify what cannot be concluded.
3. Assess a clearly labeled challenge proposal containing an unsupported statement; correct or reject it.
4. Approve a supported revision while the replay continues.
5. Inspect an older approved moment, then retract that moment without losing another approval.

Record task completion, errors, requested help, observed approval timing, edits and whether the output was worth showing. Record perceived trust after evidence inspection, not only before it.

### Viewer tasks

1. Explain what happened and what changed in their own words.
2. Identify the passer/receiver and distinguish team retention from individual control.
3. Name one claim that the evidence does not establish.
4. Switch from simple to detail and find a specific measurement/source window.
5. Select a player and locate a relevant approved moment; recognize an empty involvement state.
6. Use the recap and notice that a retracted moment disappears.

Score comprehension against a prewritten answer key; accept equivalent plain language. Obtain Spanish review from a competent speaker when evaluating translated meaning. Do not ask “was the AI impressive?” as evidence of usefulness.

### Reporting

Publish anonymous participant counts, task descriptions, concrete observed successes/failures, individual paired timing examples and corrections made. Avoid generalized percentage productivity or commercial claims. An honest statement such as “four of five participants found the evidence control without help in this small study” is appropriately scoped. A participant quote requires consent and cannot substitute for measured behavior. Unavailable recruitment remains an explicit limitation.

Any critical mistaken belief about an unsupported outcome or accidental publication must be fixed and retested. Noncritical preferences inform prioritization. If users consistently find a shorter factual explanation more useful, ship that even if a more elaborate version showcases more AI.

## 9. Engineer deliverables

- `evals/agentic/manifest.json`: version/configuration/split/budget and all arm definitions.
- `evals/agentic/results.jsonl`: one outcome per case/arm/trial; no hidden skipped failures.
- `evals/agentic/REPORT.md`: factual correctness, usefulness, modes, resource use, timing, paired comparisons and limitations.
- `docs/user-study.md`: instrument, anonymized observations, observed problems, changes and unresolved questions.
- `docs/release-evidence.md`: exact commit/images, gates, representative traces, rollback and judging instructions.

These paths are proposed implementation deliverables, not files that already exist. Keep artifacts concise, reproducible and safe to publish; retain fuller protected transcripts separately where necessary.
