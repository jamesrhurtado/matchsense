# Metric definitions — pressure-escape-v1

These are transparent heuristics for a synthetic prototype, fixed before the recorded held-out evaluation. Coordinates are metres on a 105 × 68 m pitch, x right and y down. Attack direction is read from period metadata.

| Measure | Definition | Gate / units | Limitation |
|---|---|---|---|
| Pressure before release | Maximum count of opponents within a 6 m Euclidean radius of the passer in the trailing 2 s | At least one; at least 90% of nominal 10 Hz frames must include the passer and all opponents | Proximity only; closing speed and tactical coverage are not implemented |
| Opponents bypassed | Opponent x positions at release strictly between start x and observed reception x in the team's attacking direction | At least two; players | Longitudinal geometry; does not establish line-breaking, intent, or lane obstruction |
| Retained progression | All available frames across the next 3 s preserve the passing team's possession, with a received outcome; measure ball x progress after reception | At least 5 m forward; confirmation at the exact 3 s endpoint, with no sample gap over 200 ms | Missing/unknown possession or insufficient endpoint coverage causes abstention; no causal claim |

A candidate requires all three gates. It is first eligible after the confirmation observations and pass outcome are available. The overlay expires 30 s after the original confirmation timeline, even when observations are delivered late. Each replay stops at its catalogue duration (60, 90 or 180 s for current fixtures). For original demo segment 1, confirmation is 22,200 ms and expiry is 52,200 ms.

Eligibility compares the original measured continuation distance with the 5 m gate. The displayed distance is rounded to one decimal place after measurement; a 4.96 m continuation must remain ineligible even though it displays as 5.0 m. The expanded synthetic suite caught and now guards this boundary.

Every evidence object includes source message IDs, evidence content hash, metric definition version, source cutoff, windows, units, coverage and limitations. Source revisions replace old IDs only after their own availability time. Exact retransmissions are deduplicated. Raw operands remain inspectable; rendered positions are not added to the evidence stream.

Player reception and team retention are separate claims. A recorded receiver may pass onward during the confirmation interval. Focused explanations therefore credit the player with receiving the pass and the team with retaining possession; they do not imply continuous individual control. Nearby-opponent counts establish proximity only, and longitudinal bypass establishes geometry only.

## Version 2 narrative facts

The detector's eligibility and thresholds remain `pressure-escape-v1`. New narratives add `forward-zone-v1`: signed x displacement of the successfully received pass, and its normalized reception third. Forward pass displacement is separate from post-reception team progression. Pitch thirds are `[0,L/3)`, `[L/3,2L/3)`, `[2L/3,L]` in attacking coordinates; on a 105 m pitch, exactly 35 m is middle and exactly 70 m is attacking. Leftward attacks are mirrored before classification. Invalid endpoints, missing outcomes and unsuccessful passes cannot support these facts.

Examples: a rightward pass from 35 m to 54 m moves 19 m forward and is received in the middle third; the mirrored pass from 70 m to 51 m has the same meaning. A 69.999 m reception is middle, while 70 m is attacking. Neither observation proves chance creation, pass difficulty, a tactical line break or a formal final-third entry. These definitions have engineering tests; external football review remains pending.

No probability of importance, confidence percentage, player intent, causal tactical story, real-match accuracy or sustained match-control claim is derived. The MVP investigates each delivered pass independently and retains separate story identities and approvals. The shared overlay uses the newest live approved moment; professional editorial ranking and cooldown across a complete match remain future work.

## Context contract v3 — 21 October 2026 iteration

`recent-completed-three-v1` is a bounded aggregate tool, separate from the 15 s raw-observation window. It compares signed forward pass displacement in metres, using the team's period attack direction. It does not compare post-reception carry, pass difficulty, chance creation or tactical value.

Population: this team's successful received passes in this period, resolved strictly before the current release, with resolution at or after `max(period start, replay start, release − 120000 ms)`. Select the latest three by descending resolution time, then ascending stable pass ID. Current pass excluded. Deduplication/corrections use the existing delivered-lineage resolver. Release/reception endpoints must be valid, paired and attributed to a verified receiving team/player. A comparator's release may precede the lower boundary; its resolution controls inclusion.

Fewer than three means `insufficient_history`. Unpaired relevant endpoints, invalid attribution/coordinates, or tracking gaps exceeding 200 ms across the retained window mean `incomplete_history`. Both forbid comparison. A source that silently omits both pass events cannot be detected from tracking alone: the supported incoming-feed contract requires event completeness. Wording remains explicitly limited to **this replay**. No claim of source-independent completeness or match-wide ranking is made.

