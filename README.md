# WHY/NOW

**Azure engineering build:** [Open WHY/NOW](https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io). See [QA access and testing](docs/qa.md) and [deployed Azure resources](docs/azure/README.md).

**See the play. Understand the moment.** An evidence-first story desk for a fictional football broadcast, with a producer console and a responsive viewer companion.

## Working local MVP

The local application implements synthetic replay → deterministic metrics → evidence replay → constrained wording review → exact-revision producer approval → timed shared overlay → English/Spanish companion variants and approved-moment recap.

Local mode uses **deterministic templates**, including the analyst/reviewer/editor stages. It does not call an AI model. The hosted environment adds Microsoft Agent Framework with Azure OpenAI, Event Hubs transport, Cosmos persistence and managed-identity access. The default local mode remains available for offline development. Actual resources are documented in [docs/azure](docs/azure/README.md).

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
# With API and production web server running:
npm --prefix apps/web exec -- playwright install chromium
npm --prefix apps/web run test:e2e
```

The browser tests cover the actual producer/viewer flow, Spanish and focus variants, review changes, retraction, phone layout, and streamed updates through the web proxy. See [evaluation results](evals/REPORT.md) for measured local processing and the exact scope of the synthetic evaluation. CI configuration is prepared in `.github/workflows/ci.yml`; it has not been run on GitHub.

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

Runtime exports contain only observations; seeds, fault plans, clean future trajectories and expected results are separate offline files. The application catalogue offers all 171 replays, including three-minute segments. Each pass has its own investigation, approval and recap entry; viewers can select approved history without changing the shared live overlay. All 168 constructed cases and 594 checkpoints pass with unchanged inputs and references. Synthetic results do not establish real football accuracy. The expanded suite also caught and now guards a distance-rounding defect.

## Repository map

| Directory | Purpose |
|---|---|
| `apps/web` | Next.js producer, companion and shared overlay routes |
| `services/api` | FastAPI, producer authorization, SSE, approval and recap APIs |
| `engine` | Contracts, time-scoped metrics, bounded template/Foundry workflows, SQLite/Cosmos repositories and Event Hubs transport |
| `simulator` | Seeded generator and independent structural/physical checks |
| `data/runtime` | Three runtime fixtures: metadata and JSON Lines observations |
| `data/schemas` | Versioned JSON Schemas exported from Pydantic contracts |
| `data/evaluation-only`, `evals` | Offline labels, split configurations and results; never exposed through runtime tools |
| `docs` | Architecture, metric definitions, demo guide, implementation status, Azure specifications |

## Delivery status and limits

The local and Azure implementations are available; see the QA guide for completed live checks and remaining test boundaries. Competition submission packaging remains pending. [Implementation status](docs/implementation-status.md) maps the handoff's acceptance phases to evidence and outstanding work. [Demo guide](docs/demo.md) describes what can honestly be shown now.

Local mode uses SQLite. Cloud mode uses Cosmos and Event Hubs, with one API worker/replica enforced for this engineering environment. It supports independent pass investigations across each segment, two fictional teams, 22 active players and 10 Hz observations. Runtime evidence is limited to the delivered clock. The underlying dataset is synthetic, with six authored parent configurations. Local tests do not establish real-match tactical accuracy, general semantic verification, production scale, or measured editorial savings.

No real match records, footage, team logos, viewer accounts or third-party TV synchronization are included. Cloud producer access uses a private key and request limits; enterprise multi-tenant authorization is future work. The repository and submission video have not been published.
