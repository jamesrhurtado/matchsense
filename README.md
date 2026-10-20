# WHY/NOW

**See the play. Understand the moment.** An evidence-first story desk for a fictional football broadcast, with a producer console and a responsive viewer companion.

## Working local MVP

The local application implements synthetic replay → deterministic metrics → evidence replay → constrained wording review → exact-revision producer approval → timed shared overlay → English/Spanish companion variants and approved-moment recap.

Local mode uses **deterministic templates**, including the analyst/reviewer/editor stages. It does not call an AI model. Microsoft Foundry/Agent Framework execution, Event Hubs, Cosmos DB and Azure deployment are the next integration phase. Azure resource requirements are documented in [docs/azure](docs/azure/README.md); **no Azure resources have been created**.

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
make web-build
# With API and production web server running:
npm --prefix apps/web exec -- playwright install chromium
npm --prefix apps/web run test:e2e
```

The browser tests cover the actual producer/viewer flow, Spanish and focus variants, review changes, retraction, phone layout, and streamed updates through the web proxy. See [evaluation results](evals/REPORT.md) for measured local processing and the exact scope of the synthetic evaluation. CI configuration is prepared in `.github/workflows/ci.yml`; it has not been run on GitHub.

## Repository map

| Directory | Purpose |
|---|---|
| `apps/web` | Next.js producer, companion and shared overlay routes |
| `services/api` | FastAPI, producer authorization, SSE, approval and recap APIs |
| `engine` | Contracts, time-scoped metrics, bounded local workflow and SQLite repository |
| `simulator` | Seeded generator and independent structural/physical checks |
| `data/runtime` | Three runtime fixtures: metadata and JSON Lines observations |
| `data/schemas` | Versioned JSON Schemas exported from Pydantic contracts |
| `data/evaluation-only`, `evals` | Offline labels, split configurations and results; never exposed through runtime tools |
| `docs` | Architecture, metric definitions, demo guide, implementation status, Azure specifications |

## Delivery status and limits

The local MVP is usable and tested. The complete Azure/model-backed submission remains pending. [Implementation status](docs/implementation-status.md) maps the handoff's acceptance phases to evidence and outstanding work. [Demo guide](docs/demo.md) describes what can honestly be shown now.

This is a single-host prototype with SQLite and one API worker. It supports one pass candidate per segment, two fictional teams, 22 active players and 10 Hz observations. Runtime evidence is limited to the delivered clock, but the underlying dataset is synthetic and deliberately small. Local tests do not establish real-match tactical accuracy, general semantic verification, production scale, or measured editorial savings.

No real match records, footage, team logos, viewer accounts, third-party TV synchronization, cloud deployments or paid inference are included. The current local API has no Internet-facing rate limiting or multi-tenant authorization. The public repository, judging URL and submission video have not been published.
