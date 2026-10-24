# Source observations for assignment F01

Evidence set S01. Synthetic football passage; first-period coordinates in metres on a 105 by 68 m pitch. Harbor City attacks toward increasing x. The time shown is seconds from the start of this constructed replay. All supplied observations were available by 18.200 s. There is no real-match video for this scene.

This is a factual reading aid derived from the raw observation records, not a preferred explanation or a football usefulness score. Review the underlying records if you dispute the summary. Report uncertainty or inconsistencies. The same evidence applies to all four anonymous outputs.

## Events and positions

| Source ID | Time s | Observation |
|---|---|---|
| m-0000142 | 14.000 | Eren Prado (blue-08, Harbor City) releases pass-1 from (37, 26) m. |
| m-0000155 | 15.200 | Pass-1 is recorded as received by Feli Costa (blue-09, Harbor City) at (58, 29) m. |
| m-0000186 | 18.200 | Ball at (65.0, 29.0) m. Possession team: Harbor City. |

## Tracking through reception and afterward

The source contains 31 tracking frames from 15.200 to 18.200 s, at 0.100 s intervals. The following samples show the control transition. The complete frames are in source-observations.json; a controller is a player identity and possession team is a separate field.

| Source ID | Time s | Ball x m | Ball y m | Controlling player | Possession team |
|---|---|---|---|---|---|
| m-0000154 | 15.200 | 58.0 | 29.0 | Feli Costa (blue-09) | Harbor City |
| m-0000164 | 16.000 | 59.8667 | 29.0 | Feli Costa (blue-09) | Harbor City |
| m-0000167 | 16.300 | 60.5667 | 29.0 | Feli Costa (blue-09) | Harbor City |
| m-0000168 | 16.400 | 60.8 | 29.0 | Ilan Luna (blue-01) | Harbor City |
| m-0000174 | 17.000 | 62.2 | 29.0 | Ilan Luna (blue-01) | Harbor City |
| m-0000186 | 18.200 | 65.0 | 29.0 | Ilan Luna (blue-01) | Harbor City |

Across those 31 frames, the recorded possession-team values are: Harbor City. Check the player-control column separately when assessing player-specific wording.

## Opponents at the release frame

Frame m-0000141 at 14.000 s contains all 22 players. Below are the 11 opponent x positions. Compare them with the release and reception x coordinates above. These coordinates describe longitudinal placement, not defensive formations or intention.

| Player ID | Name | x m | y m |
|---|---|---|---|
| amber-01 | Jori Marin | 90.1405 | 23.7716 |
| amber-02 | Kian Luna | 77.7754 | 30.7611 |
| amber-03 | Ari Costa | 81.9863 | 38.1477 |
| amber-04 | Beni Neri | 85.8329 | 44.7518 |
| amber-05 | Ciro Rocha | 90.0402 | 51.7524 |
| amber-06 | Dani Prado | 38.7505 | 24.8917 |
| amber-07 | Eren Vidal | 40.2495 | 28.7511 |
| amber-08 | Feli Vela | 42.0853 | 30.9004 |
| amber-09 | Gabi Paz | 90.0 | 22.0 |
| amber-10 | Hugo Sierra | 77.8589 | 28.7506 |
| amber-11 | Ilan Roca | 81.9807 | 35.7629 |

## Opponent proximity before release

The following counts are calculated from each frame using straight-line distance from the passer, with a radius of 6 m. They describe proximity, not a calibrated probability or an assessment of intention. No frames in this window omit roster players.

| Source ID | Time s | Opponents within 6 m |
|---|---|---|
| m-0000121 | 12.000 | 2 |
| m-0000122 | 12.100 | 2 |
| m-0000123 | 12.200 | 2 |
| m-0000124 | 12.300 | 2 |
| m-0000125 | 12.400 | 2 |
| m-0000126 | 12.500 | 2 |
| m-0000127 | 12.600 | 2 |
| m-0000128 | 12.700 | 2 |
| m-0000129 | 12.800 | 2 |
| m-0000130 | 12.900 | 2 |
| m-0000131 | 13.000 | 2 |
| m-0000132 | 13.100 | 2 |
| m-0000133 | 13.200 | 2 |
| m-0000134 | 13.300 | 2 |
| m-0000135 | 13.400 | 2 |
| m-0000136 | 13.500 | 2 |
| m-0000137 | 13.600 | 2 |
| m-0000138 | 13.700 | 2 |
| m-0000139 | 13.800 | 2 |
| m-0000140 | 13.900 | 2 |
| m-0000141 | 14.000 | 2 |

## Measurement definitions and scope

- Forward displacement is reception x minus release x for this attack direction. It is not the curved trajectory length of the ball.
- Post-reception forward displacement is ball x at 18.200 s minus reception x at 15.200 s.
- The pitch thirds are equal longitudinal bands: 0 to 35 m, 35 to 70 m, and 70 to 105 m. Describe boundary uncertainty if relevant.
- The current evidence window ends at 18.200 s. No shot, goal, later outcome, player intent, or match-wide conclusion is supplied.
- Synthetic positions are observations in a constructed case, not an expert-certified reconstruction of real football.

[Complete observation input](source-observations.json) includes metadata, roster identities, event records, all delivered tracking frames and the exact cutoff. It contains no output-generation method labels or reviewer answer key.
