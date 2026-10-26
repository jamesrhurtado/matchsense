# Multi-agent effectiveness: research and product decision

Prepared 22 October 2026 (America/Lima). Scope: local MVP quality and agent behavior; no deployment or submission logistics.

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

The runner randomizes execution order, retains every expected opportunity, validates handwritten context references after generation, and reports all failures, fallback, rejection and incomplete usage. It writes blinded output packets and blank rating forms. Failed or missing outputs remain in the human-review packet. A package returned after a repair is not automatically counted as a correct repair.

The discovery cases are developer-visible and share existing trajectory backbones. Repeated trials and variants are not independent football scenes. Mechanical checks establish contract/reference behavior; they do not establish editorial usefulness or comprehension.

## Decision rules

1. Review paired T3/S3/M3 outputs blind with football and producer reviewers. Compare useful supported acceptance, substantive edits, missed opportunities, wrong rejection, calls, estimated cost and latency.
2. Inspect D3 versus M3 to identify actual reviewer contributions. Label injected challenges; do not present them as spontaneous model mistakes.
3. Keep an independent reviewer only if its benefit or risk reduction justifies its measured overhead. A practical initial selection threshold is a descriptive 10 percentage point gain in accepted opportunities or 20% less substantive editing without a severe correctness regression, alongside timing targets. Small samples may remain inconclusive.
4. If S3 or T3 meets the task more effectively, choose it and state the result. Do not manufacture complex tasks or add roles to force a favorable category claim.
5. Expand to independently authored discovery/final scenes before claiming generalization. QA holds final expectations outside runtime access; human review is required for football usefulness and Spanish semantics.

## Reproduction and evidence

`python -m evals.agentic.run` is zero-model by default. `scripts/run_agent_discovery.py --stage smoke|comparison --output <new-directory>` explicitly enables existing-model calls, verifies the current text-model deployment and public retail rates, writes the bounded configuration and refuses to overwrite an existing run directory. It creates no Azure resources.

Raw runs, full traces and blinded packets are local under `.run/agentic-v4-live-smoke` and `.run/agentic-v4-live-comparison`. Public summaries and exact manifests belong in `evals/agentic/discovery-v4`. The smoke and comparison ceilings are $0.50 and $1.50 respectively; reported costs are estimates from verified rates, not an invoice. Remaining reservations are retained when usage is unknown.

Reviewer recruitment: James confirmed on 22 October that he can arrange football reviewers and producer/viewer testers. No completed sessions or ratings are implied. Use the [reviewer guide](reviewer-guide-v4.md) for the next step.

## Actual discovery conclusion

The [preserved comparison](../../evals/agentic/discovery-v4/README.md) completed 60 outcomes across 15 correlated discovery cases, with 69 actual model calls and complete usage. All arms selected the same broad angles; M3 requested no repairs. S3 encountered one mandatory-claim omission and delivered factual fallback. That single event is not sufficient evidence of M3 superiority. A subsequent shared validator-repair fix is regression-tested and separately verified. Independent human usefulness ratings and fresh cases remain the decision gate.
