# WHY/NOW quality iteration: implementation and evidence handoff

22 October 2026 (America/Lima). Local candidate: application 0.5.0, package schema 4.0.0, renderer `editorial-claims-v4`, latest prompt `director-critic-v4.1`. Scope is MVP quality and agent effectiveness. No new Azure resources or application rollout were performed.

## Delivered changes

| Review finding | Applied change | Practical limit |
|---|---|---|
| Excess precision and repeated facts | New v4 realization uses one decimal; context replaces redundant forward-distance text; reception/location share one clause | Raw source values and comparisons remain unrounded; v1/v2/v3 approved text remains immutable |
| Trivial historical differences receive strong prominence | Versioned provisional recommendation requires ≥3 m and ≥20% gap to largest prior distance (absolute-only near zero) | An editorial hypothesis awaiting football review; supported manual emphasis remains available |
| Comparison title is ambiguous | Title explicitly refers to forward displacement and the previous three passes | No implied tactical superiority |
| Current and earlier moments compete visually | Earlier-moment banner and Return to live clear personal selection/focus and focus the shared panel | Does not mutate replay or another viewer's overlay |
| Exact table is hard to interpret | Signed comparison bars, highlighted current pass, timestamps and rounded values; expandable exact source table | Missing observations remain missing; no invented movement |
| Inconsistent Spanish evidence states | Viewer/evidence labels, clock/status/navigation and comparison presentation translated | Producer interface is still primarily English; independent Spanish semantic review pending |
| Crash between package storage and accepted disposition | Package and lifecycle acceptance events share SQLite transaction/Cosmos batch; exact retries and historical recovery are idempotent | Complete durable-readiness timing, dependency indexing and broader operating-envelope work remain open |
| Agent benefit unmeasured | Matched T3/S3/M3 + D3 reviewer ablation, complete opportunity denominators, actual model runs, blank blind ratings | Discovery only; no human usefulness or multi-agent superiority claim |
| Observed model plan omitted a required fact | Shared one-repair validator feedback path within existing call/deadline/token limits | Original fallback preserved; post-fix check is a targeted regression, not a final comparison |

## Real model results

See [full discovery evidence](../../evals/agentic/discovery-v4/README.md) and [research/architecture decision](multi-agent-evidence.md).

The frozen comparison has 60 outcomes over 15 cases: 14 eligible opportunities plus one quiet case in each arm. T3, M3 and D3 delivered all expected packages; S3 delivered 13 model-selected packages plus one factual fallback. All withheld the quiet case. All broad angle choices matched, and no reviewer-requested repair occurred.

This does not demonstrate that two agents perform better than a strong single agent or deterministic selection. Candidate collaboration remains available; architecture selection is provisional pending blind usefulness/acceptance review. Do not claim category advantage from role count, one stochastic fallback, or different median latency.

The three actual runs together used 89 model calls and an estimated $0.0491799 at verified public rates, with complete reported usage. Existing infrastructure cost is separate. No model grader or fabricated user score was substituted for the missing human ratings.

## Verification

- Backend gate: 325 tests passed, including both-arm repair and immutable version compatibility.
- Local browser gate: 17 passed, two hosted checks intentionally excluded; current production frontend build and TypeScript passed.
- Scoped frontend formatting passed.
- Original regression: 168 cases, 594 checkpoints and 72 distinct moments, baseline unchanged; zero model calls.
- Version 4 JSON Schema validates a real contextual package; archived schemas unchanged.
- Visual inspection covered the mobile signed-comparison/tie case and current contextual desktop/mobile views.
- Local `/api/health` and `/api/ready` return healthy version 0.5.0/schema generation 4; SQLite/local transport. This is not a deployed-resource or production load certification.

## Reviewer handoff

James confirmed he can arrange football reviewers and producer/viewer testers. Use [the guide](reviewer-guide-v4.md) and `.run/agentic-v4-live-comparison/rating-packets.json` plus `rating-instrument.csv`. Keep `rating-mapping-private.json`, arm reports and results away from raters. Preserve empty ratings until the sessions occur. Review Spanish semantics as well as English.

The original model comparison used prompt v4.0; the latest code uses v4.1 after the observed invalid-plan fix. Keep these identities in reporting. Review the preserved blind packets as discovery material and use a fresh independent set for a final architecture decision after tuning.

## Remaining work that affects the 90+ case

1. Football/producer/viewer feedback on comparison usefulness, clarity, mistaken tactical implications and acceptable review effort.
2. Independent structural parents and a sealed final assessment, rather than counting shared-backbone variants as independent scenes.
3. Context/reviewer ablations answering a specific observed quality problem; current discovery shows no added reviewer benefit.
4. Exact durable-evidence readiness and browser clock uncertainty; 20 varied continuous opportunities, one/two-stream measurements and failure recovery.
5. Persistent historical reverse-dependency index/retention, lock profiling and an independent declared-unit incoming-feed adapter test.

The prior 84/100 was a subjective review; this handoff does not automatically raise it to 90+. It records implemented fixes and actual evidence so the next reassessment can be based on measured usefulness and working behavior.
