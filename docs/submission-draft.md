# MatchSense — project page draft

## Tagline

Make the moment make sense. MatchSense connects audience questions to match evidence, routes each story through specialist AI review, and keeps the final broadcast decision with the producer. Viewers see the approved insight on the stream, then explore that same moment in a personalized companion.

## The problem

Football fan discussions surfaced a concrete challenge: new viewers ask how to understand the game beyond a chain of passes, while others describe missing movement away from the ball. MatchSense turns those questions into clear, contextual explanations of what changed and why the moment matters ([discussion from new viewers](https://www.reddit.com/r/SoccerNoobs/comments/1glgt9u/how-to-understand-the-game/), [discussion about team movement](https://www.reddit.com/r/footballtactics/comments/1uvbpqu/how-do-yall-watch-games/)).

Sports audience research also points to demand for timely, tailored context that keeps the match at the center. In IBM’s 2025 survey of 20,864 adults across 12 markets, 56% wanted AI insights across past, current and future events; 67% said faster recaps would improve their digital experience, and 65% said the same of personalization. Capgemini’s 2025 study of 12,017 sports fans found that 53% said overuse of technology had diminished the enjoyment of watching live. Together, these findings support an experience that combines useful insight with a presentation that keeps the match in focus ([IBM study](https://newsroom.ibm.com/2025-08-18-ibm-study-sports-fans-demand-more-dynamic-digital-content,-powered-by-ai), [Capgemini research](https://www.capgemini.com/wp-content/uploads/2025/07/Final-Web-Version-Report-Tech-In-Sports_V3.pdf)).

## The solution

MatchSense is a live football explanation desk for producers, paired with a viewer companion. It turns a structured synthetic match feed into stories tied to match evidence: a producer can inspect the facts, approve an exact version, and send it to an OBS overlay. Viewers can read a concise explanation or inspect the supporting measurements, switch between English and Spanish, focus on a player or team, and get an automatic recap of approved moments.

The distinctive idea is one connected editorial loop: audience questions surface the moment to investigate; match evidence from a specific time range grounds the explanation; specialist agents prepare and review the story; the producer approves the exact version; and the companion carries that same story into personalized viewing.

The Audience Agent groups related questions from an authorized YouTube Live chat or clearly labeled rehearsal input, then helps the producer select a relevant match moment. Match Insights also presents player contributions and shot, pressure and possession outcomes, with illustrative xG for synthetic shot examples.

## How it works: a pipeline with five stages

1. **Ingest:** MatchSense releases timestamped synthetic events and observations of player positions as the match clock advances.
2. **Interpret:** Deterministic code reconstructs the available match state and calculates measurements for a specific moment, such as forward pass distance, counts of nearby opponents, shot outcomes and possession windows. Each fact retains its time range, source observations and coverage.
3. **Explain:** The Story Director selects supported facts and a useful narrative angle. A constrained renderer binds names and values from source data, time ranges and qualifications. The Claim Reviewer checks the final wording against the evidence and can request a supported revision; a clearly identified factual fallback keeps the workflow moving when needed.
4. **Render:** The producer inspects the evidence and approves the exact story revision. Approved stories appear as timed graphics in the MatchSense overlay. Add the match and overlay pages as browser sources in OBS; OBS composes the broadcaster’s stream for YouTube.
5. **Personalize:** The companion presents the same approved facts in concise or detailed form, English or Spanish, with a focus on a player or team and an automatic recap of approved moments. Each viewer can choose a personal lens while the shared story remains approved by the producer.

## Behind the scenes

The AI workflow uses Microsoft Agent Framework with Azure OpenAI through Microsoft Foundry. The Story Director and Claim Reviewer have separate jobs and hand off a structured proposal with its evidence context. Deterministic Python code calculates displayed measurements, checks source cutoffs and binds numeric values into the final wording. Bounded model calls and factual fallbacks support a predictable review path, while the producer keeps final approval. Source corrections trigger a recheck so the viewer output stays aligned with the latest approved evidence.

In an Azure QA run, the Story Director proposed a story from synthetic match evidence, the Claim Reviewer supported it after a handoff that included the same evidence, and the producer approved that exact revision. The full workflow check also confirmed durable event and story storage, Spanish views and views focused on a player, the recap and stream reconnection; a later retraction removed the story from the viewer and recap. This shows the agents carrying a story through review into a viewer experience controlled by the producer.

The web app is built with Next.js, React and TypeScript. A Python FastAPI service handles replay, evidence, review and publication. In Azure, Event Hubs transports observations, Cosmos DB stores session and story state, Azure Container Apps hosts the web and API services, and managed identity connects services. Blob Storage holds Event Hubs checkpoints; Application Insights, OpenTelemetry and Log Analytics support diagnostics. The YouTube chat connector uses OAuth and the YouTube Data API. OBS adds MatchSense overlay pages as browser sources in the broadcast composition.

## Example

A viewer asks, “What changed after that pass?” The Audience Agent groups similar questions and suggests a candidate moment. In the synthetic example at 01:31, the producer selects the pass and checks its evidence: the ball travels 30 metres forward, farther than the team’s three previous completed passes in this replay (18, 25 and 22 metres). The average number of opponents within six metres, weighted by observation time, changes from 2.0 around the passer in the two seconds before release to 0.4 around the receiver in the two seconds after reception; both windows have full observation coverage.

The Story Director turns that into a short explanation, the Claim Reviewer checks it against the evidence, and the producer approves the exact revision. The approved graphic appears over the match in OBS, while the companion offers the same moment in concise and detailed views. The story keeps the focus on the observed change: forward movement and fewer nearby opponents around the receiver.

## Deployment plan

For the submission release, we will publish versioned web and API images to Azure Container Apps, configure managed identity for Foundry, Event Hubs and Cosmos DB, and keep producer and OAuth credentials in secrets stored on the server. We will verify the full journey from synthetic feed ingestion through review, approval, OBS overlay, companion and source correction, then provide judges with the application URL and access instructions for the judging period.

## Potential impact

MatchSense brings the event feed, editorial review and fan experience into one workflow. Production teams get a clear path from a match event to a broadcast story checked against match evidence; fans get an accessible explanation with the option to explore its supporting detail. The research above highlights demand for timely context, faster recaps and personalization that keeps the match enjoyable. The demo makes this approach tangible with repeatable synthetic football data and a stream and companion experience approved by the producer.
