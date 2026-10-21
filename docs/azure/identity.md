# Identity, producer access and secrets

**Engineering implementation:** Implemented using separate API and web managed identities. The web identity has image-pull permission only. Producer testing uses a private Container Apps secret; production Entra user onboarding remains future work. See README.md.

Use a managed identity for the API/workflow host and narrow resource roles for model invocation, Event Hubs receive, Cosmos data access, checkpoint storage and telemetry as actually needed. Grant the replay publisher sender permissions separately. Give the web app only API connectivity and image pull permissions; viewer browsers need no Azure credentials.

Use Entra-authenticated producer identity or a private prototype producer key for the first shared judging build. Keep the producer role independent of viewer language/detail/focus. A viewer URL is read-only and cannot create, reset, edit, approve, suppress or retract. Log the actual producer identity with the exact package hash when cloud authentication is integrated; the local audit identifies its single operator as the local producer.

If remaining service secrets are necessary, use a Key Vault and Container Apps secret references with the managed identity. Do not add Key Vault solely to hold values that can use managed identity directly. Give operators time-limited access and define a documented rotation/expiry procedure for any judging access key. Configure minimum necessary origins and request/rate limits before public exposure.

Current local variables are described in `.env.example`. Planned service variables are not active code until their adapters are implemented. Do not place secrets in Markdown, version control, screenshots, exported traces or the browser bundle.

Official references: [Container Apps managed identity](https://learn.microsoft.com/en-us/azure/container-apps/managed-identity), [Container Apps secrets](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets).