Only `current raw forward displacement > each of all three selected raw values` permits `c-context`. Equality or mixed values omit comparison. The evidence table shows raw signed distances. At 30 m against [16, 12, 8], comparison is allowed; at 30 m against [36, 34, 32], or [30, 12, 8], it is not. Other-team, other-period, future and not-yet-delivered observations cannot enter the population.

The context record retains team/period, window, dependency availability cutoff, comparator IDs/times/measurements, endpoint IDs/hashes, eligibility population IDs/hashes, completeness, relation and limitation. Its semantic fingerprint excludes the availability timestamp itself: a correction that leaves tracking continuity unchanged must not revoke an unrelated explanation merely because it arrived later. Endpoint/population hashes, coverage status and all measurements remain bound. Package evidence identity combines the original current-play revision with this context fingerprint. Moving the clock alone does not create a new revision.

Corrections, late insertion, corrected exclusions and boundary/tie changes are recomputed against the relevant windows during materialization. Original approved packages remain immutable; invalidated projections lose approval and require review of a new exact revision. This first implementation uses bounded-window recomputation rather than a persistent reverse dependency index. The optimized index and its retention policy remain T02 work.

## Recap selection contract

`distinct-approved-v1` filters exact authorized approved revisions and verified focus **before** selection. Signature: ordered predicate, actor/team ID, comparison relation where present, and measurement bucket. Metres use `floor(value / 10)` (9.9 → 0; 10 → 1; −0.1 → −1); seconds/player counts remain exact and zones categorical. Exact actor IDs distinguish identical names.

Keep the earliest representative per equivalent signature and its complete member IDs/revisions/times, then retain the newest three distinct signatures in chronology. Similarity never creates a trend claim. Approved counts, distinct counts, selection reason and an input-revision projection hash remain inspectable. Retractions recompute the projection. Expired approved entries are archival and do not revive the live overlay. All approved history stays accessible.

## Editorial emphasis policy v4 — 22 October 2026

`distance-emphasis-v1` does not change eligibility or the exact latest-three comparison. It recommends a historical lead only when the current raw forward distance exceeds the largest comparator by at least 3 m and at least 20% of that comparator's absolute distance. If the comparator magnitude is below 1 m, only the absolute gap is applied. This is a provisional product rule for avoiding trivial headlines, not a validated football significance threshold. Football/producer review may justify a versioned change.

A raw 18.084 m pass versus a largest prior 18.0 m pass is a true comparison but defaults to current-play emphasis. A raw 18.084 m versus a largest prior 10 m pass meets both provisional conditions. Producers/agents can still select any supported historical contrast; if rounded values tie at one decimal, the sentence and chart disclose that the strict comparison uses original values. Full raw values remain in expandable source evidence.

New v4 titles explicitly name the previous three passes. A comparison sentence already states the current distance, so detail rendering omits the redundant forward-distance clause. Focused reception/location share one sentence bound to both facts; later possession remains a team claim. Stored v3 text is immutable and retains its original rendering.

## Match coverage v1 / publication v5 — 24 October 2026

[Match event definitions](match-events.md) govern the opt-in mixed replay. Shots
require observed resolution; only confirmed goal status changes score. Score
recomputes from initial state plus latest available unique goals. Unknown actors,
own goals and unlinked goals are supported without inferred assists or causes.

Possession integrates elapsed milliseconds over fixed trailing 60 s windows on
15 s boundaries. Assignment includes declared in-flight team possession; no gap
over 200 ms inherits state. Dead, loose and unknown time are explicit. Team-share
denominator is assigned time; coverage is assigned/(assigned+unknown). Percentages
require >=30 s assigned and >=95% coverage. Period/segment boundaries clip windows;
no extrapolation after the last frame. Evidence stores raw durations and sources,
not rounded percentages alone. Corrected sources create new exact revisions.

Recoveries need explicit observation for player/cause attribution. A team change
alone says team change. Restarts are separate, linked transition/recovery records
form one incident, and next-three-second retention is independently witnessed.

`mixed-approved-v2` recap reads exact approved revisions, deduplicates linked
shot/goal incidents and possession windows, prioritizes distinct goals then rounds
through remaining families to at most five entries. Chronological presentation,
complete timeline count and source-confirmed score header are separate. Legacy
pass-only recaps keep `distinct-approved-v1`.
