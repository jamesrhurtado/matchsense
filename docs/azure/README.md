# Azure resource specifications — planned only

No resources were created. These notes describe the target architecture in the technical handoff so that provisioning can happen later. Resource names are suggestions, not existing identifiers. Subscription, tenant, region, model deployment, quota and budget remain to be chosen/verified.

| Required resource | Suggested name | Purpose | Detail |
|---|---|---|---|
| Resource group | `rg-whynow-demo` | Own and clean up the demo resources together | All resources tagged `project=why-now`, `environment=demo`, `owner`, `expiry` |
| Foundry resource/project and model deployment | `whynow-foundry`, `whynow-project`, `story-model` | Structured model access for the bounded analyst/reviewer/editor workflow | [Foundry](foundry.md) |
| Event Hubs namespace/hub and checkpoint storage | `whynow-events`, `match-observations` | Match-partitioned observation transport | [Event Hubs](event-hubs.md) |
| Cosmos DB for NoSQL account/database/containers | `whynow-state`, `whynow` | Shared story state, exact revisions, approvals, audit and session snapshots | [Cosmos DB](cosmos-db.md) |
| Container Apps environment and two apps | `whynow-env`, `whynow-api`, `whynow-web` | One workflow/API host and the Next.js surfaces | [Hosting](container-apps.md) |
| Registry | `whynowregistry<unique>` | Store application images; alternatively use an existing authorized registry | [Hosting](container-apps.md) |
| Application Insights + Log Analytics | `whynow-insights`, `whynow-logs` | Correlated traces, failures, latency and usage | [Observability](observability.md) |
| Managed identities + Key Vault if secrets remain | `whynow-api-identity`, `whynow-vault` | Server credentials and narrow resource permissions | [Identity](identity.md) |

Use one region where the chosen model and required services are available. Verify capacity in the actual subscription before selecting it; this repository does not assert that any model/SKU/region is available. Budget estimates require actual region/SKU choices, expected tokens and demo uptime. There is no price quote or cost measurement for Azure in the local evaluation.

Provisioning order: group and identities → Foundry/model → Cosmos and Event Hubs/checkpoints → registry/observability → apps/configuration/RBAC → verification. Run end-to-end approval/retraction/reconnect and failure tests in the resulting environment before recording Azure claims.

Do not add Fabric, vector search, APIM/MCP, Service Bus, Speech or AKS for this MVP. The current prototype needs cloud adapters before it can use the proposed resources. Resource creation alone does not complete the integration.
