# Multi-agent effectiveness: research and product decision

Prepared 22 October 2026; latest bounded follow-up 27 October 2026 (America/Lima). Scope: local MVP quality and agent behavior; no deployment or submission logistics.

## What the category requires

The [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) emphasize distinct responsibilities, coordinated handoffs, recovery, and effectiveness relative to a single agent. A larger role count or more tool calls is not evidence of effectiveness.

[Microsoft's orchestration guidance](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) recommends choosing the least complexity that reliably meets the task because coordination introduces cost, latency and failure modes. [Anthropic's research-system account](https://www.anthropic.com/engineering/multi-agent-research-system) describes benefits on tasks with independent investigative directions and emphasizes outcome evaluation and human checks. Its reported research-task gains cannot be transferred to MatchSense.

## Applied design

The Director chooses a useful supported angle and claim order. The Claim Reviewer checks the rendered proposal against canonical facts and can request a repair, reject, or ask for bounded evidence. A deterministic renderer validates the final clauses. Producer approval remains authoritative.

The v4 update makes the choices more concrete: a tiny true historical difference does not automatically lead the story; reception is expressed once with its location; titles identify the exact comparison; raw values remain separate from rounded presentation. A provisional editorial policy recommends historical emphasis only if the distance exceeds the largest comparator by at least 3 m and by 20% of its absolute value (the relative test is omitted when the comparator magnitude is below 1 m). This is an explicit product hypothesis awaiting football review, not a calibrated tactical metric. Producers and agents may still select a supported smaller comparison; rounded ties are qualified.

## Fair experiment

| Arm | Behavior | Question |
|---|---|---|
| T3 | Deterministic editorial selection and v4 renderer | Does model selection add useful content? |
| S3 | Strong single agent with meaningful self-check/repair | Is one agent sufficient? |
| M3 | Director plus Reviewer with separate review context | Does specialized review improve the outcome? |
| D3 | Director without model review, evaluation-only | What does the Reviewer add beyond deterministic validation? |

All model arms use GPT-4o mini `2024-07-18`, the same allowed observations and tools, v4 renderer, and the same six-call/32,000 conservative-token/15-second workflow ceiling. D3 is enabled only with an explicit evaluation flag and is never selected by the application. Same-model roles are not statistically independent.

The runner randomizes execution order, retains every expected opportunity, validates handwritten context references after generation, and reports all failures, fallback, rejection and incomplete usage. It retains every outcome in the result log. A package returned after a repair is not automatically counted as a correct repair.

The discovery cases are developer-visible and share existing trajectory backbones. Repeated trials and variants are not independent football scenes. Mechanical checks establish contract/reference behavior; they do not establish editorial usefulness or comprehension.

## Decision rules

1. Review paired T3/S3/M3 outputs blind with football and producer reviewers. Compare useful supported acceptance, substantive edits, missed opportunities, wrong rejection, calls, estimated cost and latency.
2. Inspect D3 versus M3 to identify actual reviewer contributions. Label injected challenges; do not present them as spontaneous model mistakes.
3. Keep an independent reviewer only if its benefit or risk reduction justifies its measured overhead. A practical initial selection threshold is a descriptive 10 percentage point gain in accepted opportunities or 20% less substantive editing without a severe correctness regression, alongside timing targets. Small samples may remain inconclusive.
4. If S3 or T3 meets the task more effectively, choose it and state the result. Do not manufacture complex tasks or add roles to force a favorable category claim.
5. Expand to independently authored discovery/final scenes before claiming generalization. QA holds final expectations outside runtime access; human review is required for football usefulness and Spanish semantics.

## Reproduction and evidence

`python -m evals.agentic.run` is zero-model by default. `scripts/run_agent_discovery.py --stage smoke|comparison --output <new-directory>` explicitly enables existing-model calls, verifies the current text-model deployment and public retail rates, writes the bounded configuration and refuses to overwrite an existing run directory. It creates no Azure resources.

Raw runs and full traces are local under `.run/agentic-v4-live-smoke`, `.run/agentic-v4-live-comparison`, and the latest run path recorded below. Public summaries and exact manifests belong in `evals/agentic/discovery-v4`. The smoke and comparison ceilings are $0.50 and $1.50 respectively; reported costs are estimates from verified rates, not an invoice. Remaining reservations are retained when usage is unknown. No human-rating packets were used in the bounded follow-up below.

Reviewer recruitment: James confirmed on 22 October that he can arrange football reviewers and producer/viewer testers. No completed sessions or ratings are implied. Use the [reviewer guide](reviewer-guide-v4.md) for the next step.

## Previous v4.0 discovery conclusion

The [preserved comparison](../../evals/agentic/discovery-v4/README.md) completed 60 outcomes across 15 correlated discovery cases, with 69 actual model calls and complete usage. It is a historical v4.0 run, not the latest evaluation.

## Bounded v4.1 follow-up — 27 October 2026

The latest run is stored locally at `.run/agentic-matchsense-evidence-20261027-1445`; raw model traces remain in the ignored `.run` directory. The benchmark used GPT-4o mini `2024-07-18`, the same evidence, deterministic renderer, and per-workflow call/token/deadline caps for S3 and M3. Job order was interleaved and serial. Four arms ran once on each of 15 cases: T3 deterministic renderer, S3 strong single agent with self-check, M3 Director + Reviewer, and D3 Director without model review (evaluation-only). The 15 cases comprise four generated challenge cases sharing a trajectory generator and 11 history variants of one existing replay. They are discovery cases, not 15 independent matches.

The evaluator was strengthened with deterministic checks for runtime contract, cutoff, whether every claim source was visible to the workflow, reference actor attribution, team-retention versus individual-control attribution, complete language/detail/focus variant coverage, and reference context status/relation/comparator identities. Missing workflows, failures and fallback outcomes remain included. We did not collect blind human ratings, as instructed for this short demo; therefore this run makes no fan-preference, editorial-quality or human-acceptance claim.

| Arm | AI-composed | Deterministic fallback | Abstention | Calls | Median ms | Deterministic checks |
|---|---:|---:|---:|---:|---:|---:|
| T3 | 0 | 0 | 1 | 0 | 30 | all applicable checks passed |
| S3 | 14 | 0 | 1 | 28 | 7,501 | 15/15 case outcomes passed |
| M3 | 13 | 1 | 1 | 28 | 7,885 | 15/15 case outcomes passed |
| D3 | 14 | 0 | 1 | 14 | 3,438 | all applicable checks passed |

T3 produced 14 deterministic packages and correctly withheld the one ineligible case; the table's zero AI-composed count is intentional. Each model arm returned a package for the 14 eligible cases and abstained on the single delayed-outcome case. The `pass` for M3 includes its deterministic fallback package, not an accepted Reviewer approval.

### Paired result: M3 versus S3

- 15 matched case pairs; the two arms passed all applicable deterministic checks in all 15 pairs. There was no observed advantage on these checks.
- Both arms returned 14 packages and correctly withheld the same ineligible opportunity. S3 AI-composed all 14; M3 AI-composed 13 and served one deterministic fallback.
- The output plans matched in 10 of 14 packages. In the other four, M3 added the reception-zone claim to the detailed selection; no reviewer or fan rated that as more useful.
- M3's Reviewer requested zero revisions. On `untrusted-name`, the Reviewer response omitted a required claim verdict, so the workflow blocked that response and returned the deterministic package. This is a real observed fail-closed fallback, but S3 completed the same case without fallback; it does not establish that the Reviewer improved the outcome.
- Median elapsed time was 7.885 s for M3 and 7.501 s for S3. Both used 28 model calls. Recorded token usage was complete: M3 89,617 tokens; S3 91,718. D3 used 14 calls, as it omitted the review call.
- Across all arms the run made 70 calls, used 206,624 input and 13,034 output tokens, and had an estimated retail cost of $0.038814 USD at the verified East US rates ($0.15/M input, $0.60/M output). Unknown-usage workflows: zero. These are estimates, not a bill.

### Conclusion and demo wording

This run verifies that the pipeline preserved evidence, temporal scope, attribution and audience-variant contracts on this small developer-visible set. It also shows the actual handoff, an incomplete Reviewer response being contained, and a safe deterministic fallback. It does **not** show that M3 is more reliable than S3 on the measured checks, more useful to viewers, or better on real matches. In the observed run, S3 had one fewer fallback and M3 supplied a different optional detail in four cases without any utility rating. The demo therefore labels these as observed results, not a multi-agent win.

The demo page also shows a separate seeded policy probe. We injected the same fixed `historical_contrast` Director plan into both arms on three replay variants where the factual comparison was true but the provisional policy did not recommend leading with it. Each arm ran two trials per variant, for six matched pairs. The injected first Director response replaced a model call to isolate review versus self-review; the model then had the same evidence, model, renderer, remaining call budget, and repair opportunity in each arm.

Neither arm corrected the seeded angle: **M3 0/6; S3 0/6**. Both marked every proposal supported and returned it unchanged. No fallback or repair occurred. Ordinary package/evidence/cutoff/attribution/context/audience controls passed 6/6 for both arms; the additional seeded-policy control failed 6/6 for both. This shows that the current Reviewer and self-review prompts did not enforce the provisional emphasis policy in this probe. It does not show a factual error, because the historical comparison itself was supported; the policy is not football ground truth.

The probe used 12 model calls, complete usage (46,504 input and 3,719 output tokens), and an estimated retail cost of $0.009207 USD. The three variants share one match, so the six trials are repeated observations rather than six independent scenes. No human ratings were collected. The demo reports this separately from the spontaneous discovery comparison and does not claim a multi-agent advantage.
