# Metric definitions — pressure-escape-v1

These are transparent heuristics for a synthetic prototype, fixed before the recorded held-out evaluation. Coordinates are metres on a 105 × 68 m pitch, x right and y down. Attack direction is read from period metadata.

| Measure | Definition | Gate / units | Limitation |
|---|---|---|---|
| Pressure before release | Maximum count of opponents within a 6 m Euclidean radius of the passer in the trailing 2 s | At least one; at least 90% of nominal 10 Hz frames must include the passer and all opponents | Proximity only; closing speed and tactical coverage are not implemented |
| Opponents bypassed | Opponent x positions at release strictly between start x and observed reception x in the team's attacking direction | At least two; players | Longitudinal geometry; does not establish line-breaking, intent, or lane obstruction |
| Retained progression | All available frames across the next 3 s preserve the passing team's possession, with a received outcome; measure ball x progress after reception | At least 5 m forward; confirmation at the exact 3 s endpoint, with no sample gap over 200 ms | Missing/unknown possession or insufficient endpoint coverage causes abstention; no causal claim |

A candidate requires all three gates. It is first eligible after the confirmation observations and pass outcome are available. The overlay expires 30 s after the original confirmation timeline, even when observations are delivered late. At 60 s the synthetic segment stops. For the demo fixture, confirmation is 22,200 ms and expiry is 52,200 ms.

Every evidence object includes source message IDs, evidence content hash, metric definition version, source cutoff, windows, units, coverage and limitations. Source revisions replace old IDs only after their own availability time. Exact retransmissions are deduplicated. Raw operands remain inspectable; rendered positions are not added to the evidence stream.

No probability of importance, confidence percentage, player intent, causal tactical story, real-match accuracy or sustained match-control claim is derived. The MVP supports one bounded pass investigation per segment; multi-possession ranking and editorial cooldown across a complete match remain future work.
