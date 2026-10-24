# Iteration implementation record

## 23 October 2026 — broader match coverage selected for next-iteration planning

James requested an implementable plan after reporting first-time-user confusion about pass-only information. [MC01–MC10](match-coverage-implementation-plan.md) specifies goals/confirmed score, shots, possession windows, recovery/control-change stories and a mixed-event timeline/recap, with evidence, English/Spanish, approval, correction handling and real-user validation. These are **planned, not implemented or verified**. No model run, deployment or product code change was performed for this planning task.

This promotes basic event coverage previously staged in the original Obsidian notes and deferred/conditional in later repository plans. It supersedes those deferrals for the selected families; xG, tactical causation, set pieces, disciplinary events and real-feed integration are outside the required slice. Existing correctness and unresolved research/operational gates remain open. Estimates are 100–160 engineering hours plus a 20% integration allowance, subject to the schema/fixture checkpoint. Role assignments and pilot recruitment remain to be arranged. The owner's feedback is not recorded as a completed formal user study.

Active handoff pointers in the plan index, prior improvement plan and engineering backlog now link to this plan so the scope does not disappear in the next implementation pass. Track per-ticket delivery evidence here during implementation.

## 21 October 2026 — first implementation slice

Implementation began after the owner authorized applying the researched plan. The following statuses distinguish code delivered from evidence still required. The target remains the Grand Prize; no revised judging score is asserted.

| Ticket | Status | Evidence / remaining work |
|---|---|---|
| R01 | Engineering definitions established; external review pending | Actor/proximity/geometry vocabulary in metrics; boundary and mirrored tests. Football reviewer and neutral narrative/user pilot still needed. |
| F01 | Implemented | Receiver reception separated from team retention in both languages; onward-control and turnover cases tested. Existing approved packages remain immutable. |
| O01 | Core implemented | SQLite/Cosmos outcome lifecycle, restart interruption, ETag/idempotency, known usage preservation, API callbacks including abstention/rejection, protected diagnostics and release provenance. `evidence_observed_at` means server observation at scheduling, not a measured durable-ingestion timestamp. Browser display acknowledgments and complete end-to-end timing remain L01 work. |
| C01 | Implemented for scoped narrative grammar | Version 2 packages and clause bindings, code-controlled names/values/relations, full audience realization validation, version 1 compatibility and schema export. Contradiction, role/unit/name/window/qualification and source-correction checks pass. Free-form prose is outside the accepted grammar. |
| C02 | Implemented | Signed forward pass displacement and normalized reception zone; no detector threshold changed. Source windows, direction, reception boundaries and delayed correction tested. |
| A01 | Implemented; bounded live integration verified | Director chooses supported angle/claim selections; Claim Reviewer checks final content. Bounded evidence/repair/fallback and usage accounting. Same-model role contexts are not statistically independent. |
| E01 | Foundation implemented | T2/S2/M2 adapters, explicit budgets/reservations, blinded content packets and complete terminal rows. Four developer-visible challenge compositions share one generator backbone; fresh independent final parents remain pending. |
| A02 | Pending measured comparison | S2 has a meaningful same-role self-review/repair path under the same ceiling. No claim of M2 superiority until the paid/blind comparison is run and graded. |
| U01 | Implemented | Explanation/Show why discoverable at 1366×768 and 390×844; evidence stages, status/fallback labels; browser checks and screenshots. |
| P01 | Implemented | Verified role/team IDs filter approved history and recap; no-involvement state, Whole play return, source-only trails with missing-frame gaps; shared overlay unaffected. Human usefulness remains unmeasured. |
| C03 | Deferred conditional work | Genuine prior-pass comparison is not implemented; the old limited comparison tool must not be described as a new analytical capability. |
| N01 | Deferred conditional work | Current chronological approved recap remains; no claimed editorial ranking improvement. |
| L01 | Initial continuous-play measurement completed; broader gate pending | Two simultaneous 1× cloud replays produced AI candidates in two calls each, but one left only 8.753 s for review. Active-session transport scheduling and lock scope were improved, with six regression tests. The separate post-change run produced two-call AI candidates with 19.786 s and 17.490 s remaining; see QA for exact scope and retained earlier miss. This is not a measured P95 or live-readiness certification. |
| L02 | Not selected | No speculative factual-first revision/promotion path added before timing evidence. |
| E02 | Pending final study | Existing synthetic regression and new offline harness smoke are integration checks. Agent usefulness, broad semantic quality and final sealed assessment remain unestablished. |
| U02 | Instrument prepared; participants pending | `docs/user-study.md` includes tasks, answer keys, consent, counterbalancing and honest reporting. No observations invented. |
| Q01 | Local and bounded cloud integration passed | Backend, production build, existing synthetic regression and browser flows verified. Real model, publication, browser and replacement-replica results are recorded in QA. |
| S01 | Private source delivery completed; submission pending | Owner confirmed registration; the private `jamesrhurtado/why-now` repository is created and pushed with the MIT license. Reviewers/viewers are not yet arranged. Final video, public visibility for submission and submission completion remain pending. |

