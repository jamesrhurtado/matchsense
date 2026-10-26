# Live-match explanation desk

MatchSense explains a match as it unfolds. The source here is a prerecorded synthetic
segment delivered over time, not a real match broadcast or a prediction. AI and
producer review run while play continues. Recaps and history support that live use.

## Start locally

Install the existing project dependencies and sign in with `az login` to the
existing authorized Azure model account. Then:

```sh
npm --prefix apps/web run build
make live-dev
```

Open **http://127.0.0.1:3100**. Keep **Live simulation** and **AI · Director and
Reviewer** selected, then click **Start live simulation**. The four-minute feed
starts immediately at 1×. No pause, speed or seek controls exist in this mode.

The launcher verifies the existing model/version, current retail prices and Azure
CLI authentication. It uses local SQLite `.run/live-match.db` and the existing
GPT-4o mini deployment, not new cloud resources. Each live session reserves at
most 96 model calls conservatively; at the checked rates the launcher refuses a
reservation above $0.50. Actual usage is reported separately and is usually much
lower. This is not a monthly Azure spending cap; producer-requested edits use
separate existing bounded workflows. Do not print credentials or share the local
producer key in public hosting.

If AI is not configured, the entrance disables AI start and explains why. Choose
**Template preview · no AI calls** explicitly for offline UI testing. To learn the
controls, choose **Guided walkthrough**; it retains pause/seek and guided stops.
These are distinct experiences, never silently substituted for a live AI test.
Ordinary `make coverage-dev` supplies the offline backend, with that explicit
Template preview choice. The earlier Azure engineering deployment is separate.

## Present the workflow

- Introduce selective help: “Fans want to enjoy the match. MatchSense gives producers
  supported explanations and lets viewers choose when to go deeper.”
- Start a new simulation and explain: “This synthetic feed represents a match
  happening now. The producer reviews explanations while the match continues.”
- Around 16–25 seconds, inspect the first supported pass/pressure insight. Show
  the evidence and the clock still advancing. Approve before its live window
  expires; expired candidates can only be approved for history.
- Open **Viewer companion**. Show the approved insight, casual/analyst detail,
  Spanish and an involved player. Viewer choices do not change the shared match.
  Live viewers begin in **Match first**, without automatic explanation overlays
  or a changing explanation sidebar. Choose **Explore explanations** to open
  those tools. **Catch me up** is available in either view.
- In the producer's **Preview for viewers**, compare casual and analyst wording,
  then Spanish. This reads the selected revision without publishing or calling
  a model. Phones show one preview at a time. The queue shows three suggestions
  plus the selected one; **Show all** and filters retain the rest. Every event
  family remains available.
- Return to the producer: shots, recovery/control changes and possession windows
  enter the queue. Live possession suggestions use complete one-minute boundaries
  to reduce repetition; evidence intervals and the original expiry remain explicit.
- A confirmed goal changes the source score at about 01:44 independently of
  whether a producer approves its explanation. The correction scenario later
  cancels that goal and withdraws affected approved text and recap entries.
- At 04:00, the segment ends. Open its approved recap. It does not auto-loop or
  imply full time for a complete match. **New simulation** ends the old simulation
  and creates fresh approvals; **End simulation** stops early and retains history.

For a short recording, show an uninterrupted excerpt and use disclosed editing
for later scenes. Do not claim paused/accelerated replay as real AI latency.

Catch-up offers **Whole segment**, **Last minute**, and **Since I joined** or
**Since my last visit**, with an explicit interval. Visit information stays in
that browser, never the share URL. Corrections refresh an open recap and add a
withdrawal notice without repeating old copy. Current score/validity are checked
now, even for an earlier requested interval. An empty recap means no approved
explanations in that interval, not that nothing happened.

### Research opening for the later submission video

“More information is not always a better match experience. In Capgemini's 2025
multi-sport survey, 53% said overuse of technology had diminished live-viewing
enjoyment. MatchSense lets producers choose supported stories and fans choose when
to explore them.”

Credit: [Capgemini, printed page 35](https://www.capgemini.com/wp-content/uploads/2025/07/Final-Web-Version-Report-Tech-In-Sports_V3.pdf#page=35),
March–April 2025, 12,017 sports fans in 11 countries/regions. This is an attitude
survey sponsored by a technology-services company, not a football-only trial or
proof that MatchSense reduces distraction. Put the source on screen. Participant
testing must establish our actual effect; do not claim it is proven.

## Five-minute reviewer task

**What you are testing:** a producer reviews AI suggestions while a simulated
match continues; viewers choose whether to explore approved explanations.

1. Open **http://127.0.0.1:3100** on the host computer. Keep **Live simulation**
   and **AI · Director and Reviewer** selected; click **Start live simulation**.
   This uses actual AI. **Template preview** tests the controls without AI calls.
2. Let the four-minute match run. When a suggestion arrives, read **What changed**
   and inspect its evidence. The clock keeps moving; you do not need to approve
   every suggestion.
3. Open **Preview for viewers**, compare casual/analyst wording and Spanish,
   then approve one explanation. Preview alone does not publish. If its live
   window has expired, approval is for history only.
4. Open **Viewer companion** in another tab. **Match first** keeps viewing quiet.
   Choose **Explore explanations** to see approved stories, change language/detail
   and try an involved player focus. Draft suggestions must stay private.
5. Open **Catch me up** and choose **Last minute** or **Whole segment**. Check the
   interval. An empty recap means no approved explanations in that interval.
6. Return to the producer and retract your approved story. Check that it disappears
   from the viewer and refreshes an open recap. At **04:00**, the replay ends;
   another match starts only when you choose **New simulation**.

The score follows confirmed source events, independently of explanation approval.
This is simulated live delivery, not a real fixture or a prediction.

Tell us: **What does the product do? Did an explanation help? Did you miss match
action while using it? What was confusing or unsupported?** Rate usefulness 1–5.

Football reviewers should assess the measurement and wording, including the
nearby-opponent limitation. Nobody should infer tactical intent or a cause of a
later goal. Record whether the attempt used actual AI, fallback or templates;
separate producer and viewer observations. Participants and findings remain
pending until real people complete these tasks.

## Verify and interpret results

```sh
make test
make synthetic-evaluate
make coverage-evaluate
# Against a coverage-enabled local template server:
PLAYWRIGHT_BASE_URL=http://127.0.0.1:3000 npm --prefix apps/web run test:e2e
# Explicit existing-model browser test (makes model calls):
WHY_NOW_LIVE_AI_E2E=1 PLAYWRIGHT_BASE_URL=http://127.0.0.1:3100 \
  npm --prefix apps/web run test:e2e -- live.spec.ts
```

`scripts/verify_live_match.py` runs one stream and then two at continuous 1×,
without pause, seek, automatic approval or API/browser reads during playback. It
reads durable package/outcome records directly and reconciles handwritten
references. It requires the model API and a local SQLite path to the same store.
The 25 referenced logical opportunities per scene are not independent matches;
the new mirrored/fault scenes share an authored trajectory backbone. Full reports
retain missing candidates, abstention/rejection, fallback, incomplete usage and
missed review-time targets. Detailed source-delivery-to-browser timing, independent
football validation and cloud operating limits require separate evidence.
