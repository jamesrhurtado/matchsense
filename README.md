# WHY/NOW

**Current experience: the local live-match explanation desk below.** The [earlier Azure engineering build](https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io) is separate and does not contain this iteration. See [QA access and testing](docs/qa.md) and [deployed Azure resources](docs/azure/README.md).

**Source:** [jamesrhurtado/why-now](https://github.com/jamesrhurtado/why-now), currently private at the owner's request. Original project source is licensed under [MIT](LICENSE).

**Explain the match. Let fans enjoy it.** A live football explanation desk: AI suggests supported stories, a producer approves them, and fans choose when to explore an explanation or catch up. Demonstrated with fictional teams and a synthetic feed.

## Live-match explanation desk — local candidate

The main experience now delivers a synthetic match continuously at 1× while AI
suggests explanations and the producer reviews them. The viewer receives only
approved insights. Source-confirmed score and clock update separately. Background
processing continues with no browser open; inspecting history never rewinds the
shared match. The feed stops at the end, with approved history and catch-up recap.

Live viewers now start in **Match first**, with the pitch, score and clock. Open
**Explore explanations** for approved insights, evidence, Spanish and player/team
focus. **Catch me up** covers the whole segment, last minute or a private
browser-local visit interval. Corrections remove affected copy and show a concise
withdrawal notice; an open recap refreshes without closing. These controls are
intended to reduce interruption; real-user evidence is still pending.

Producers get an optional **Preview for viewers** for casual/analyst and Spanish
variants of the exact selected revision, plus a compact selection/review disclosure.
Previews never publish or add model calls. The queue starts with three suggestions
and the selected item; **Show all**, family filters and archives preserve access
to every family. Evidence inspection keeps a small match clock visible.

```sh
npm --prefix apps/web run build
make live-dev
```

Open **http://127.0.0.1:3100**, choose **Live simulation** and **AI · Director and
Reviewer**, then **Start live simulation**. This reuses the existing Azure model
and requires Azure CLI authentication; it provisions no resources. The launcher
verifies model identity/rates and credentials before serving. AI attempts, failures
and factual template fallback remain identified. Current local configuration is
not a deployment of this iteration to Azure. The local pilot has real-model and
continuous-play evidence, but the proposed review-time target is not met; see
[verification and limitations](evals/live-match/verification.md). See [startup, walkthrough and short
reviewer tasks](docs/live-match-demo.md), [the implementation plan](docs/next-iteration/live-match-plan.md)
and [delivery record](docs/next-iteration/decision-log.md).

Without Azure credentials, use `make coverage-dev` and explicitly choose
**Template preview · no AI calls** at the entrance. That tests the interface and
rule-based output, not model quality. **Guided walkthrough** separately retains
pausing and navigation for onboarding. Existing stored packages remain unchanged.

## Broader match coverage — local engineering candidate

**New synthetic-data slice (SD01–SD04):** six distinct development parents,
twelve paired 90-second passages and base/delivery-check views. Movement uses
smooth bounded paths; support/keeper targets use the episode ball; events and
control share the same state. Independent checks cover motion, source alignment,
missing evidence, delayed outcomes, corrections and explicit possession coverage.
The original default replay and stored packages remain unchanged.

To try these additional passages offline:

```sh
WHY_NOW_SYNTHETIC_DEVELOPMENT=1 make coverage-dev
```

At **http://127.0.0.1:3000**, choose **Guided walkthrough**, **Template preview**,
then **More demo scenarios → Development passage 01**. The optional catalogue
contains passages 01–12 and their delivery-check versions. See the
[dataset card and short walkthrough](docs/synthetic-dataset-v1.md) and
[separate verification](evals/synthetic-vnext/verification.md). Reproduce with
`make episodes-data` / `make episodes-evaluate`. These are development scenes;
held-out/real-model comparisons and football/user validation remain pending.

The opt-in mixed replay adds source-confirmed clock/period/score, corrected goals,
resolved shots, explicit recovery/control changes, and fixed possession windows.
All story families use producer approval, English/Spanish, relevant player/team
focus, family-specific evidence and approved timeline/recap. Score updates are
source state and do not imply an approved explanation. Existing pass packages
and the original 173-replay regression remain intact.

The local match view now has a broadcast-style scoreboard, original fictional club
crests, a textured pitch, observed control labels and an approved-story lower
third, with responsive English/Spanish layouts. See the [visual design record](docs/match-stage-design.md).

```sh
make coverage-dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000), select **Pressure Swing flagship · guided mixed-event pitch**,
choose **Guided walkthrough** and **Template preview · no AI calls** for the offline walkthrough, and use the prefilled local producer key. The command enables
`WHY_NOW_MATCH_COVERAGE=1` and isolates SQLite in `.run/match-coverage.db`.
Coverage is off in ordinary `make dev`; the eight additional fixtures have a separate
catalogue. The guided demo uses continuous authored player/ball movement and keeper lanes,
and, in Guided walkthrough, pauses at the first example of each event type so you can inspect and approve
it. Pressure Swing pauses at the comparative 30 m pass, around 91.3 s. Turn off **Pause at new event types** for continuous playback. **Check the evidence**
opens the supporting facts and brings them into view. Observation counts are
position samples/source records, not football incident counts. The original mixed
fixtures and stored approvals remain unchanged. No Azure credentials or paid calls
are needed. See the
[mixed-event walkthrough](docs/match-coverage-demo.md),
[event definitions/rollback matrix](docs/match-events.md),
[verification record](evals/match-coverage/pressure-flagship/verification.md) and
[pilot materials](docs/match-coverage-pilot.md).

The new **Pressure Swing** insight compares time-weighted nearby-opponent averages
before a pass and after reception, with explicit intervals and coverage. The new
flagship demonstrates **2.0 → 0.4** around a **30 m forward pass**, plus a scoped
comparison against three previous team passes. “Why this moment?” is separate
from factual evidence; casual/analyst and relevant player views share approved
facts. This is a proximity proxy, not tactical intent, pass difficulty or a cause
of the later goal. See [the flagship walkthrough and rubric rationale](docs/pressure-flagship.md).

This is a local engineering candidate. Recruitment, external football/Spanish
ratings, real-user findings and deployment of this iteration remain pending. A bounded real
**gpt-4o-mini 2024-07-18** smoke now verifies pressure, shot, goal, recovery and
possession through Director/Reviewer (10 calls, exact source-rendered bilingual
text). It does not establish broad model quality or user usefulness. The hosted
0.5 build remains separate and has not been updated.

## Working local MVP

This section records the earlier guided/pass-focused engineering workflow. Its
template-mode and pausable startup instructions are historical alternatives;
use **Live-match explanation desk** above for the current main experience.

The local version 0.5 candidate adds v4 editorial rendering, concise role-focused text, consistent measurement precision, comparison bars, explicit earlier-moment navigation, and atomic acceptance accounting. See [the latest quality handoff](docs/next-iteration/quality-v4-handoff.md), [multi-agent evidence](docs/next-iteration/multi-agent-evidence.md), and [reviewer guide](docs/next-iteration/reviewer-guide-v4.md). This local update has not replaced the previously documented Azure build.

The local application implements synthetic replay → deterministic metrics → evidence replay → constrained wording review → exact-revision producer approval → timed shared overlay → English/Spanish companion variants and approved-moment recap.

Local mode uses **deterministic claim selection and bilingual rendering**. It does not call an AI model. The hosted environment adds Microsoft Agent Framework with Azure OpenAI, Event Hubs transport, Cosmos persistence and managed-identity access. The default local mode remains available for offline development. Actual resources are documented in [docs/azure](docs/azure/README.md).

The current local iteration adds bounded previous-pass context, distinct factual titles, a compact mobile evidence pitch, role-first player views and grouped approved recaps to the two-role Story Director / Claim Reviewer workflow. The model selects and orders verified facts; bilingual wording, names, values, actor roles and qualifications resolve through the validated renderer. Explanations include forward pass displacement and reception zone, separate from subsequent team progression. Each workflow attempt has a durable outcome, including abstention and rejection. Stored version 1 and 2 packages remain readable with unchanged text/hashes; new structured generation produces version 3. [Iteration status](docs/next-iteration/decision-log.md) distinguishes completed implementation from pending model comparisons and human studies.

## Run locally

Requires Node.js 22+, npm, Python 3.13 and `uv` (or pip in a Python 3.13 environment).

```bash
uv python install 3.13
uv venv --python 3.13 .venv313
uv pip install --python .venv313/bin/python -r requirements.txt
npm --prefix apps/web ci
make dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The local producer key is prefilled. Choose segment 01 and open the console, set 1× or 2× speed, then press Play. A candidate becomes eligible at **00:22.2**, after the three-second retention window. Select **Show why**, replay the evidence, and approve before **00:52.2**. The overlay then expires on the replay clock. Pause the live replay if you need more editorial inspection time.

Open the **Viewer companion** link to see the same session, change detail/language/player focus, and choose **Catch me up**. A new replay creates a new session and preserves the previous session's audit history. Segments 02 and 03 intentionally produce no candidate.

For separate processes:

```bash
.venv313/bin/python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev
```

The producer access key is read by the API from `WHY_NOW_PRODUCER_TOKEN`; the documented local default is `local-demo-producer`. Set a private value before any shared hosting. Enter it in the landing page; it stays in the current browser tab's session storage. The viewer does not need a key. The application does not automatically read `.env` files: export backend variables in the shell. Set `API_URL` when the web server must reach an API other than `http://127.0.0.1:8000`.

## Verify

```bash
make test
make data-check
make evaluate
make synthetic-evaluate
make web-build
make coverage-evaluate  # separate new-family hand references and physical/feed checks
# With API and production web server running:
npm --prefix apps/web exec -- playwright install chromium
npm --prefix apps/web run test:e2e
```

The browser tests cover the actual producer/viewer flow, Spanish and focus variants, review changes, retraction, phone layout, and streamed updates through the web proxy. See [evaluation results](evals/REPORT.md) for measured local processing and the exact scope of the synthetic evaluation. The backend and web checks have passed on [GitHub Actions](https://github.com/jamesrhurtado/why-now/actions/runs/39615382555). CI configuration is in `.github/workflows/ci.yml`.

## Expanded synthetic data

The v2 generator provides **168 reproducible cases across 28 scenario families and six parent configurations**, including near misses, missing observations, late arrivals, duplicates, corrections, different actual receivers and longer sequences. See the [generation and testing guide](docs/synthetic-data.md) and [expanded evaluation](evals/synthetic-v2/REPORT.md), which reports current failures explicitly.

```sh
make synthetic-list
# Export one case using the existing data contract:
.venv313/bin/python -m simulator.suite --case p01-01
# Export the complete corpus under .run/synthetic/:
make synthetic-data
make synthetic-evaluate
```

Runtime exports contain only observations; seeds, fault plans, clean future trajectories and expected results are separate offline files. The application catalogue offers all 173 replays, including three-minute segments. Each pass has its own investigation, approval and recap entry; viewers can select approved history without changing the shared live overlay. All 168 constructed cases and 594 checkpoints pass with unchanged inputs and references. Synthetic results do not establish real football accuracy. The expanded suite also caught and now guards a distance-rounding defect.

## Try contextual explanations

Choose **Previous-pass history A** or **B** on the landing page. Both contain five moments over 2.5 minutes. In the producer console, jump to second 95 and select Moment 4. The present passage is identical: 30 m forward. History A has previous completed passes of 16, 12 and 8 m; B has 36, 34 and 32 m. Only A supports a comparison. Inspect the exact evidence, approve, then open the viewer companion. Select **Inspect the facts** and the comparison sentence to see the three-pass table. Replay history stays collapsed on phones.

Producer **Suggest an emphasis** offers movement/reception and supported previous-pass comparison. Each edit creates a new exact proposal for approval. Recap groups similar approved facts, links to their moments and never claims a trend. The two new replays are developer discovery material sharing one trajectory backbone; they do not establish independent football validity. Regenerate with `.venv313/bin/python -m simulator.context_replays`.

See [current delivery status](docs/next-iteration/decision-log.md), [runtime measurements](docs/runtime-performance.md) and [validation gaps](docs/product-validation.md). The 90+ reassessment remains open pending human/model/operational evidence.

## Repository map

| Directory | Purpose |
|---|---|
| `apps/web` | Next.js producer, companion and shared overlay routes |
| `services/api` | FastAPI, producer authorization, SSE, approval and recap APIs |
| `engine` | Contracts, time-scoped metrics, bounded template/Foundry workflows, SQLite/Cosmos repositories and Event Hubs transport |
| `simulator` | Seeded generator and independent structural/physical checks |
| `data/runtime` | Original 173 observation-only replays plus eight opt-in mixed-event fixtures; metadata and JSON Lines/gzip observations |
| `data/schemas` | Versioned JSON Schemas exported from Pydantic contracts |
| `data/evaluation-only`, `evals` | Offline labels, split configurations and results; never exposed through runtime tools |
| `docs` | Architecture, metric definitions, demo guide, implementation status, Azure specifications |

## Delivery status and limits

The local and Azure implementations are available; see the QA guide for completed live checks and remaining test boundaries. Competition submission packaging remains pending. [Implementation status](docs/implementation-status.md) maps the handoff's acceptance phases to evidence and outstanding work. [Demo guide](docs/demo.md) describes what can honestly be shown now.

The [PM update handoff](docs/next-iteration/pm-update-handoff.md) summarizes the contextual update, verification, ordered implementation commits and remaining release gates.

The [broader match implementation plan](docs/next-iteration/match-coverage-implementation-plan.md) governs this iteration. The [implementation record](docs/next-iteration/decision-log.md) identifies delivered changes and outstanding evidence. The [Pressure Swing walkthrough](docs/pressure-flagship.md) describes the current flagship demo and its measurement limits.

Local mode uses SQLite. Cloud mode uses Cosmos and Event Hubs, with one API worker/replica enforced for this engineering environment. It supports independent pass investigations across each segment, two fictional teams, 22 active players and 10 Hz observations. Runtime evidence is limited to the delivered clock. The underlying dataset is synthetic, with six authored parent configurations. Local tests do not establish real-match tactical accuracy, general semantic verification, production scale, or measured editorial savings.

No real match records, footage, team logos, viewer accounts or third-party TV synchronization are included. Cloud producer access uses a private key and request limits; enterprise multi-tenant authorization is future work. The repository and submission video have not been published.

## Recommended next priorities

The [25 October problem evidence and competitor review](docs/problem-evidence.md)
and [evidence-led product plan](docs/next-iteration/evidence-led-product-plan.md)
recommend validating the live editorial task, clarifying evidence and audience
previews, and testing catch-up over an explicit interval. These are researched
recommendations, not additional delivered features or proven user benefits.

The [synthetic-data research and source audit](docs/synthetic-data-research.md)
led to [SD01–SD08](docs/next-iteration/synthetic-data-plan.md). SD01–SD04 now add
the opt-in [development dataset](docs/synthetic-dataset-v1.md); held-out cases,
comparative AI evidence and composed four-minute demos remain later work.

Priorities reflect the five equally weighted judging categories; they are product
judgments, not predicted judging scores.

1. Validate the current flagship with football/Spanish reviewers and first-time
   viewers. Measure comprehension, producer approval/edit effort and time to a
   usable story; report observed results and failures. Pilot materials are
   prepared, but participant ratings and findings remain pending.
2. Demonstrate meaningful Director/Reviewer behavior with traceable evidence,
   bounded repair or rejection, and comparison against the existing single-agent
   and deterministic alternatives. Current discovery results do not establish
   multi-agent superiority.
3. Continue the SD plan with held-out inputs and fair current-workflow comparison;
   review the delivered development scenes with football participants. Preserve
   original sources and report failures. Ball/shot speed remains conditional on
   source coverage and independent validation.
4. Rehearse and record the under-two-minute functioning demo. Deploying the new
   mixed-event candidate and changing repository visibility remain separate
   owner-authorized release steps.

Chaos Index, calibrated Pass Escape Difficulty and tactical turning-point claims
remain deferred until their definitions and validation justify them. Additional
agent roles, Fabric services and speech are optional; they need a demonstrated
product benefit before adding cost or complexity.
