# Implementation status

## Engineering implementation

| Handoff phase | Status | Evidence |
|---|---|---|
| 0: Inspect and decide | Complete | Five Obsidian notes and attached concept brief read; empty project inspected; Git initialized |
| 1: Data foundation | Complete for local MVP; expanded test corpus implemented | Versioned Pydantic/JSON contracts, three hosted fixtures, 168 reproducible offline cases across 28 families and six parents, 22-player coverage, clean/observed/reference separation and independent physical/temporal validation |
| 2: Deterministic visual slice | Complete | Three metrics, time controls, negative-case abstention, live SVG pitch, independent historical evidence replay |
| 3: Publication path | Complete for local MVP | Protected controls, immutable packages, exact revision/hash approvals, edit/review, suppression/retraction, expiry, SSE companion, 100 prevalidated variants, recap, SQLite restart safety |
| 4: Foundry and Agent Framework | Implemented | Actual Agent Framework analyst/reviewer/editor calls, typed decisions, bounded evidence requests, composed factual variants, usage/spans and explicit fallback; public API/browser tests and restart durability passed; evidence is in docs/qa.md |
| 5: Evaluation and hardening | Partial | Backend/browser gates, cloud persistence/transport tests, historical 24-segment evaluation and expanded 168-case regression with authored checkpoints; fair model comparison, football expert review, human comprehension and production load tests remain pending |
| 6: Azure and submission | Azure deployed; submission packaging pending | Dedicated resources and public engineering endpoint provisioned; private producer access configured. Public repository and final video remain pending |

## Implemented contract choices

The endpoint names follow the technical handoff, with these MVP choices:

- Story edits accept proposed wording. Local mode restores the canonical template for unverified changes; cloud mode uses a separate reviewer context that can accept, revise, request evidence or reject. The producer retains publication control.
- Viewers receive authoritative snapshot/SSE state. Browser event history and stored recap jobs are deferred. Cloud ingestion has Blob checkpoints and durable Cosmos observations. Fresh recap generation is bounded and deterministic; no asynchronous model job or polling endpoint is needed in this mode.
- Only a currently approved story is viewer-visible; an expired approved moment remains in the companion/archive and recap, while the shared overlay disappears. Retraction and edits remove the current approval.
- One API worker is required. Local state uses SQLite; cloud state uses session-partitioned Cosmos transactions and ETags. One cloud replica is enforced and broad distributed production readiness is not claimed.
- The hosted prototype uses a private producer key, bounded requests and separate managed identities. Viewer requests have no Azure credentials. Enterprise producer user onboarding remains future work.

## Work still required for the full submission

1. Complete independent engineering QA using the public environment and document findings.
2. Run fair template/single-agent/workflow comparisons on fresh held-out scenario families. The existing evaluation is a narrow deterministic synthetic test.
3. Conduct user comprehension/editorial timing tests and production load/recovery exercises appropriate to an actual broadcaster.
4. Implement multiple-pass investigation/ranking and substantive player personalization; the expanded synthetic cases already expose these scope gaps. Add fresh unseen parents after tuning before claiming full-match applicability.
5. Publish the repository and record the final sub-two-minute submission demo when requested.

The hosted build is an engineering MVP. This does not certify production deployment, comprehensive AI factual accuracy, a winning judging score, or a completed competition submission. See [QA record](qa.md) for actually completed deployed checks.
