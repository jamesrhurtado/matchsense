> Latest pitch: [Pressure Swing flagship walkthrough](pressure-flagship.md#run-and-present). This document retains the original mixed-event scene; its timing/key differs from the new additive flagship.

# Mixed-event local walkthrough

This is a four-minute synthetic segment in zero-call deterministic template mode.
The hosted build has not been changed. No real-feed, xG, assist or tactical cause
is inferred. Preparation is navigation, not a latency demonstration.

Start from the repository root:

```sh
make coverage-dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). If an older instance occupies
3000/8000, stop its own terminal first. Dependencies: README local setup. The flag
is explicit and storage is isolated in `.run/match-coverage.db`. Local producer
key is prefilled; viewers use the companion link with no key. The default is **Guided matchday demo · moving play and mixed events**. Open the
producer console. This version has continuous scripted movement and keeper lanes;
it is still a synthetic presentation segment, not a full football simulation.
The older mixed discovery/correction replays remain available unchanged.

For a first rehearsal, leave **Pause at new event types** enabled and press
**Play** at 1×. The first guided pause is the pass at about 16.2 s. Click
**Review paused moment** if the queue is below the pitch, then **Show why**.
The evidence scrolls into view. Inspect it, approve or skip, and press **Play**
again. Further first-family pauses occur at the recovery (~30 s), shot (~46 s),
possession summary (60 s) and confirmed goal (104 s). Some recovery facts receive
an additional sustained-control revision after three seconds; inspect the current
revision before approval. Turning the checkbox off gives continuous playback.

**Show why** means “show the recorded facts supporting this wording”; it does not
claim a tactical cause. **Replay data details** explains that delivered observations
are tracking samples and source records, not hundreds of football incidents.

The following jump-based walkthrough remains useful for rehearsing individual
families; jumps are explicit navigation rather than live latency evidence.

1. Jump to **25 s**, inspect and approve the pass. Existing pass evidence still
   works. Candidate is ready at 16.2 s in this fixture; original segment 01 keeps
   its original 22.2 s readiness.
2. Jump to **33 s**, filter **Control changes**, select loose-1, inspect its
   explicit recovery and next-three-second evidence, then approve.
3. Jump to **47 s**, filter **Shots**, select attempt-1. The observed outcome is
   saved; location is a point, not an invented ball trajectory. Approve.
4. Jump to **60 s**, filter **Possession** and select the 60-second snapshot.
   Inspect assigned denominator, coverage, dead/loose/unknown durations. Approve.
   This interval will stay fixed when replay time advances.
5. Jump to **105 s**. Confirmed score becomes **1–0** even before story approval.
   Filter **Goals**, inspect goal-1 and approve. No pass-caused-goal or assist claim.
6. Open **Viewer companion**, switch to Spanish and shooter/scorer focus. Try
   each team and an uninvolved player. Open approved history and select the saved
   shot, recovery and possession interval; inspect sources on phone/desktop.
   **Catch me up** combines exact approved revisions. Navigation changes only
   this viewer; **Select shared overlay** is a protected producer override.
7. At **150 s**, unapproved old candidates are archived. Select **Include archived
   candidates** in the studio to review them. **Approve for history only** never
   revives a live overlay. Linked shot/goal cards occupy one viewer incident,
   while their separate identities and source details remain in the producer.
8. Continue to **186 s** for the off-target attempt with unknown shooter/location;
   later passes keep working through the end of the segment. There is no final
   whistle/full-match-result claim.

For correction, create **Guided matchday demo · score correction** (or the unchanged original **Mixed-event correction replay**). Approve goal-1 and
attempt-2 at 105 s. Advance to **136 s**: source cancellation makes score **0–0**,
revokes affected approval and removes the old recap entry. Inspect/reapprove the
cancelled-shot replacement. The unrelated saved shot stays approved. Old package
bytes/hashes remain stored. Reset creates a new session; backward seeking is not
supported.

Suggested spoken pitch: “MatchSense helps you follow a varied football segment.
The score comes from confirmed observations. A producer approves explanations of
shots, control changes, possession and passes. Viewers can inspect the evidence,
change language and catch up on approved incidents. This local demonstration
uses synthetic data and templates; real-user usefulness is still being tested.”
