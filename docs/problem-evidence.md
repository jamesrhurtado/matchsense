# MatchSense: problem evidence and competitive review

Researched **25 October 2026**, America/Lima. Research and recommendations, not
newly implemented functionality or participant findings. Read alongside the
[next iteration plan](next-iteration/evidence-led-product-plan.md).

## Recommendation

Position MatchSense as **a live explanation desk for football producers, with an
approved companion for viewers**. Its purpose is to help a producer choose a
supported story, check it while play continues, and give viewers a short,
understandable explanation that stays consistent when the source changes.

The research supports interest in contextual sports information, different levels
of detail, and catch-up. It also exposes resistance to distracting graphics and
unconvincing AI. It does **not** establish that producers will buy MatchSense, that
fans need another app, or that the current explanations improve understanding.
Those are the next questions to test.

Avoid claiming that football has no explanation tools. Established products and
several projects in this hackathon already address that space. Our opportunity
is a specific workflow done convincingly, with measured usefulness and visible
editorial control—not a longer feature list.

## What was inspected

Firefox Developer Edition access was verified before research. The six existing
project tabs, hackathon About page and expanded challenge were read directly in
that app. Two linked public demos were opened in new Firefox tabs. Public-source
research then covered surveys, football analysis, scholarly work, reporting and
fan discussions. This is a purposive desk review, not a systematic literature
review or a representative fan survey.

Project descriptions are authors' claims. A working page or an “AI” badge does
not independently verify its backend, model calls, metric validity or reliability.
No competitor repository was copied, no users were contacted, and no project
was liked, joined, submitted or published. Public-demo inspections were brief;
they were not full-match evaluations.

The comparison uses the actual local MatchSense source, README, metric definitions
and [existing live verification record](../evals/live-match/verification.md).
Previously recorded tests were not rerun for this documentation task.

## The problem, separated by user

| Person | Job to be done | Friction to investigate | What MatchSense can currently demonstrate |
|---|---|---|---|
| Producer/editor | Find an explanation worth airing, verify it, and publish in time | Research effort, competing incidents, limited review time, corrected data | Mixed-event queue, evidence, exact-revision approval, withdrawal, shared overlay |
| First-time/casual viewer | Understand what changed without studying a dashboard | Jargon, isolated numbers, losing track of players, too much information | Short approved copy, actors on the pitch, English/Spanish, selectable detail |
| Returning viewer | Rejoin without reading every event | Missing the sequence and reading an outdated score/story | Current source score and approved segment recap; “since I left” is not yet implemented |
| Analyst-minded viewer | Inspect the measurement and its scope | Unstated windows, incomplete observations, unsupported tactical interpretation | Intervals, denominators, coverage, scoped comparisons and underlying observations |
| Potential buyer | Support a useful editorial output at an acceptable cost | Integration, data rights, reliability, adoption and editorial accountability | Local prototype and earlier separate Azure build; no buyer or production validation |

An initial buyer hypothesis is a small digital football production team that
already has lawful access to an appropriate event/tracking feed. This is a
recruitment hypothesis, not a validated market segment. MatchSense does not collect
professional football data from video or eliminate the need to license it.

## Evidence ledger

Each finding separates the source result from our interpretation. Source IDs are
used in the iteration plan to avoid turning recommendations into research facts.

### E1 — Timely information, personalization and catch-up have an audience

