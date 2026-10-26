# Pressure Swing — hackathon flagship

## Why this next

The owner's rubric weights implementation, agentic innovation, impact, experience
and category fit equally (20% each). My recommendation is **Pressure Swing with
inspectable before/after observations**, then human validation. This is a product
judgment, not a predicted judging score.

| Candidate | Demo value and engineering tradeoff | Decision |
|---|---|---|
| Pressure Swing | A visible, measurable change; reuses the grounded Director/Reviewer and approval flow; easy to explain and inspect | Deliver a bounded nearby-opponent proxy |
| Pass Escape Difficulty | Needs a defined difficulty target and independently labeled calibration; proximity is insufficient | Defer the difficulty score |
| Chaos Index | A memorable name without a stable meaning or validated baseline risks a decorative number | Defer |
| Tactical turning points | Could be valuable, but present observations do not establish intent, line breaks, causal influence or a match-level turning point | Defer; retain factual scoped comparisons |

Implementation/UX benefit from a complete working path, explicit unknowns,
correction safety and a legible demo. Agentic innovation comes from constrained
selection/abstention, independent review and evidence refresh, not increasing the
number of roles. Impact still needs participant evidence. Category compliance
requires mapping the final submission to the actual chosen category; the rubric
alone does not establish eligibility. Reference:
[official hackathon rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md).

## Exactly what the measure means

**Average opponents within 6 m**, time weighted, around the passer for the two
seconds before release, versus around the receiver for the two seconds starting
at observed reception. Require all opponent identities and actor coordinates per
accepted interval, observed actor/team control, gaps no longer than 200 ms and
at least 95% covered time in each two-second window. Before mean must be at least
1, decrease at least 1, forward pass displacement at least 10 m. Existing pass
eligibility and three seconds of subsequent observed team possession also apply.
The window cannot cross the period start. These are provisional product gates;
they do not establish pressing intent, escape difficulty, probability or causation.

The new synthetic sequence has releases at 12, 37, 62 and 87 s. At **91.3 s**,
the last pass has its full retention evidence: **30 m forward**, nearby-opponent
averages **2.0 → 0.4**, coverage **100% / 100%**. It travels farther forward than
each of the preceding three completed team passes (18, 25, 22 m) within the
existing 120-second comparison population. No claim links it causally to the
later goal. All movement is authored synthetic source data, not match footage.

## Complete product path

- New v6 immutable pressure packages coexist with stored v1–v5. Old schemas,
  source exports and package hashes are retained. The new schema has explicit
  pressure windows, measurements and comparison scope.
- Backend source measurement → existing Director/Reviewer adapter or zero-call
  local renderer → protected producer review → approved timeline/overlay →
  bilingual variants, relevant passer/receiver/team focus, evidence and recap.
- “Why this moment?” explains supported relevance separately from “Check the
  evidence”. Before/pass/after cards expose counts, interval coverage and
  preceding-pass distances; casual/analyst presentations use the same facts.
- Source audit codes remain available in a disclosure with a plain explanation.
  A revision identifies the evidence version, not a confidence or quality score.
- Automatic flagship overlays hold for up to 8 seconds to reduce interruptions.
  Confirmed goals, producer manual selection, expiry and source withdrawal take
  precedence. Existing fixtures keep their selection policy.
- Guided pauses skip ordinary pressure candidates and stop at the comparative
  flagship. They remain producer-client convenience controls, never approval.
- Existing goals/corrections, shots/unknown outcomes, possession denominators,
  recoveries/control changes and ordinary pass stories remain supported.

## Run and present

From the repository: `make coverage-dev`, then open
[MatchSense locally](http://127.0.0.1:3000). The coverage-enabled homepage defaults to
**Pressure Swing flagship · guided mixed-event pitch**. The verification instance
runs separately at [port 3100](http://127.0.0.1:3100), using API port 8100.
No Azure credentials or model calls are required for deterministic local mode.

Suggested pitch (replay time is different from time spent explaining):

1. Start a fresh flagship session at 0. Say: “Fans see what happened; MatchSense
   makes a supported change understandable, with a producer in control.” Play.
2. At the pass/recovery/shot pauses, inspect one example and approve it. Show
   the saved attempt and make clear it is not a goal. Resume after each review.
3. At 60 s, inspect possession: interval, assigned-time denominator and coverage.
4. At about 91.3 s, select the 01:31 Pressure Swing candidate. Open **Check the
   evidence**: 2.0 before, 30 m forward, 0.4 after; all three comparison passes
   are visible. Approve; open the companion link. Switch Spanish, then receiver
   focus. Compare the casual and analyst views and show **Why this moment?**.
5. Resume to 104 s: source-confirmed score updates independently; goal wording
   appears publicly only after approval. End with **Catch me up**.
6. Optional correction demo: fixture ending `0006`, approve goal at 105 s, then
   run to 135 s. Cancellation removes the old approved goal and corrects score.

For a shorter staged pitch, use the explicit replay jump controls at 33, 47, 60,
92 and 105 s and say that you are skipping replay time. Do not describe seeking
or paused playback as real-time AI latency. Continuous 1× playback can be shown
by unchecking **Pause at new event types**.

## Model-specific status

The existing Azure deployment was checked as **gpt-4o-mini, 2024-07-18,
GlobalStandard**, API 2024-10-21. Five bounded real workflows (pressure, shot,
goal, recovery, possession) each used Director + Reviewer, produced valid exact
source-rendered bilingual packages, and reported complete usage. Ten calls,
5,026 input / 352 output tokens; verified retail estimate **$0.0009651**.
[Raw smoke evidence](../evals/match-coverage/pressure-flagship/model-final/report.json).
One execution per family establishes execution support, not broad model quality,
usefulness, calibrated reliability or superiority over fewer agents. Old hosted
builds were not updated. Running model mode in the API additionally requires
`WHY_NOW_MODEL_MODE=foundry`, `WHY_NOW_MATCH_MODEL=1` and existing Azure endpoint,
deployment and credential configuration. The default remains zero-call local.

## Pilot addendum — pending real participants

Keep the existing [mixed-event pilot](match-coverage-pilot.md); add a separately
labeled **flagship** task on fixture ending `0005` at 92 s. Do not replace its
older frozen scene or answer key silently. Ask viewers to explain what 2.0/0.4
means, identify the before/after windows, distinguish pass distance from later
retention, and state what the display cannot prove. Ask them to find evidence,
switch to a relevant player and recover the moment from the recap. Record task
completion, unassisted comprehension, confusion and preferred detail level.

Have a football reviewer independently verify proximity/count integration and the
comparison population, and a Spanish reviewer assess wording. Ask whether the
change is worth surfacing; engineering thresholds are not their answer key.
Recruitment, consent, ratings, findings and any significance claim remain pending.
Deployment/publication and category submission are separate owner decisions.

The retained preliminary smoke (`model-smoke/`) preceded a small source acquisition
scheduling correction. The final smoke (`model-final/`) was repeated against the
final exported fixture; all five final package metrics exactly match that source.
Across both smoke runs: **20 calls**, retail estimate **$0.0019224** in total.

A source packet, staged reviewer task, frozen source hash, bilingual candidate
and headers-only ratings sheet are prepared in
[the unassigned reviewer packet](reviewer-pack/pressure-flagship-preparation/README.md).
It contains no participant findings or completed ratings.
