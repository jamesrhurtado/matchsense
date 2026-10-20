# Implementation status

## Verified local MVP

| Handoff phase | Status | Evidence |
|---|---|---|
| 0: Inspect and decide | Complete | Five Obsidian notes and attached concept brief read; empty project inspected; Git initialized |
| 1: Data foundation | Complete for local MVP | Versioned Pydantic/JSON contracts, three seeded 60 s fixtures, 22-player coverage, independent physical/temporal validation |
| 2: Deterministic visual slice | Complete | Three metrics, time controls, negative-case abstention, live SVG pitch, independent historical evidence replay |
| 3: Publication path | Complete for local MVP | Protected controls, immutable packages, exact revision/hash approvals, edit/review, suppression/retraction, expiry, SSE companion, 100 prevalidated variants, recap, SQLite restart safety |
| 4: Foundry and Agent Framework | Pending | Local role workflow is deterministic and explicitly labeled; model access and framework host must be integrated and tested after resources exist |
| 5: Evaluation and hardening | Partial | Automated backend/browser gates and 24 synthetic-segment evaluation; fair single-agent/model comparison, human comprehension tests and cloud failure tests remain pending |
| 6: Azure and submission | Pending by request | Markdown resource specifications prepared; no resources, public repository, public judging endpoint or video created |

## Implemented contract choices

The endpoint names follow the technical handoff, with these MVP choices:

- Story edits accept a proposed sentence. The constrained local reviewer restores the validated template if it cannot verify that exact wording. The result displays the producer's proposed wording and the actual review outcome. This is a real producer-edit branch, not an injected model error.
- Viewers receive authoritative snapshot/SSE state. Durable stream history, distributed checkpoint recovery and stored recap jobs are deferred. Fresh recap generation is bounded and deterministic; no asynchronous model job or polling endpoint is needed in this mode.
- Only a currently approved story is viewer-visible; an expired approved moment remains in the companion/archive and recap, while the shared overlay disappears. Retraction and edits remove the current approval.
- One API worker and SQLite are required locally. Thread locking and transactions protect the single-host path; this does not establish distributed production readiness.
- A simple producer key provides real API authorization for the prototype. Internet hosting needs a private key, request limits and cloud identity controls before judging access is offered.

## Work still required for the full submission

1. Create the documented Azure resources later, after region/model/cost decisions.
2. Implement the chosen Microsoft Agent Framework workflow host with Foundry structured responses and independent tools. Add deadline, malformed-output and provider-failure tests against the actual adapter. Preserve the local template fallback and producer gate.
3. Implement Event Hubs and Cosmos adapters with checkpointing, transactional revision checks and shared-worker concurrency. Connect real tracing and measured model usage.
4. Run fair template/single-agent/workflow comparisons on fresh held-out configurations, and verify failure/recovery behavior in Azure.
5. Publish the repository and judging build when authorized, record an honest sub-two-minute demo, and check the actual current contest rules before submission.

The local MVP is not the completed Azure submission. The current build can be demonstrated without credentials or paid resources.