[IBM's 18 August 2025 survey release](https://newsroom.ibm.com/2025-08-18-ibm-study-sports-fans-demand-more-dynamic-digital-content,-powered-by-ai)
reports that 56% wanted AI insights/commentary across past, current and future
events; 67% agreed faster recaps would improve their digital experience, and 65%
said the same about personalization. It reports 73% using mobile sports apps.

Method: June 2025 online survey, 20,864 adults across 12 markets, unweighted,
covering multiple sports including football. IBM commissioned it and sells sports
AI services. These are stated preferences, not observed adoption or willingness
to buy this product; they are not percentages of football fans or Peruvians.

**Implication:** test a concise, mobile catch-up experience and useful audience
differences. **Not supported:** a promised increase in retention, revenue or
comprehension, or a claim that most fans want constant automated commentary.

### E2 — More technology can make the experience worse

[Capgemini's 2025 research brief](https://www.capgemini.com/wp-content/uploads/2025/07/Final-Web-Version-Report-Tech-In-Sports_V3.pdf#page=35)
reports 53% saying overuse of technology has diminished live-viewing enjoyment,
57% anticipating compromised authenticity from excessive technology/data, and
57% concerned about false content spreading misinformation about players/teams
(printed pages 35–36).

Method: March–April 2025, 12,017 sports fans in 11 countries/regions; methodology
on printed pages 55–57. This is another commercial research sponsor, not a
football-only experiment. The percentages measure attitudes, not failure rates.

**Implication:** selective stories, a readable display and optional detail are
better hypotheses than permanently filling the screen with indicators. Test
whether people can keep following the match while using the companion.

### E3 — Some football viewers struggle to see meaning beyond the ball

In [r/SoccerNoobs, “How to understand the game?”](https://www.reddit.com/r/SoccerNoobs/comments/1glgt9u/how_to_understand_the_game/)
(November 2024), a newcomer describes seeing only a chain of passes and asks
what to look for. In [r/footballtactics, a beginner's question](https://www.reddit.com/r/footballtactics/comments/1tmj2dg/im_trying_to_understand_soccer_tactics_better_as/)
(May 2026), a poster describes difficulty following player roles and overall
movement even while using a scores app.

A [separate discussion about watching games](https://www.reddit.com/r/footballtactics/comments/1uvbpqu/how_do_yall_watch_games/)
(July 2026) includes a self-described experienced player/coach who misses off-ball
movement. Replies also argue that watching football should remain enjoyable,
rather than becoming analytical work. A [discussion of excessive statistics](https://www.reddit.com/r/football/comments/1vbmahg/has_football_analysis_become_too_focused_on/)
contains disagreement about whether numbers help or obscure context.

These are self-selected anecdotes across three communities, not authenticated
expert interviews or estimates of prevalence. They can contain factual mistakes.
They motivate interview questions; they do not validate tactical claims.

**Implication:** show who was involved, the observed change, and one understandable
reason for selection. Test whether the viewer can paraphrase it. A statement such
as “18 m forward” may still leave the newcomer's question unanswered.

### E4 — Football visualization research supports testing different presentations

[Sezen, Tsekleves and Mauthe (2020), Abertay's publication record](https://rke.abertay.ac.uk/en/publications/bar-charts-versus-plain-numbers-visualizations-for-enhancing-the-/),
describes prototype comparisons of numbers and charts for football second screens;
effectiveness and enjoyment differed by visualization. The accessible abstract
does not establish a universal winning format or provide enough detail for a
product effect-size claim.

[Lung, Zheng and Wang (AHFE 2024)](https://openaccess.cms-conferences.org/publications/book/978-1-964867-30-4/article/978-1-964867-30-4_31)
studied 36 people, split into 18 higher- and 18 lower-experience viewers, using
simulated football penalty-shootout videos. Their results distinguish understanding
and preferences across information types and viewer experience. This narrow
experiment is not evidence for live open-play use or MatchSense.

**Implication:** compare plain-language and analyst presentations with real users;
do not equate more charts or a 3D pitch with better understanding.

### E5 — Turning data into broadcast stories is an established job and market

[Stats Perform's editorial service](https://www.statsperform.com/products/editorial-data/)
describes specialists using tools to find narratives for commentators and media,
including live use. [Opta Live](https://www.statsperform.com/products/opta-live/)
already markets automatic story discovery, alerts, visualizations, historical
context and access to expert researchers. This is supplier evidence of an
existing product category, not an independent measurement of unmet demand or
MatchSense's advantage.

**Implication:** interview producers about their current tools and handoffs. Our
claim should be a tested improvement to a particular editorial task. “Nobody
explains football in real time” is indefensible. Historical records and expert
research are incumbent strengths that our four-minute simulations cannot match.

### E6 — Football momentum analytics already exist

[AWS/Sportec/DFL's Match Momentum account](https://aws.amazon.com/blogs/media/bundesliga-match-fact-match-momentum-revealing-the-games-invisible-pulse/)
describes a live attacking-dominance signal using weighted, decayed five-minute
indicators, with momentum defined from the difference between team threat values.
This is a partner implementation account, not an independent outcome trial.

**Implication:** a new “momentum” or “chaos” gauge is not automatically novel. Our
current nearby-opponent measure is narrower and cannot inherit those meanings.
Keep the before/after evidence legible; do not invent a universal tactical score.

### E7 — Data disagreements need qualifications, not blanket distrust

[Eliot McKinley's American Soccer Analysis article, 2 October 2019](https://www.americansocceranalysis.com/home/2019/9/30/shots-in-the-dark-how-data-providers-tell-us-different-versions-of-what-happened)
reports that, among 45 sampled shots from two 2018 World Cup games, 30% had a
longitudinal-location range exceeding five yards across four providers. The
author lacked true shot locations and could not name the most accurate provider.
This is an old, bounded comparison—not a current industry error rate.

**Implication:** retain source identity, coverage and corrections. Source-linked
text can still be wrong if the source is wrong. Hashes establish version identity,
not football truth; producer approval does not independently validate the feed.

### E8 — Human data collection is real, but MatchSense does not automate it

[Rest of World, 23 June 2026](https://restofworld.org/2026/fifa-world-cup-ai-data-workers/)
reports manual annotation work and interviews workers and researchers. Its roughly
$70-per-match example concerns one Rio-based worker recording local-match events
for betting, not an industry-wide wage for all detailed event tagging. The report
also includes lower-visibility matches; it does not establish that all non-elite
football lacks data.

The blanket claim that women's football has no data is contradicted by
[StatsBomb's documented women's-football programme in 2023](https://statsbomb.com/news/statsbomb-offers-free-analytics-support-to-womens-teams-in-2023-24/)
and [Stats Perform's NWSL account in 2026](https://www.statsperform.com/insights/stars-storylines-stats-nwsl-2026/).
Coverage and affordability gaps may exist, but their extent requires separate
evidence.

**Implication:** acknowledge collection labour and feed dependencies. Do not use
tagging costs to claim MatchSense saves that work or serves untracked matches today.

### E9 — Sports AI mistakes are a concrete risk, not a measured MatchSense rate

Wimbledon's 2024 AI-written Catch Me Up published incorrect player details.
([Guardian reporting](https://www.theguardian.com/sport/article/2024/jul/01/ai-writer-served-by-wimbledon-and-ibm-commits-double-fault),
1 July 2024.)

This tennis example motivates checking factual copy; it does not quantify error
rates in football or establish that our two roles eliminate hallucinations.

### E10 — Football definitions constrain what we can explain

[FIFA's pressure definition](https://www.fifatrainingcentre.com/en/fwc2022/efi-metrics/efi-metric--pressure-on-the-ball.php)
involves closing space toward the ball carrier. A count inside a radius does not
by itself establish this behavior. [FIFA's possession-control description](https://www.fifatrainingcentre.com/en/fwc2022/efi-metrics/efi-metric--possession-control.php)
includes an in-contest state. Unobserved time in MatchSense must not automatically
be called contested time; missing evidence and observed lack of control differ.

**Implication:** preserve the current measurement qualifications and explicit
denominators. Explain them in useful language before exposing technical records.

## What The Ninety Labs teaches us about framing

[The Ninety Labs project page](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126492)
starts with a specific activity, its human cost and inconsistencies, then connects
it to a proposed video-to-event system, benchmark and explanation pipeline.
That structure is more concrete than opening with a slogan about the beautiful game.

Borrow the **argument structure**: person → task → evidence of friction →
consequence → demonstrated solution → measurement. Do not borrow its problem
unchanged: its upstream event extraction is outside MatchSense's current capability.
The page's staffing/turnaround claims were not independently established here;
do not repeat them as verified. E7–E8 give the necessary limits on its two headline
statistics. Its broad coverage claim should not be repeated.

## Six-project comparison

This table records the pages as seen on 25 October, not a ranking of final entries.
“Not observed” is not proof a feature is absent. Registration likes, team size,
test counts and technology count are not measures of product quality.

| Project and source | Described scope / overlap | Evidence inspected and advantages | Lesson for MatchSense |
|---|---|---|---|
| [The Ninety Labs](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126492) | Video auto-eventing, synthetic footage/hidden labels, targeted data generation, agent explanations, overlays and accessibility | Description read; repository field “–”; no functioning extraction demo tested. Much stronger upstream focus than ours, if demonstrated | Make our editorial problem equally concrete. Do not pivot into vision or claim to solve collection |
| [Pulse: Football Insights You Can Verify](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126354) | Evidence packs, 2D/3D pitch, networks, attacking lanes, casual/analyst, recap | Description separates template prototype from planned model/cloud work; repository field “–”. Runtime not tested. Advertised spatial analytics exceed ours | Evidence, audience modes and fictional data are shared territory. Spatial explanations deserve a usability test, not an automatic 3D rebuild |
| [PitchPulse – AI Broadcast Director](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126499) | Live stats, human on-air controls, verified narratives, languages, voice, match Q&A/MCP, timed graphics | Public demo inspected: kickoff, advancing clock, draft card, On air/Drop controls and numeric evidence disclosure. UI labeled a card AI/fact-checked; backend not audited. Voice, seven languages and Q&A correctness not tested | Stronger public try-it path, discovery controls and feature breadth. We must show task success and correction behavior rather than claim generic verification is unique |
| [Virtual Studio Crew](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126365) | Five roles, live explanations, multilingual personas, graphical cues, spoken recap | Public demo inspected: simultaneous audience panels, play-by-play, Studio feed, template labels and later displayed verification/handoff results. Stopped around simulated minute 30; no complete-match or speech test. Page's 9.9 s median/30-story evaluation was not reproduced | Clearest side-by-side audience demonstration and most visible role handoffs. Add a compact preview and explain consequential decisions; character art/extra agents are not necessary |
| [Second Guess: The Football What-If Engine](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126312) | Alternative decisions, simulations and estimated outcome differences | Description read; repository field “–”; no functioning simulator tested. Immediately understandable question and interaction | Borrow specificity of the user question. Counterfactual probabilities require calibration we do not have; do not add them for spectacle |
| [My project idea: MatchMind AI — The AI Football Analyst](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126324) | Live interpretation, rolling-window momentum, evidence, audience modes and visible agents | Description and repository link inspected; embedded video/runtime not evaluated. Clear list of user questions and a concise screen story; quality/superiority claims unverified | “What changed?” is a stronger entry point than “Suggested insight 3”. Our current scoped comparison does not establish a match-level tactical turning point |

The two inspected public demos:
[PitchPulse](https://pitchpulse.livelyfield-1dcb67cb.polandcentral.azurecontainerapps.io/)
and [Virtual Studio Crew](https://studio-crew.politebay-c6735be6.canadacentral.azurecontainerapps.io/).
Neither was tested for correction propagation, restart behavior, mobile usability,
or full numerical/semantic validity. Do not declare superiority from their absence
in these brief inspections. The first demo was paused; the second was stopped.

## What is shared, missing, and worth making distinctive

**Shared territory:** synthetic live events, AI explanations, evidence inspection,
casual/analyst output, multilingual delivery, player/team interest, graphics and
recaps. Several projects advertise verification and purposeful agent roles.

**Gaps worth addressing:** plain-language evidence, a readable editorial decision,
an immediate comparison of audience outputs, and incremental catch-up with visible
source corrections. The last is a promising differentiation hypothesis; this
review does not establish that no competitor has it.

**Defensible demonstration:** show a supported story selected, reviewed and
approved while play continues; then correct the source and visibly withdraw the
dependent story across overlay, history and recap. Explain what the system does
not know. Current infrastructure supports much of this, but participant usefulness
and operational advantage remain unproven.

**Do not race on:** number of agents, number of gauges, inflated “zero
hallucinations” claims, arbitrary confidence percentages or uncalibrated tactical
causation. Adding more features could reduce the time available to demonstrate
the completed workflow.

## Contest fit and delivery constraints

Read directly in Firefox: [About and rubric](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/home/getting_started)
and [full challenge](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/executive_challenge_details/5078/about).
The [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md)
were also cross-checked.

The central fit is synthetic football events → interpretation → explanation →
on-screen output → different audience experiences, with live responsiveness,
recaps and multilingual storytelling. Speed, pass difficulty and video auto-eventing
appear as features to consider; they are not all mandatory features for every entry.
Synthetic data is required; a real-feed integration is not needed for this slice.

Each rubric area carries 20%: technological implementation, agentic innovation,
real-world impact, experience/presentation and category adherence. The Grand Prize
is the strongest overall product target. Foundry and multi-agent categories need
their own evidence; role count does not establish effective collaboration.

Submission closes **27 October 2026 at 23:59 Pacific**, according to the rules;
the wider date banner is not the submission deadline. Requirements include a
functioning demo video **under two minutes**, public GitHub source and judge access
through the judging period. Our README still identifies private source and an
older, separate hosted build. Release actions need their own owner authorization.

## Pitch language we can use

> During a football match, a useful explanation has a short window: someone must
> choose the story, check its evidence and make it understandable while play
> continues. MatchSense gives a producer a live explanation desk. AI proposes supported
> stories; the producer approves what viewers receive, with simple or analytical
> detail in English or Spanish. The same evidence supports the overlay and catch-up
> recap, and source corrections withdraw affected explanations. We demonstrate the
> workflow with simulated live football data.

Present the producer difficulty as the workflow being tested, not as measured
industry-wide waste. Use E1 or E2 for a carefully qualified audience statistic,
then move quickly to the functioning product. Do not claim labor savings, retention
uplift, tactical truth or purchase intent before measuring them.

## What would change the recommendation

- If producers already obtain sufficient trusted stories faster in their tools,
  integration or a viewer-only companion may matter more than another desk.
- If human approval consistently misses live windows, reduce low-value suggestions
  and revisit the workflow prospectively; do not remove the approval policy to
  make a demo appear faster.
- If viewers prefer the match alone, keep insights optional and concentrate on
  catch-up rather than an always-on feed.
- If a concise explanation does not outperform bare stats in the pilot, revise
  the content before investing in speech, chat, 3D or extra metrics.
- If the proposed producer has no usable tracking feed, the present pressure
  explanation is unavailable. That is an integration constraint, not something
  an LLM can fill in.

Real producer interviews, independent football/Spanish review, comprehension
comparisons, buyer willingness and production integration remain pending. The
[iteration plan](next-iteration/evidence-led-product-plan.md) defines the next tests.
