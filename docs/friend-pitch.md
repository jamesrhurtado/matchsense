# MatchSense — friend pitch and local demo

> **24 October local mixed-event candidate:** start `make coverage-dev` and use
> [the mixed-event walkthrough](match-coverage-demo.md) for the broader pitch.
> It covers confirmed score/goals, shots, possession and control changes alongside
> passes. It uses local templates; new-family live AI and human usefulness remain
> unverified. The pass-focused script below is preserved as the baseline demo.

## Run it locally

From this project folder, start both the backend and website:

```bash
cd "/Users/james/dev/why now"
make dev
```

Open **http://127.0.0.1:3000** and keep the terminal running. Press **Ctrl+C** in that terminal to stop both servers. The API runs on port 8000. Use port 3000 for the demo; the older presenter script's reference to port 3120 was a previous rehearsal address.

This checkout already has its Python environment and web dependencies. Startup was checked on 23 October 2026: the homepage returned HTTP 200, and health/readiness reported version 0.5.0, local templates, SQLite, and local transport. This was a startup check, not a fresh full browser rehearsal.

For a fresh installation, use Node.js 22+, npm, Python 3.13, and `uv`, then run:

```bash
cd "/Users/james/dev/why now"
uv python install 3.13
uv venv --python 3.13 .venv313
uv pip install --python .venv313/bin/python -r requirements.txt
npm --prefix apps/web ci
make dev
```

The local producer key is **`local-demo-producer`**, prefilled on the landing page. Default local mode needs no Azure credentials or model calls. You do not need to copy `.env.example` to start; the application does not automatically load `.env` files. Any custom backend settings must be exported in the terminal before startup.

If port 3000 or 8000 is already occupied by this project, use the running instance or stop its existing terminal before starting another one.

## What the project does

**MatchSense helps football viewers understand why a moment matters, with evidence they can inspect and explanations a producer controls.**

A broadcast can show a pass and its numbers, but viewers still need context: what changed in this passage of play, and why highlight it? MatchSense turns match observations into a candidate story, shows the supporting evidence, and lets a producer approve the exact explanation before viewers receive it.

The working prototype has two connected experiences:

- **Producer console:** replay a synthetic match, inspect candidate moments and their evidence, request a different supported emphasis, approve an exact revision, and retract a story later.
- **Viewer companion:** explore approved explanations, inspect the facts, switch between English and Spanish, change detail or player focus, revisit approved history, and request a catch-up recap.

The key idea is the connection between **context, evidence, and editorial control**. For example, a pass that moves the ball 30 metres forward becomes more interesting when the previous three completed passes moved it only 8, 12, and 16 metres forward. The viewer can inspect those values instead of accepting an unexplained headline.

The intended users are broadcast producers and their audiences. Its potential value is helping producers prepare supported explanations and helping viewers follow the action. Editorial time savings and audience impact still need measurement.

## How it works

```text
Match observations → calculated facts → candidate explanation
                   → evidence review → producer approval
                   → shared overlay + viewer variants + recap
```

The website uses Next.js, the API uses FastAPI, and local sessions use SQLite. Measurements come from deterministic calculations. In default local mode, claim selection and bilingual wording also use deterministic templates.

The implemented Azure path adds a Story Director and Claim Reviewer using Microsoft Agent Framework and Azure OpenAI, with Event Hubs and Cosmos DB. That is a separate execution mode: starting `make dev` does not activate AI. Viewer language and focus choices select prepared variants of the approved story rather than starting a model call for each viewer.

## Your 30-second pitch

> “MatchSense helps explain the story behind a football play. It takes match observations, identifies a moment worth explaining, and shows the evidence behind the explanation. A producer reviews and approves the exact story before viewers see it. Viewers can then inspect the facts, switch language, or catch up on approved moments. I’m demonstrating it with a synthetic replay in local template mode; the project also has an implemented Azure AI workflow.”

## Prepare the two-minute demo

Use the existing [full presenter script](demo-script-v4.md) for the longer walkthrough. This is a shorter version for a conversation with a friend.