## Architecture decisions

1. Keep deterministic facts and exact-revision producer publication authoritative. Models select explanatory content; rendered clauses cannot introduce arbitrary new facts.
2. Implement Director → Claim Reviewer first. The single-agent comparator uses the same claim builder, renderer, tools, ceiling and a substantive self-check/repair path. Optional third composition role is deferred until comparative evidence supports it.
3. Keep the existing three/four-call legacy workflow readable and available through explicit `WHY_NOW_NARRATIVE_VERSION=1`; default application generation is version 2. Existing saved packages are not rewritten on deployment. A rollback must retain compatible readers for stored version 2 packages.
4. Use existing Cosmos/SQLite resources for workflow outcomes. No new Azure service is required. A terminal outcome is immutable; later editorial actions remain in the existing audit stream.
5. Distinguish numerical/structural validity, supported narrative meaning, user usefulness and operational speed. None substitutes for the others.

## Verification record

- Original regression: 168/168 cases, 594/594 authored checkpoints, 72/72 distinct expected moments; unchanged baseline inputs/outcomes; zero model calls. Generated timing-only report changes were discarded after verification.
- Full backend gate: 272 passed, including source-scope checks and six active-transport/concurrency regressions.
- Production web build and TypeScript passed.
- Local browser coverage: 14 distinct tests passed after updating stale wording expectations; two explicitly hosted tests excluded from the local run. The initial integration test failures were obsolete expectations for wording and the new focus-aware empty state; the corrected test verifies the visible measurement, proposed wording label and disappearance after retraction.
- Offline agent harness: four scheduled T2 outcomes, three packages and one appropriate pre-outcome abstention; zero model calls. This is not a model comparison.
- Actual model/cloud, browser and restart measurements are recorded in `docs/qa.md`; they are separate from mocked provider tests.

## Release handoff

API `cloud-v17` and web `cloud-v8` are healthy on the existing Azure resources. The runtime provenance is `c85f035`. Private source is pushed to `https://github.com/jamesrhurtado/why-now` under MIT. GitHub backend/web CI passed at `eb90aed`; the transport commit triggered its own CI run. Local full backend gate passed all 272 tests.

Next evidence sequence: create independent evaluation parents and freeze the split; run the bounded T2/S2/M2 discovery comparison and blinded ratings; complete the 20-opportunity timing study; recruit the football reviewer/viewers and run the prepared study; choose any conditional features from measured findings; record the final demo and complete submission packaging. Registration is confirmed. Public repository visibility requires the owner's later direction because the current explicit request is private.

## 21 October 2026 — contextual product iteration

This section supersedes the earlier implementation-status rows where behavior changed. The starting working tree was clean at `170e1c49ecedfb1bb8dce5604cd1d2c2c13e061d`. Both the Grand Prize plan and the supplied 76/100 assessment informed this work. Source remains local/private; no new infrastructure or paid model run was dispatched, and no new numerical score is assigned.

