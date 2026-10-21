# Microsoft Foundry and model deployment

**Engineering implementation:** Implemented in engine/foundry_workflow.py. Dedicated Foundry/model resources are provisioned; real model calls have been exercised. See README.md and ../qa.md for deployment and live verification status.

## Resources and configuration

Create a Foundry resource and project suitable for the selected model API, with one compatible model deployment shared by the workflow roles. A small structured-output-capable model is sufficient to begin; choose its exact model/version, deployment SKU, tokens-per-minute quota and region after verifying current availability and an acceptable budget. Do not assume the deployment name equals the model name.

The intended workflow runs in the Python API container. Agent Framework supplies typed orchestration; Foundry supplies model access. A Foundry hosted-agent runtime is not required and is not assumed compatible with an arbitrary Python workflow graph.

Required server configuration after selecting the API:

| Setting | Meaning |
|---|---|
| `WHY_NOW_MODEL_MODE` | Explicit `template` / `foundry`; no silent cloud claim |
| `AZURE_OPENAI_ENDPOINT` | Actual account model endpoint used by the Agent Framework client |
| `FOUNDRY_PROJECT_ENDPOINT` | Project context endpoint; model calls use the account deployment endpoint |
| `FOUNDRY_MODEL_DEPLOYMENT` | Actual deployment name |
| Managed identity client ID | When selecting a user-assigned identity |
| API version, if required by the chosen client | Pin only after the selected SDK/API is tested |

Cloud configuration is read by the deployed adapter; local mode still uses SQLite and templates. Use managed identity and the minimum required project/model invocation permissions. Keep credentials server-side. Do not ship a model key to the web app.

## Implemented workflow design

Version 0.4 defaults to the scoped version 2 narrative workflow: Story Director selects claim blocks, the application renders exact bilingual variants, and Claim Reviewer checks final content with per-claim verdicts. Normal execution uses two model calls; evidence continuation and one repair/re-review share a six-call, twelve-tool, 15-second ceiling. The same model deployment and managed identity are reused. Legacy packages remain readable, with explicit version 1 generation available through `WHY_NOW_NARRATIVE_VERSION=1`.

Every attempt is recorded separately from its publication package. This includes abstentions, rejections, failures and incomplete usage; unknown consumption is not zero cost. Outcome timestamps distinguish scheduling/start/completion. Exact ingestion-to-display timing and comparative agent usefulness still require the planned measurements.

The following describes the retained version 1 path:

- Analyst: read bounded sequence/positions/metrics, return a typed proposal containing evidence references and qualifications.
- Reviewer: use independent tools; supported / needs evidence / revise / reject; at most one additional evidence/revision cycle.
- Editor: generate four short number-free audience introductions. The application appends authoritative measurements and geometric caveats, then validates the complete variants. A final reviewer sees the composed text. One introduction repair is allowed; models never retype the measurements.
- Total deadline, tool-call budget, token budget and concurrency semaphore are explicit. A timeout/malformed response/tool failure gives a labeled supported template fallback or abstention, never automatic publication.
- Approval remains an exact package/evidence revision/hash with producer identity. Models cannot approve or publish.

Test provider failure, prompt injection through external text, malformed structured output, timeouts and reviewer-driven changes. Measure actual usage/latency. Run a fair single-agent comparison with the same tools, model and disclosed budget before making collaboration-quality claims.

Official references: [Agent Framework workflow executors](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/advanced/agent-executor), [official Python workflow sample](https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/agents/custom_agent_executors.py), [Microsoft Foundry documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/). SDK imports/package versions and endpoint semantics must be confirmed when this integration is implemented; no untested dependency is presented as complete.

## Verified implementation configuration

The engineering deployment uses GPT-4o mini GlobalStandard through `story-model`, API version `2024-10-21`, Agent Framework core `1.22.0` and OpenAI provider `1.17.0`. `WHY_NOW_MODEL_MODE=foundry` selects the adapter; `WHY_NOW_AZURE_ENVIRONMENT=production` selects managed identity. `AZURE_CLIENT_ID` identifies the API identity. Offline mode uses local templates; local model development can use DefaultAzureCredential.

Version 2 limits are 15 seconds, two simultaneous model workflows, six model calls, twelve read-only tool requests and a conservative token budget of 32,000. The explicitly selected legacy version 1 path retains its 25-second/eight-call limits. The API schedules at most four outstanding jobs. These are application bounds, not a hard Azure invoice cap. Provider usage remains explicit even when validation causes fallback.