1. Open **http://127.0.0.1:3000**.
2. Choose **Previous-pass history A · 5 moments · 2.5 min**. Its ID is `match-57c134ad6e6457a4`; the selector may also append its duration in seconds.
3. Keep the local producer key and click **Open producer console**. Open its **Viewer companion** link in another tab so both views share the same session.
4. Use **Jump to second → Jump forward** at **20**, **45**, and **70**, in that order. At each stop, wait for the corresponding story, inspect it, and approve it. These approved moments prepare the history and recap.
5. Jump to **95**, select **Moment 4**, and leave it unapproved. A jump pauses the replay clock, giving you time to present.
6. Confirm its comparison: current pass **30 m forward**; previous three completed passes **8, 12, and 16 m** in chronological order. Some views show the previous passes newest first: **16, 12, 8**. These values describe forward displacement, not total pass length.
7. If that comparison is not the selected angle, use **Suggest an emphasis → Emphasis → Previous-pass comparison → Submit for review**. Wait for the new revision. Describe this as your editorial selection.
8. Check **Processing & review trace**. For the default launch, describe the execution as **local template mode**.

Do this preparation before starting the pitch. Keep the replay paused at 95 seconds until you approve Moment 4.

## Two-minute walkthrough

| Time | Screen action | What to say |
|---|---|---|
| 0:00–0:20 | Show the producer console with Moment 4 selected. | “You can see a pass, but why should it get attention? MatchSense helps a producer explain what changed. This is a synthetic football replay, paused so we can inspect it.” |
| 0:20–0:50 | Open **Show why** and inspect the evidence. | “This pass moved the ball 30 metres forward. The previous three completed passes moved it 8, 12, and 16 metres. The comparison is specific, and we can inspect its support. This doesn't mean it was the best pass of the match.” |
| 0:50–1:10 | Close the evidence panel, briefly show **Processing & review trace**, then click **Approve**. | “This local demo uses templates without AI calls. The Azure AI path adds a Story Director and Claim Reviewer around the same evidence checks. Either way, the producer approves the exact revision before publication.” |
| 1:10–1:40 | Switch to the companion. Open **Inspect the facts**, select the comparison clause, then show **Original values and sources**. Change to Spanish and add detail. | “The viewer gets an explanation they can check. They can see the comparison, inspect the source values, and switch language or detail while staying within the approved facts.” |
| 1:40–2:00 | Return to English and open **Catch me up**. | “If you missed the action, the recap uses approved stories. The goal is to make the moment understandable while keeping the evidence visible and the producer in control.” |

Allow extra time for clicks. If you prefer a simpler first rehearsal, choose original segment 01, play to **00:23**, and pause. Its first candidate becomes eligible at **00:22.2** and must be approved before **00:52.2** on the replay clock. Show evidence → approve → viewer → Spanish. That scenario is for a single-moment demonstration; the historical comparison above uses history A.

## Useful answers if your friend asks

- **“Is this real match data?”** The current demo uses original synthetic observations and fictional teams. Real footage, vendor-feed integration, and TV synchronization are not included.
- **“Is the local explanation AI-generated?”** No. Default local mode uses deterministic templates. Only claim actual AI execution when the session trace confirms it.
- **“What makes it different from a stats dashboard?”** It connects a specific explanation to inspectable evidence, exact producer approval, and several viewer presentations of those approved facts.
- **“Can the system publish automatically?”** Publication requires producer approval. A changed proposal needs fresh approval; an approved story can also be retracted.
- **“Does it understand football tactics?”** It currently explains supported geometry and possession observations. Football expertise and real-match usefulness still need independent validation.
- **“What comes next?”** Validate editorial usefulness with reviewers, test real incoming observations, and measure reliability, operating scale, and audience value.

If a candidate is missing, confirm history A, Moment 4, the 95-second clock, and completed review. If an overlay disappears, check its replay-clock expiry; approved history can remain available afterward. Start a fresh session if you need to go backward.

## Further reading

- [Project overview and setup](../README.md)
- [Full presenter script and rehearsal run sheet](demo-script-v4.md)
- [Other demonstration scenarios](demo.md)
- [Architecture](architecture.md)
- [Validation gaps](product-validation.md)
