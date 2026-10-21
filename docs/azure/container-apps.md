# Container Apps hosting and registry

**Engineering implementation:** Implemented with Dockerfile.api, Dockerfile.web, runtime web proxy and infra/deploy_apps.py. API ingress is internal; web ingress is public HTTPS. Each app is bounded to one replica. Actual resources and QA status are in README.md and ../qa.md.

| Resource | Proposed initial configuration |
|---|---|
| Container Apps environment | One environment in the selected region, linked to the planned Log Analytics workspace |
| API/workflow app | Python 3.13, FastAPI/Uvicorn, port 8000; one initial replica/worker until the shared Cosmos/concurrency adapter is verified |
| Web app | Node.js 22+, Next.js production build/start, port 3000; public HTTPS ingress |
| API ingress | Prefer internal ingress with the web app proxying `/api`; verify long-lived streaming through the complete path |
| Registry | Existing authorized registry or one small ACR; managed identity pull permissions |
| Initial compute | Begin with small CPU/memory allocations supported by the chosen environment; measure model/workflow latency and memory before choosing limits |
| Scale | Keep one warm demo instance if needed for predictable response; set a bounded maximum after shared-state concurrency is validated |

The future runtime image must include only application code, schemas and `data/runtime`. Exclude `evals`, `data/evaluation-only`, provenance seeds, source vault paths, `.env`, SQLite files and test artifacts. The local repository retains those offline materials for reproducibility.

Configure server-side API URL, allowed origins, producer identity/authentication, model/persistence/Event Hubs endpoints and observability settings. Never use the public local demo key on an Internet-facing producer endpoint. Add request and stream limits before public judging access.

Streams must use `text/event-stream`, disabled buffering/compression, heartbeats and authoritative reconnect snapshots. Confirm actual ingress timeout behavior and reconnection under the chosen environment. Do not assume support for indefinite streams just from local success.

Health probes should use `/api/health` for liveness and a separate readiness check once actual external dependencies are integrated. Make model access failure a degraded/template mode rather than claiming successful AI execution. Keep revision-identifiable images for demo reproducibility and rollback.

Use one workflow execution host; do not deploy a second hosted-agent runtime unless the actual selected SDK/workflow requires and verifies it. [Container Apps ingress documentation](https://learn.microsoft.com/en-us/azure/container-apps/ingress-overview), [environment ingress settings](https://learn.microsoft.com/en-us/azure/container-apps/ingress-environment-configuration?tabs=azure-cli).