| Plan ticket | Actual delivery | Still open |
|---|---|---|
| A01 | Bounded recent-three aggregate, raw signed measurements, complete/insufficient/incomplete statuses, stable tie/cutoff/window rules, endpoint coordinates/hashes, conservative completeness checks | Football reviewer and definition/usefulness review; upstream complete-event assumption remains explicit |
| T02 | v3 schema/renderer, combined current/context revision, population hashes including exclusions, late-insertion/correction invalidation, immutable v1/v2 readers | Persistent reverse dependency index/retention; further operational bounds |
| A02 | Angle controls lead/title; comparison is evidence-gated; Reviewer receives independently recomputed context; labeled repair and missing-verdict tests; existing ceilings preserved | Live model behavior, broader relevance/false-rejection evidence; fuller explicit plan metadata |
| U01 | Distinct bilingual titles, actor disambiguation, real producer emphasis controls and exact new-revision approval | Independent Spanish/content review and study-based usefulness |
| U02 | Compact clause-linked pitch, reception region, movement arrow, retention interval, comparison table, factual replay labels, collapsed phone history and core audience localization | Broader accessibility audit and user evidence-connection study; full evidence-detail localization |
| U03 | Role-first passer/receiver emphasis, deterministic approved recap with buckets/signatures/revision binding, grouped member links, focus before selection and correction/retraction recomputation | Human usefulness evidence; discovery-driven rule tuning if necessary |
| U04 | Observable angle/fact/context/reviewer repair/fallback summary before expandable technical trace; failed/no-package outcomes retained | Participant review and broader outcome interaction evidence |
| T01 | Append-only delivery/opportunity records and first approved-render acknowledgment, immutable terminals/usage, stale/expiry/capacity tests | Exact durability/readiness stages, full expected-opportunity/crash/restart reconciliation and clock uncertainty work |
| T03 | Focused subscription/preferences/variant/ack hooks; separate evidence, controls, review and summary components; scoped formatting check; incoming-feed boundary documented | Lock profile, further backend decomposition, declared-unit adapter plus independent contract test |
| A03 | Matched T3/S3/M3 adapters use v3; provider/config/source provenance checks; 12-outcome zero-model smoke | Live budget/rates, context/reviewer ablations, blind independent human ratings and architecture decision |
| I01 | Eight authored history variants plus two physically/feed-validated playable paired five-moment replays; old 168-case inputs unchanged | Independent structural discovery parents, sealed 24-parent final set, realism/Spanish review |
| I02 | Working comparison/recap/focus/edit tasks and current validation status documented | Participant recruitment, pilot, frozen sessions and observed findings |
| I03 | Retained local two-stream continuous 1× template sample and explicit scope/limits | 20 varied opportunities, model/cloud cost/latency, failure recovery and operating-limit report |
| C01 | Context contrast, qualified insufficient history and contextual correction/isolation covered by backend/API tests; real producer/viewer comparison and five-history browser flow | All three acceptance scenarios through complete browser flows and independent release review |

Verification in this candidate: **301 backend tests passed**; production web build, TypeScript and scoped formatting passed; **15 local browser tests passed** at desktop/phone sizes, including the new actual five-moment contextual replay. Original regression: **168/168 cases and 594/594 checkpoints**, unchanged baseline, zero model calls. Offline agent smoke: **12 T3 outcomes, 11 packages, one appropriate abstention, zero failures and zero model calls**. Full JSON Schema resolves/validates a real v3 package. Synthetic discovery and injected repair tests are not human findings or spontaneous model-error measurements.

Try landing-page catalogue **Previous-pass history A/B**, jump to second 95, select Moment 4, inspect and approve. The current passage is identical at 30 m: A compares against [16,12,8]; B against [36,34,32]. Only A yields historical contrast. Five approved moments remain usable with collapsed mobile history. Generate these observation-only runtime fixtures with `python -m simulator.context_replays`; schedules/references remain outside runtime images.

