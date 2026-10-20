# Application Insights and Log Analytics

**Status: specification only.** The local trace panel reports measured deterministic stage timings and SQLite audit events. No Application Insights workspace, Azure trace link, model token usage or cloud cost has been verified.

Create one Application Insights component and Log Analytics workspace, linked to the Container Apps environment as appropriate. Add OpenTelemetry instrumentation using the current supported Azure/Foundry SDK integration after choosing actual model/workflow clients.

Correlate match ID, replay session/generation, source message revision, evidence/story revision, workflow run, approval/publication ID and trace ID. Record replay waiting separately from metric processing, model latency, network delivery and human approval. A 1 ms local template calculation is not end-to-end live AI latency.

Required spans: release/ingestion → validation/state → metrics → analyst/tool calls → reviewer/targeted check → editor/variant validation → producer decision → publish/expire/retract → companion delivery/recap. Record bounded retry/fallback/abstention reasons and actual model token/cost usage when supported.

Do not export secrets, producer keys, authentication headers, unrestricted prompts or future/hidden-label data. Define retention, sampling and a budget cap appropriate to the demo; preserve approval and failure evidence even when high-frequency tracking spans are sampled. Add actionable alerts for sustained workflow failure, consumer lag, stream delivery failure and unexpected spend once thresholds are measured.

Official reference: [Application Insights OpenTelemetry guidance](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-overview). Exact instrumentation package versions and Foundry trace compatibility remain to be verified in the real integration.
