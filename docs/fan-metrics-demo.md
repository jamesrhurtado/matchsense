# Synthetic Match Lab

Open `http://127.0.0.1:3000/insights` from the local MatchSense app, or choose
**Explore fan metrics** on the home page. The page is bilingual and reads its
deterministic example from `GET /api/insights/demo`.

## What the demo shows

- **xG:** twelve synthetic shots. A small, versioned logistic formula uses
  goal distance/angle, body part, nearby defenders, play type and goalkeeper
  position. It displays per-shot estimates and team totals. The formula is
  educational; it is not trained or calibrated on real match data and must not
  be presented as Opta/Premier League xG.
- **Pressure outcomes:** fourteen generated episodes. The detector uses a
  four-metre proximity rule over consecutive frames, then records the next
  five-second outcome. Two episodes have incomplete evidence; any rate uses
  only the twelve with known outcomes (five regains). These are observed
  sequences, not proof that pressure caused a turnover.
- **Tactical shape:** high-press and mid-block scenes each contain generated
  positions for 22 players. The page calculates pressure-start location, team
  length/width and line spacing from the shown frame. The tactic label is
  authored scene metadata, not a general tactical diagnosis.
- **Player contributions:** event counts for progressive passes, recoveries,
  shots and xG. Values remain grouped by player and role; there is no overall
  score or ranking.

All content is deterministic and fictional for demo/review. Real-football xG,
validated pressing rates and general tactical interpretation need separate
data/model work before product claims.

## Live viewer metrics

The viewer companion can also open **Match insights** for its current replay
session. `GET /api/replay-sessions/{session_id}/insights` calculates against the
observations delivered by that session's match clock. Corrections supersede the
older source records before totals are calculated.

- Player contributions count completed progressive passes of at least 5 m,
  explicit recovery events, and recorded shot outcomes. An incomplete pass,
  recovery, or shot is not inferred from player proximity.
- Pressure episodes require an opponent within 4 m for two consecutive
  tracking frames. The following 5 seconds determine whether the pressing team
  gained possession, the other team kept the ball and progressed at least 5 m,
  or kept it without that progression. Incomplete windows remain marked as such.
  These are observed sequences, not causal claims.
- Live xG is explicitly illustrative and unvalidated. It uses shot location,
  goal angle, tracked defenders within 4 m, body part and play type. The
  flagship fixture includes authored synthetic shot context for its first two
  located shots; older or incomplete events do not get guessed inputs. The
  formula has not been calibrated against real football. Shots without the
  required details or complete nearby tracking receive no estimate.
  Source-confirmed shot outcomes are shown separately.

Tactical-shape labels and the separate generated examples remain in the
Synthetic Match Lab; the live companion does not diagnose a high press or
mid-block from positions alone.