Evidence: [metric contracts](../metrics.md), [runtime measurements](../runtime-performance.md), [validation status](../product-validation.md), [reassessment limits](../product-score-reassessment.md), [candidate evaluation manifest](../../evals/agentic/context-smoke/manifest.json). The 90+ gate remains open. No category score is raised automatically for ticket implementation.

### Ordered source handoff

The contextual update was organized into local commits `9afd879` (backend/context/publication accounting), `56ff86e` (paired replay/evaluation evidence), and `c2778b0` (audience/producer UI and browser checks). A source-fingerprint audit confirmed all 41 files recorded in the candidate evaluation manifest match the committed implementation. The [PM update handoff](pm-update-handoff.md) records this delivery and the still-open plan gates. These commits have not been pushed or deployed as part of this handoff.

## 22 October 2026 — version 0.5 quality iteration

Delivered v4 concise rendering, provisional significance-aware emphasis, explicit comparison titles, signed comparison visualization, coherent viewer/evidence labels, earlier-moment return navigation and atomic package/acceptance accounting with recovery. Existing approved v1/v2/v3 packages remain unchanged. A real discovery failure omitted a mandatory claim; both agent strategies now receive identical bounded validator-repair feedback.

Actual comparison: 60 outcomes, 15 correlated cases, 69 calls, complete usage; all broad angles matched, no reviewer repairs, one S3 factual fallback. Together with smoke and post-fix checks, estimated model usage is $0.0491799. No multi-agent advantage, human benefit or new score is asserted. See [quality handoff](quality-v4-handoff.md), [comparison evidence](../../evals/agentic/discovery-v4/README.md), and [reviewer guide](reviewer-guide-v4.md). James can arrange reviewers/testers; sessions remain pending.

## 24 October 2026 — MC01–MC10 local engineering delivery

This entry supersedes the planning-only status for the match-coverage iteration.
Baseline source: `2d515515f0dcaeac7ad48f62a63900bebaefc858`; kickoff backend gate
325 passed. The working tree already contained planning documents, friend pitch,
reviewer assignments and a review-preparation script; those were preserved.
Delivery remains reviewable local changes, with no new commit, push or deployment.

Engineering owner for this delivery: Codex. Product/recruitment owner: James.
External football/Spanish reviewers and pilot facilitator remain unassigned.
The primary MC plan governs scope; no required event family was deferred.

| Ticket | Status progression / supported mode | Evidence and remaining limitation |
|---|---|---|
| MC01 | Planned → implemented → engineering-checked | [Definitions/examples and rollback matrix](../match-events.md); interval-end, cutoff, public-state, unknown-actor and approval rules frozen. External football review pending. |
| MC02 | Planned → implemented → locally verified | Additive typed shot/goal/recovery/period payloads, strict v5 family evidence/claims/renderer/schema; original readers/hashes intact. SQLite and mocked Cosmos parity; live Cosmos unverified. |
| MC03 | Planned → implemented → locally verified | Two reproducible four-minute observation-only exports, separate catalogue (original 173 untouched), 21 hand references independent of production metrics, physical/feed checks. Engineering-authored synthetic discovery, not human football validation. |
| MC04 | Planned → implemented → locally verified | Pure public score/clock projection, source-confirmed goals, unknown/own/unlinked goals, shot outcomes; duplicates, late delivery, corrected team/scorer and cancellation checks. No inferred assists, saves or causation. |
| MC05 | Planned → implemented → locally verified | Time integration, explicit base/coverage/exclusions/minimums, source dependencies and period clipping; recovery/control/restart distinction, incident dedup, immediate-loss and 3 s witness checks. |
| MC06 | Planned → implemented → zero-call verified | Bilingual simple/detail/verified focus, bounded realization and denominator/role checks; Director/Reviewer adapter with fake-provider support/reject/abstain/failure tests. Deployment-specific new-family AI remains unverified and opt-in. |
| MC07 | Planned → implemented → local template verified | Shared storage/approval/audit, protected producer/public projections, corrections, exact retries, archive-only approval, producer overlay override, stale job rejection, queued-outcome persistence and actual API/SQLite restart. Paid scheduling/cloud operating limits remain unverified. |
| MC08 | Planned → implemented → browser verified | Prominent score/period, mixed queue/family filters, mobile/desktop evidence, approved possession interval, verified role/team focus, linked shot/goal incident details, timeline and max-five mixed recap. |
| MC09 | Planned → implemented → local gates verified | 371 backend tests (325 original + 46 new); 21 browser tests incl. 3 real mixed flows and one mocked linked-role check; 2 Azure tests intentionally skipped; type/format/build passed. Original 168/168 cases, 594/594 checkpoints unchanged; new references 21/21. Continuous 1× two-session results are recorded separately from model/cloud claims. |
| MC10 | Engineering preparation complete; human study pending | [Pilot packet](../match-coverage-pilot.md), setup, mixed demo, friend/presenter addenda, metrics/feed docs and [handoff](match-coverage-handoff.md). Recruitment, facilitator, reviewer ratings, user observations and retests pending. |

