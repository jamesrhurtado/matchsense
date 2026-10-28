# MatchSense — hackathon demo script

**Core idea:** a viewer question is tied to the right match moment; MatchSense
checks an explanation against match evidence; the producer chooses what reaches
the broadcast and companion.

## English video script — target 1:54

Start from one guided AI session and one synthetic match. The YouTube test player
should already show the OBS composition. Use Audience Agent rehearsal questions
unless authorized YouTube Live chat is connected; keep the **Rehearsal** label
visible for simulated questions. The match moment and all views must come from
the same session. Do the setup and confirm the AI trace before recording.

| Time | Show | Say |
|---|---|---|
| 0:00–0:13 | Open on the YouTube player with the synthetic match from OBS. | “Football gives us the numbers. But what changed in that pass? MatchSense makes the match make sense, turning match events into a story a producer can verify and fans can explore.” |
| 0:13–0:28 | Cut to the producer console. Show the Audience Agent group and its **Rehearsal** badge. Select **01:31 · Nearby pressure change**, then click **Confirm moment and review**. | “The Audience Agent groups similar viewer questions. I confirm they refer to the 01:31 pass, connecting the question to the right moment.” |
| 0:28–0:46 | Show the evidence for that pass: 30 m forward, **2.0 → 0.4** nearby opponents, six-metre radius, two-second windows, and coverage. | “This synthetic pass moves the ball 30 metres forward. The average number of opponents within six metres changes from 2.0 around the passer to 0.4 around the receiver. Both two-second windows are fully covered.” |
| 0:46–1:04 | Show the explanation’s review status and its evidence/source windows. | “MatchSense checks the explanation against the match evidence. I can inspect the source windows before making the final decision.” |
| 1:04–1:16 | Approve the exact reviewed revision for viewers. | “I approve this exact revision for viewers. The producer makes the final call on what goes on air.” |
| 1:16–1:29 | Cut from the OBS composition to the actual YouTube player showing the question and approved insight over the match. | “The confirmed question and approved explanation now appear together over the match in OBS and on YouTube.” |
| 1:29–1:47 | Open the same session’s companion. Show the simple explanation, then its measurements/evidence; briefly show **Catch me up**, language, or player focus. | “The companion gives casual fans a clear explanation, lets analysts inspect the measurements, and helps returning viewers catch up or follow a player.” |
| 1:47–1:54 | Finish with the stream and companion side by side, then the MatchSense name. | “One question, one checked story, one producer decision. MatchSense makes the match make sense.” |

## Recording checks

- Rehearse the **Pressure Swing flagship** at 91.3 s. Confirm the pass reads 30 m
  forward, the nearby-opponent average reads 2.0 → 0.4, and both windows show
  100% coverage. Keep **SYNTHETIC MATCH DEMO** visible.
- In a fresh AI guided session, confirm the Audience Agent group, Story Director
  proposal, Claim Reviewer verdict, and producer approval are visible for the
  moment. Do not claim the agents outperform a single agent; the bounded
  comparison found no such advantage and has no human ratings.
- Confirm the replay pauses on the intended reviewable moment and that earlier
  insights do not interrupt the take. This behavior still needs a recording
  rehearsal; do not assume it is fixed.
- Confirm the exact approved revision is selected for the overlay, then verify
  that the OBS composition reaches the YouTube player and that the same approved
  moment appears in the companion. OBS status alone does not confirm delivery.
- If using simulated questions, label them as rehearsal data. If using YouTube
  Live chat, reconnect and verify that messages are actually being read before
  recording. Never imply rehearsal prompts came from real viewers.
- Use a small technology caption only for services confirmed in that recorded
  run, such as Microsoft Agent Framework and Azure OpenAI.

## Why this sequence

The Audience Agent groups questions; the producer links the group to a specific
candidate. MatchSense creates and checks the story from the match event and
evidence. The Audience Agent does not write a chat reply or automatically choose
the story. The producer approves the exact version before it reaches the stream
and the viewer companion.

This puts the complete path on screen without pausing for a separate architecture
walkthrough. It also demonstrates three viewing needs through product behavior:
plain-language context, optional evidence and measurements, and personalized
catch-up/player focus. These are product capabilities, not claims of a completed
participant study. The synthetic pass and its evidence carry the technical story;
keep the separate shot/xG panel out of this recording so the demo stays centered
on one moment.

For this demo, show the Audience Agent doing useful work but do not pitch an
agent count or claim that multiple agents outperform a single agent. The current
bounded evaluation does not establish that superiority. See [QA](qa.md) and the
[multi-agent evaluation](next-iteration/multi-agent-evidence.md).

Setup references: [OBS/YouTube](youtube-pitch-demo.md) ·
[Audience Agent](next-iteration/audience-agent.md) ·
[OBS status](obs-monitoring.md).
