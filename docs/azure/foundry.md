# Microsoft Foundry and model deployment

**Status: specification only.** The application currently uses local deterministic templates; no model endpoint, credentials, SDK call or hosted workflow has been verified.

## Resources and configuration

Create a Foundry resource and project suitable for the selected model API, with one compatible model deployment shared by the three roles. A small structured-output-capable model is sufficient to begin; choose its exact model/version, deployment SKU, tokens-per-minute quota and region after verifying current availability and an acceptable budget. Do not assume the deployment name equals the model name.

The intended workflow runs in the Python API container. Agent Framework supplies typed orchestration; Foundry supplies model access. A Foundry hosted-agent runtime is not required and is not assumed compatible with an arbitrary Python workflow graph.

Required server configuration after selecting the API:

| Setting | Meaning |
|---|---|
| `WHY_NOW_MODEL_MODE` (future) | Explicit `template` / `foundry`; no silent cloud claim |
| `FOUNDRY_PROJECT_ENDPOINT` (future) | Endpoint from the selected project/API |
| `FOUNDRY_MODEL_DEPLOYMENT` (future) | Actual deployment name |
| Managed identity client ID | When selecting a user-assigned identity |
| API version, if required by the chosen client | Pin only after the selected SDK/API is tested |

These future configuration names are a design contract; the local API does not read them yet. Use managed identity and the minimum required project/model invocation permissions. Keep credentials server-side. Do not ship a model key to the web app.

## Workflow to implement after provisioning

- Analyst: read bounded sequence/positions/metrics, return a typed proposal containing evidence references and qualifications.
- Reviewer: use independent tools; supported / needs evidence / revise / reject; at most one additional evidence/revision cycle.
- Editor: transform reviewed facts into typed variants. Validate numbers, entities, units, claim references and required qualifications; one repair maximum.
- Total deadline, tool-call budget, token budget and concurrency semaphore are explicit. A timeout/malformed response/tool failure gives a labeled supported template fallback or abstention, never automatic publication.
- Approval remains an exact package/evidence revision/hash with producer identity. Models cannot approve or publish.

Test provider failure, prompt injection through external text, malformed structured output, timeouts and reviewer-driven changes. Measure actual usage/latency. Run a fair single-agent comparison with the same tools, model and disclosed budget before making collaboration-quality claims.

Official references: [Agent Framework workflow executors](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/advanced/agent-executor), [official Python workflow sample](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/agents/custom_agent_executors.py), [Microsoft Foundry documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/). SDK imports/package versions and endpoint semantics must be confirmed when this integration is implemented; no untested dependency is presented as complete.