No ticket is marked deployed. Source-confirmed state is public without editorial
approval; explanatory variants, history and recap still require exact approval.
Turning off the creation flag does not reinterpret already-created mixed sessions.
Stored v1–v4 packages are never migrated in place; v5 rollback must retain a
compatible reader or isolate these sessions.

Verification: [actual command outputs and mode limits](../../evals/match-coverage/verification.json),
[independent references](../../evals/match-coverage/results.json),
[schema/reproducibility](../../evals/match-coverage/schema-and-reproducibility.json),
[continuous playback](../../evals/match-coverage/continuous-play.json),
[actual restart](../../evals/match-coverage/restart.json), and
[desktop/phone captures](../../evals/match-coverage/screenshots/).

The first continuous schedule missed eight observed control-change revisions in
its denominator; that incomplete run is retained separately. The complete
schedule accounts for 85 opportunities across two full 1× sessions and retains
per-family readiness, queue wait, review time, expiry/deferrals and usage, including
all attempted opportunities. Missing human review duration, per-opportunity browser
paint, durable ingestion timing and provider/model latency remain explicit. These
measurements support only the documented local template load, not production P95.

Observed integration failures were corrected: original catalogue count/isolation,
legacy async ordering, clock text markup, and a mistaken new opposing-team empty
state assertion. The restart harness initially used a producer projection for a
public-visibility assertion; the public check was corrected. Original numerical
reference expectations were not changed. Generated old report timing differences
were restored, with new results reported separately.

Pilot status: 0 participants, no ratings/findings. James owns 5–8 viewer and 1–2
football-aware reviewer recruitment; facilitator and independent Spanish/answer-key
review remain pending. Counterbalance baseline/candidate, retain consent and raw
counts, and fix/retest critical misconceptions before general release. Automated
correctness does not prove usefulness. No paid model call, new Azure resource,
external publication or hosted deployment was performed.


Final local gate: **371/371 backend checks**, including 46 new-family checks;
**21/21 local browser tests** (three real mixed backend flows plus one mocked
linked-role edge case), two paid Azure tests skipped. Default mixed-segment
selection is verified; the pass regression explicitly selects the original
fixture without changing its numerical or wording expectations. Approved linked
shooter/scorer roles and historical source-cutoff evidence are covered.
Timing: 85/85 opportunities found; **83/83 pre-end live opportunities** meet the
10 s review target, minimum 12.65 s. Two segment-end snapshots are retained with
nominal windows, not counted as live latency evidence. The final backend matches
the timing fingerprints; the homepage default was refined afterward and checked
through the browser suite. Public-usefulness gates remain pending real people.

## 2026-10-24 — Hackathon match-stage visual refresh

Implemented the requested football UI research and live-panel redesign. Research
and design rationale: [match-stage design](../match-stage-design.md). The original
broadcast treatment adds fictional club crests, prominent source score and clock,
textured pitch and shaded markers, observed team control, actual segment progress,
and an approved-explanation lower third. Selection policy is still inspectable
through a keyboard-operable disclosure. Missing scores display dashes. Producer
and viewer share the stage; evidence diagrams retain their existing presentation.
No claims, event locations, stored packages, approval rules or backend code changed.

