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

No probability of importance, confidence percentage, player intent, causal tactical story, real-match accuracy or sustained match-control claim is derived. The MVP investigates each delivered pass independently and retains separate story identities and approvals. The shared overlay uses the newest live approved moment; professional editorial ranking and cooldown across a complete match remain future work.
