# Quieter live editorial experience — verification

25 October 2026. Local engineering, not human validation or a new model-quality
study. Existing Azure deployment remains separate. Changes extend the existing
feed, packages, approval, evidence, audience variants and recap infrastructure.

## Delivered behavior

- Live viewer starts with the match. Approved explanations, preferences and
  evidence open on request; catch-up stays available. Hidden explanation panels
  do not fetch evidence/variants or record a viewer paint acknowledgment.
- Producer initially sees three suggestions plus the selected one; Show all,
  family filtering and archive retain all supported families. Evidence and
  preview inspection pin the selected story while the shared clock continues.
- Audience preview reads exact existing variants, on demand, in English/Spanish,
  with casual/analyst columns or a single mobile pane. It does not approve or
  generate content. A response for another revision cannot display.
- Catch-up supports an inclusive event-occurrence interval and includes a
  possession window by its end time. Default API behavior stays compatible.
  Current validity and score are evaluated now, so a later source correction
  removes a claim even from a recap of an earlier interval.
- Source withdrawal notices persist in the existing lifecycle store; manual
  retractions are projected from existing editorial audit. Both require previously
  approved content. Public notices expose identity, family, time and a fixed
  explanation, never withdrawn prose, model reasons or private traces.
- An open recap refreshes on relevant approval/source/score changes and keeps
  stale members out using exact currently approved identities. No “nothing
  happened” inference is made from missing approvals.
- Private browser-local visit boundaries are not sent in share URLs. Storage
  disabled/unknown/future values fall back to the current join time. Hidden-tab
  clock updates are not treated as watching the match.

## Checks and retained evidence

Baseline before changes: **429 backend tests passed**. The full updated run:
**440 passed** in `backend.txt`. A final targeted run after copy and persistence
checks: **20 passed**. The new interval/withdrawal cases run on SQLite and the
Cosmos test adapter, including reopening each adapter, exact package/hash retention,
unknown/unapproved events, source cancellation, manual retraction, focus, interval
boundaries and a correction arriving after the requested interval. Adapter tests
do not certify a live Cosmos deployment.

Original regression: **168 cases / 594 checkpoints**, baseline unchanged. Output
is in `original-regression.txt` and the report; tracked baseline artifacts were
restored after timing-only regeneration. Independent mixed-family references:
**21/21**, plus the existing two physical/feed checks, zero model calls.

Production Next.js build/TypeScript and component/hook formatting passed. Browser
checks cover the new template live flow, private bilingual/mobile preview,
wrong-revision refusal, interval/visit catch-up, corrected score and withdrawn text,
as well as original evidence, focus, approvals and compatibility flows.

Final broad browser run: **32 passed, 2 failed, 3 skipped**. Both failures were
obsolete UI expectations: the recap used to close after retraction, and its close
button now has a Spanish label in Spanish mode. The affected tests were updated
to verify the new behavior and both passed separately (`browser-flow-recheck.txt`,
`browser-pressure-recheck.txt`). This is **34 distinct local cases passed across
runs**, not one clean 34-case run. The two hosted checks and opt-in paid-model check
were not run.

The separate **four-minute continuous phone run passed**: 243.94 seconds including
startup/final inspection, continuous 1× with no pause, seek or automatic approval.
The viewer remained match-first, observed the confirmed goal and later cancellation,
ended at 04:00 without a new session, and opened an empty approved recap with the
correct final score. This adds one distinct case (**35 local browser cases total
across runs**). See `continuous-result.json`, `browser-continuous.txt` and
`screenshots/continuous-end-mobile.png`. This was a template/UI continuity run;
it does not rerun the real-model timing gate or measure usefulness.

Initial browser checks exposed test-attribute forwarding, stale mocked revision
responses, a route-interception cleanup error and obsolete close-on-retraction
expectations. Those were fixed. The focused-retraction regression also exposed
the need to validate recap members against current approvals; the client now
rejects old members even if a delayed response returns them. No original
fact/approval/withdrawal expectation was relaxed. The intentional behavior change
is keeping the recap open with current information instead of closing it.

## Timing reanalysis, not a new trial

`scripts/analyze_editorial_timing.py` reads the retained scheduling-v2 dual-stream
runs; `prior-timing-analysis.json` is its output. Both retain their original
**21/25 timely opportunities (84%)**, with one missed opportunity in scene 7.
The proposed 95% / 15-second gate remains failed. No expiry or reference changed.

The three possession candidates per scene had median worker-queue intervals of
about 0.6 ms, median workflow intervals of 3.73/3.31 s and median review time
remaining of 8.95/8.58 s. Their existing eligibility lasts 15 s, so any model time
necessarily prevents a full 15 s of remaining review time. This diagnoses an
incompatible gate/window as well as processing delay; it does not justify changing
the target after observing results. Other families also retain late cases.

Replay-to-replay and wall-to-wall measurements are separate. Durable receipt to
evidence readiness, complete source-to-browser latency and human review duration
remain unknown. These are related authored scenes, not independent matches or
proof of agent superiority. Queue truncation is visual only; no reduction in
model cost, missed moments or distraction is claimed.

## Remaining limits

No new paid model evaluation: this verification uses explicit template execution;
the existing real-AI configuration remains available at the local entrance. Model
roles, prompts and thresholds were not changed. Recorded actions are not a claim
of semantic correctness or independent agents.

Football/Spanish relevance, paired baseline keys and actual participant results
remain pending. The research opening is an attributed multi-sport attitude result,
not proof of WHY/NOW's impact. Prior invalidations have no fabricated notice times.
Visit state is per browser, not cross-device read history; catch-up is occurrence
based, not a stream of everything delivered since arrival. Existing single-host
and production integration limits still apply. No deployment, push, visibility
change or video publication was performed.
