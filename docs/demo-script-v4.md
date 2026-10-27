# MatchSense — hackathon demo script

**Core idea:** a fan’s question finds the right match moment; the producer
checks the evidence; the approved story reaches the stream and each fan’s view.

## Video script — 1:50

Before recording, start the YouTube test broadcast from OBS and let the
synthetic match begin playing. The video opens after delivery is confirmed,
with the audience question already in chat. This keeps the 1:50 cut focused on
the product experience; MatchSense does not start the broadcast automatically.
Use the English narration for the submission video.

| Time | Show | Say |
|---|---|---|
| 0:00–0:10 | The YouTube test broadcast is already live in OBS. Show the synthetic match playing and the prepared live-chat question: “What changed after that pass?” | “The play is over; the question remains: what changed? MatchSense groups live chat and helps the producer find the play—with evidence they can check.” |
| 0:10–0:22 | Audience Agent groups similar questions; producer confirms the suggested moment. | “I confirm which moment they mean, because live video and chat can be out of sync.” |
| 0:22–0:37 | Open the story evidence: 30 m forward; nearby-opponent average 2.0 before, 0.4 after; reveal source windows. | “This pass moved 30 metres forward. The nearby-opponent average changed from 2.0 before to 0.4 after. I can inspect the observations behind both numbers.” |
| 0:37–0:52 | Show Story Director → Claim Reviewer handoff. Add a brief, clearly labeled **Review recovery test** insert from the saved evaluation. | “The Story Director shapes a story from match evidence. The Claim Reviewer checks its claims. When one review was incomplete, MatchSense blocked it and used safe fallback wording.” |
| 0:52–1:05 | Producer approves the exact revision; Broadcast Producer recommends `show`, `hold`, or `wait`. | “I approve the exact story. The Broadcast Producer weighs eligible moments and confirmed audience interest, then recommends what to show. I make the final call.” |
| 1:05–1:20 | OBS composition and actual stream output: audience question paired with the approved insight. | “OBS puts the approved insight over the match. The question adds audience context; the on-air story stays tied to checked evidence.” |
| 1:20–1:37 | Same session’s companion: switch language, detail, player focus; show **Catch me up**. | “Fans can explore the same approved facts in their language, at their level of detail, or through a player—and catch up on moments they missed.” |
| 1:37–1:50 | Stream and companion side by side; MatchSense name and verified technology caption. | “A fan’s question finds its moment. A checked story reaches the stream, and every fan can explore it their way. That’s MatchSense.” |

## Why this is MatchSense

The differentiator is the connected workflow: **audience question → verified
match moment → evidence-backed story → producer decision → OBS/YouTube graphic →
personalized companion**. MatchSense does not generate an unverified chat reply:
the Audience Agent groups questions, the producer confirms the moment, and the
overlay pairs the question with an existing approved insight.

The agents have visibly different jobs: Audience Agent groups demand; Story
Director selects the explanation; Claim Reviewer checks its claims; Broadcast
Producer recommends what is ready. They share the same session and story state,
while the human producer approves what goes on air.

This shows the hackathon’s synthetic-event-to-explainable-story-to-broadcast-
and-personalization pipeline, and makes agent roles, handoffs, and recovery
visible for the [Best Multi-Agent System category](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md). The [official challenge description](https://reactor.microsoft.com/en-us/reactor/series/s-1709/) also calls for real-time match intelligence, narratives/recaps, explainability, and personalized experiences. The final video must be under two minutes and in English or include an English translation.

## Rehearsal essentials

- Use the **Pressure Swing flagship** at 91.3 s: 30 m forward, nearby-opponent
  average 2.0 → 0.4, with 100% coverage in both windows. Keep **SYNTHETIC MATCH
  DEMO** visible; these observations do not prove intent or causality.
- Use one session for producer console, stage, overlay, and companion. Confirm
  the exact story revision is approved before selecting it for broadcast.
- For an AI run, verify the live session and agent trace. A local template
  rehearsal makes no model calls. For real audience grouping, connect an
  authorized live YouTube chat; label simulated questions as rehearsal data.
- Verify the composed output in the actual stream. OBS status is read-only and
  does not itself confirm YouTube delivery. The companion follows the app clock.
- Use a small technology caption only for services present in the recorded run
  (for example, Microsoft Agent Framework and Azure OpenAI). Use cleared audio
  and permitted visual assets.

Setup: [OBS/YouTube](youtube-pitch-demo.md) · [Audience Agent](next-iteration/audience-agent.md) · [OBS status](obs-monitoring.md).

## Evaluation note for the project page or judge Q&A

In the 15-case discovery comparison, S3 and M3 passed the same deterministic
controls; the Reviewer made no revisions, and one incomplete review was safely
contained. In the separate seeded policy challenge, both arms kept the angle in
all six matched trials. Present these as measured workflow evidence, not fan
ratings. Full results: [multi-agent evidence](next-iteration/multi-agent-evidence.md) · [discovery report](../evals/agentic/discovery-v4/README.md).
