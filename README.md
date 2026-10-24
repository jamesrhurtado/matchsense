# WHY/NOW

**Azure engineering build:** [Open WHY/NOW](https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io). See [QA access and testing](docs/qa.md) and [deployed Azure resources](docs/azure/README.md).

**Source:** [jamesrhurtado/why-now](https://github.com/jamesrhurtado/why-now), currently private at the owner's request. Original project source is licensed under [MIT](LICENSE).

**See the play. Understand the moment.** An evidence-first story desk for a fictional football broadcast, with a producer console and a responsive viewer companion.

## Broader match coverage — local engineering candidate

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
and use the prefilled local producer key. The command enables
`WHY_NOW_MATCH_COVERAGE=1` and isolates SQLite in `.run/match-coverage.db`.
Coverage is off in ordinary `make dev`; the six additional fixtures have a separate
catalogue. The guided demo uses continuous authored player/ball movement and keeper lanes,
and pauses at the first example of each event type so you can inspect and approve
it. Pressure Swing pauses at the comparative 30 m pass, around 91.3 s. Turn off **Pause at new event types** for continuous playback. **Check the evidence**
opens the supporting facts and brings them into view. Observation counts are
position samples/source records, not football incident counts. The original mixed
fixtures and stored approvals remain unchanged. No Azure credentials or paid calls
are needed. See the
[mixed-event walkthrough](docs/match-coverage-demo.md),
[event definitions/rollback matrix](docs/match-events.md),
[verification record](docs/next-iteration/match-coverage-handoff.md) and
[pilot materials](docs/match-coverage-pilot.md).

The new **Pressure Swing** insight compares time-weighted nearby-opponent averages
before a pass and after reception, with explicit intervals and coverage. The new
flagship demonstrates **2.0 → 0.4** around a **30 m forward pass**, plus a scoped
comparison against three previous team passes. “Why this moment?” is separate
from factual evidence; casual/analyst and relevant player views share approved
facts. This is a proximity proxy, not tactical intent, pass difficulty or a cause
of the later goal. See [the flagship walkthrough and rubric rationale](docs/pressure-flagship.md).

This is a local engineering candidate. Recruitment, external football/Spanish
ratings, real-user findings and deployment remain pending. A bounded real
**gpt-4o-mini 2024-07-18** smoke now verifies pressure, shot, goal, recovery and
possession through Director/Reviewer (10 calls, exact source-rendered bilingual
text). It does not establish broad model quality or user usefulness. The hosted
0.5 build remains separate and has not been updated.

## Working local MVP

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
| `data/runtime` | 173 observation-only runtime fixtures: metadata and JSON Lines/gzip observations |
| `data/schemas` | Versioned JSON Schemas exported from Pydantic contracts |
| `data/evaluation-only`, `evals` | Offline labels, split configurations and results; never exposed through runtime tools |
| `docs` | Architecture, metric definitions, demo guide, implementation status, Azure specifications |

## Delivery status and limits

The local and Azure implementations are available; see the QA guide for completed live checks and remaining test boundaries. Competition submission packaging remains pending. [Implementation status](docs/implementation-status.md) maps the handoff's acceptance phases to evidence and outstanding work. [Demo guide](docs/demo.md) describes what can honestly be shown now.

The [PM update handoff](docs/next-iteration/pm-update-handoff.md) summarizes the contextual update, verification, ordered implementation commits and remaining release gates.

The [broader match implementation plan](docs/next-iteration/match-coverage-implementation-plan.md) governs this iteration. The [90+ product improvement plan](docs/next-iteration/grand-prize-90-plus-plan.md) is historical context, based on version 0.4. It specifies changes by judging category, agent/context contracts, priorities, dependencies, acceptance tests and evaluation gates, excluding submission logistics. The [implementation record](docs/next-iteration/decision-log.md) identifies delivered changes and outstanding evidence; the [earlier plan](docs/next-iteration/README.md) remains available as historical context.

Local mode uses SQLite. Cloud mode uses Cosmos and Event Hubs, with one API worker/replica enforced for this engineering environment. It supports independent pass investigations across each segment, two fictional teams, 22 active players and 10 Hz observations. Runtime evidence is limited to the delivered clock. The underlying dataset is synthetic, with six authored parent configurations. Local tests do not establish real-match tactical accuracy, general semantic verification, production scale, or measured editorial savings.

No real match records, footage, team logos, viewer accounts or third-party TV synchronization are included. Cloud producer access uses a private key and request limits; enterprise multi-tenant authorization is future work. The repository and submission video have not been published.