Final gate: production build, typecheck, formatting and **23 local browser tests
passed**; two paid Azure tests skipped. All 21 existing local cases remain passing,
with two new desktop/mobile stage regressions for source correction without
approved narration, missing control, keyboard policy inspection and Spanish.
Screenshots and the initial/final run record are in
[UI verification](../../evals/match-coverage/ui-refresh/verification.md). The initial
clock markup failure was fixed; a concurrent preview rebuild invalidated later
pages, so the complete suite was repeated after restart. Final run: no failures.

Desktop, mobile (360/390 px), tablet (768 px) and Spanish presentation inspected.
This is a local engineering/design result. Human preference and usefulness remain
pending real participants; no new model call, external publication or deployment.

### Keeper/ball clarity follow-up

User inspection identified confusing ball/player overlap and keeper locations.
Confirmed that the mixed fixture inherits general off-ball grid positioning,
without keeper-specific movement. Added explicit-metadata keeper kits (distinct
colors and square shapes), EN/ES keeper legend, and a white linked ball symbol
that exposes the overlapping player while anchoring the observed ball position.
No player relocation, fixture rewrite, role inference from shirt numbers, source
observation change or stored-package/hash change. Existing awkward keeper
locations remain an acknowledged simulation limitation; realism needs a separate
fixture version. See the match-stage design record and UI verification follow-up.

Keeper/ball final gate: **24 local browser checks passed**, two paid Azure checks
skipped; build/typecheck/format passed. Added a regression for explicit keeper
roles and exact ball/source anchoring; desktop/mobile screenshots inspected.

## 2026-10-24 — Moving fixture and first-run workflow correction

Owner rehearsal feedback showed the pitch barely changing despite a progressing
clock, confusing position-sample counts with incidents, and evidence opening
outside the current viewport. This feedback is recorded as owner input, not a
completed recruited pilot. Root causes: off-ball drift of about 0.25 m in the old
fixture, a raw observation counter, and missing evidence navigation.

Added separately versioned moving discovery/correction fixtures (`...0003/0004`)
with continuous authored player/ball paths and keeper lanes. The old mixed
fixtures and original 173 catalogue/reference cases are unchanged, as are stored
package bytes/hashes. Physical/feed checks pass and all four pass opportunities
remain eligible. New fixture goal/shot paths match their authored event locations;
unknown shooter/location and missing ball observations remain unknown.

The homepage defaults to the new guided fixture under the coverage flag. A
producer-only client option pauses at the first example of each event family
(possession from the 60 s summary), without auto-approving or publishing.
Playback controls precede the pitch; a review action navigates to the queue;
Show why scrolls to/focuses supporting evidence and clarifies that it does not
infer tactical causation. Raw observation counts move into an explanatory
disclosure. Guided pauses can be disabled for continuous playback.

Verification: **381 full backend checks**, **25 local browser checks**, build,
typecheck and formatting passed; two paid Azure checks skipped. Final fixture
subset: **7 passed**, including additive catalogue regeneration. Original
**168 cases / 594 checkpoints** match the saved baseline. New-family independent
references remain **21/21**. Source/physical, new moving-demo, old baseline and
browser results are kept separately. See [moving demo](../moving-demo.md) and
[verification](../../evals/match-coverage/moving-demo/verification.md).

This remains an authored synthetic segment, not a full football simulation.
No human ratings, football-review findings, paid calls, external publication or
deployment are claimed. Guided pauses rely on the open producer client; multiple
controllers can still affect playback. Human usefulness/realism validation remains
pending participants.

Moving-demo continuity gate: both versioned four-minute segments completed at
real 1× speed with no seeks/errors, all required families observed, and correct
confirmation/cancellation state (242.54/241.56 s elapsed). Results are separate
from the older timing benchmarks; no latency or user-usefulness claim added.

### Controlled-ball badge readability

