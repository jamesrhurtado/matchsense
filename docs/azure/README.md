# Azure engineering environment

Provisioned on 20 October 2026 in the selected Visual Studio Enterprise Subscription. Resource group: `rg-whynow-demo`. Public application: https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io . Live QA results and remaining gates are recorded in [QA guide](../qa.md). The 21 October update reuses the same environment: Azure lists 14 resources, including the Foundry project and an automatically created failure-anomaly alert. No additional Azure services were provisioned for the expanded replay release.

| Resource | Deployed configuration | Application use |
|---|---|---|
| Foundry | `whynow-foundry-jh1020`, project `whynow-project`, East US | Managed-identity model invocation from API |
| Model | `story-model`: GPT-4o mini `2024-07-18`, GlobalStandard, capacity 50 | Version 2 Story Director and Claim Reviewer; bounded evidence/repair |
| Cosmos DB | `whynow-state-jh1020`, serverless, East US 2 | `whynow` database; `session-state`, `story-state`, `observations`, all partitioned by `/session_id` |
| Event Hubs | `whynow-events-jh1020`, Standard, 1 throughput unit | `match-observations`, 2 partitions, 1 day retention; `whynow-state` consumer group |
| Checkpoints | `whynowcheckpointsjh1020`, Standard LRS | Private `eventhub-checkpoints` Blob container |
| Container Apps | `whynow-env`, East US, Consumption | Public web and internal API, one replica each |
| API | `whynow-api`, 1 CPU / 2 GiB | FastAPI v0.5.0, Agent Framework investigations, producer agents, ingestion and per-story publication |
| Web | `whynow-web`, 0.5 CPU / 1 GiB | Next.js production server and runtime streaming proxy |
| Registry | `whynowregistryjh1020`, Basic | Revisioned Linux amd64 images, managed-identity pulls |
| Monitoring | `whynow-logs` and `whynow-insights` | Workspace-linked Application Insights, 30-day retention, workspace daily ingestion quota 0.2 GB |
| Identities | `whynow-api-identity`, `whynow-web-identity` | API data/model roles; web identity only image pull |

East US rejected Cosmos account creation because of regional capacity. The failed empty account was removed and recreated in East US 2. Other resources remain in East US; account for that cross-region hop when assessing latency.

Service authentication uses managed identities. Cosmos, Foundry and Event Hubs local-key authentication are disabled; Storage shared-key access is disabled. The prototype producer uses a private access key held as a Container Apps secret. The local access handoff is `.azure/qa-access.json`, owner-readable, Git-ignored and excluded from image uploads. No service key or producer credential is in the browser bundle or documentation.

The environment is for engineering tests: one API worker/replica, bounded model concurrency, request limits, public read-only viewer URLs, and private producer mutations. Horizontal scaling and production identity onboarding are not certified. No AI Search, AKS, Fabric, APIM or hosted-agent service was provisioned.

## Reproduce and update

Use the current authenticated Azure CLI. Scripts read the selected subscription, so verify it before provisioning. Defaults are in `infra/provision.py`; edit them for a separate environment. The scripts provision resources directly with Azure Resource Manager/CLI, rather than introducing a second hosted-agent deployment lifecycle.

1. `python3 infra/provision.py`
2. `python3 infra/configure.py`
3. Build images using `az acr build --registry whynowregistryjh1020 --image whynow-api:<new-tag> --file Dockerfile.api --platform linux/amd64 .` and the corresponding `Dockerfile.web` / `whynow-web:<new-tag>`.
4. `WHY_NOW_IMAGE_TAG=<api-tag> WHY_NOW_WEB_IMAGE_TAG=<web-tag> python3 infra/deploy_apps.py`
5. `.venv313/bin/python scripts/cloud_smoke.py`

Use new image/revision tags for every change. Check Container Apps revision health and the public `/api/ready` response after a rollout. `/healthz` tests the web process independently; API readiness checks persistence and transport errors. The web proxies `/api` to the internal API URL at runtime, including SSE.

## Costs and cleanup

These resources now incur charges. Event Hubs Standard and the registry have baseline charges; containers, Cosmos, logs, Storage and model calls add usage. The earlier $75–150/month figure was a planning allowance, not a measured bill or spending cap. Check actual Cost Management costs grouped by `rg-whynow-demo` after billing catches up.

Resources carry `project=why-now`, `environment=demo` and an expiry tag of `2026-11-20` where supported. The expiry tag does not delete anything automatically. Delete the dedicated resource group only after preserving required QA evidence and receiving a cleanup instruction; doing so removes the database, observations, images and telemetry for this environment.

The deployed verification record is in [QA guide](../qa.md). The current API is `cloud-v20` and the web is `cloud-v10`, built from base commit `5eb555e` plus the documented working-tree release changes. The deployment reuses the same 14 resources. Earlier tags remain historical QA evidence.

Verified image digests:

- API: `sha256:8dd08db53aabd69acbfd5873b4ff3675c445095027bd8263743d83f69bf67a65`
- Web: `sha256:6b50b4840574627cf52ed962267fe2a3f48852a2ef45200e7f3f4055a513a28a`

The Azure API is configured for the YouTube OAuth callback at the public web
origin. Its client secret is held as a Container Apps secret and is not stored in
this repository. OAuth setup is not proof of a successful read from an active
YouTube Live chat; see the [current QA record](../qa.md) for the tested boundary.

Per-service specifications below retain the design rationale and now identify implemented behavior: [Foundry](foundry.md), [Cosmos](cosmos-db.md), [transport](event-hubs.md), [hosting](container-apps.md), [identity](identity.md), [observability](observability.md).