Owner screenshot showed that the prior leader line and source-position dot could
still obscure #11. Changed the live controlled-ball presentation to a small badge
beside the explicitly observed carrier, with no line/dot over the number. Badge
placement prefers a stable clear corner, gives keeper squares extra clearance and
retains the source coordinates separately. Free-ball anchors paint behind player
markers; free/in-flight rendering still follows observed coordinates. No carrier
is inferred from proximity, and no source or stored package is changed.
Desktop/mobile screenshots and browser checks are recorded under
`evals/match-coverage/ball-badge/`. No model call or deployment.

Ball badge final gate: **27 browser checks passed**, two paid Azure checks skipped;
production build, typecheck and formatting passed. Crowded desktop/mobile cases
verify the badge does not cover two-digit numbers, transitions to the observed
free-ball coordinate and disappears when ball observations are missing.

## 24 October 2026 — pressure flagship iteration (owner authorized)

Selected **Pressure Swing**, defined as a nearby-opponent proxy, as the most
worthwhile next pitch addition under the equal-weight rubric. The recommendation
is judgment, not a predicted score. Chaos/difficulty indices and tactical turning
points remain deferred until their target meanings and evidence can be validated.
See [rationale and demo](../pressure-flagship.md),
[frozen implementation contract](flagship-implementation.md) and
[separate verification](../../evals/match-coverage/pressure-flagship/verification.md).

| Work | Engineering status | Evidence / limitation |
|---|---|---|
| Nearby-opponent measurement | Implemented | Time-weighted 6 m counts; declared 2 s windows; ≥95% coverage, observed control, bounded gaps; no tactical cause |
| New v6 family pipeline | Implemented | Source → review → exact approval → EN/ES, role focus, evidence, timeline/recap; SQLite and Cosmos adapter checks |
| Integrated presentation fixture | Implemented | Additive IDs 0005/0006; four passes within comparison population, 2.0→0.4 and 30 m flagship; all old families retained; old exports unchanged |
| Clear relevance/evidence and audience views | Implemented | Separate why/evidence, before/action/after, scoped comparison table, casual/analyst and verified passer/receiver focus |
| Noise policy | Implemented | Flagship automatic 8 s hold; source withdrawal/expiry, goals and producer override respected; no automatic approval |
| Current-model execution | Verified bounded smoke | Existing gpt-4o-mini 2024-07-18; five real families, ten calls; model-specific execution only, not broad quality or superiority |
| Pilot/release materials | Prepared | Separate flagship task/key; recruitment, external football/Spanish ratings and findings pending |
| External deployment/publication | Pending owner decision | Existing hosted build not updated |

No extra agent roles or Azure resources added. The event model flag now initializes
after its Foundry dependency (startup bug fixed). Continuous checks exposed an
unknown-outcome status error; a focused regression covers it. Browser checks
exposed the original mobile pass evidence moving below the established viewport;
new relevance cards are scoped to flagship sessions so the original assertion is
retained. The new recap test's hidden-option selector was corrected to a heading.
Failed first-run logs remain in the verification folder.

Final backend: **410 passed** (including 28 pressure-specific checks). Original
**168 cases / 594 checkpoints** and mixed **21/21** remain separate and unchanged.
Final continuous discovery/correction fixtures each reach 240 s at real 1× with
zero seeks/errors and all six candidate families (242.57/243.83 s elapsed).
Existing browser regression: **27 passed**, two hosted Azure cases skipped;
new flagship browser verification is recorded separately after correcting test
locators for the hidden option, heading level and translated language label.
Production build, typecheck, formatting and whitespace checks pass. Latest real
model smoke matches the final source exactly; both bounded smokes together used
20 calls, estimated retail cost **$0.0019224**. No deployment or participant
findings were added. The unassigned reviewer packet includes a frozen source
cutoff, staged review task and headers-only rating sheet.

Final flagship browser rerun: **1 passed**; combined final build coverage is
**28 local browser scenarios passed**, **2 hosted-only skipped**. New-family
screenshots and raw logs are retained separately in the flagship verification
folder. Fresh local session at 0 s is paused and ready for the owner to start.
