# Agent evaluation harness

This is separate from `evals/synthetic.py`: the 168-case corpus remains inspected regression data. Start from the repository root:

```
.venv313/bin/python -m evals.agentic.run --dry-run
.venv313/bin/python -m evals.agentic.run
```

Both commands make **zero model calls**. The second runs the actual T2 deterministic structured renderer and writes manifests/results/report under ignored `.run/agentic`. Every attempted or budget-skipped job has a terminal row. Human grades remain unset. Errors record only their class, avoiding accidental provider-token disclosure.

Four developer-visible challenge compositions cover a receiving-player handover during team retention, duplicate cross-team names with mirrored direction, an instruction embedded in a name, and an outcome unavailable at cutoff. They share one existing trajectory-generator backbone; seed changes do not create independent football parents. This is an initial development set, below the planned 8–12 distinct discovery parents. A football reviewer still needs to assess realism; independent QA must author and seal the final set. Expectations are authored without invoking the production detector, but are not independent football ground truth.

`RuntimeInput` contains metadata, visible observations, cutoff and pass ID only. References, seed configuration, family labels and expected narrative never reach adapters. Source IDs are permitted because actual tools need them. No runtime module should import this evaluation package.

The injectable async adapter contract is `adapter(RuntimeInput, WorkflowBudget) -> {outcome, package, usage, ...}`. Outcomes include template/AI/fallback/abstention/rejection/timeout/failure/stale/budget exhaustion. Usage keys are `model_calls`, `input_tokens`, `output_tokens`; null means unknown and retains the full reservation. Adapter exceptions retain the reservation too. An adapter must enforce the shared per-workflow call/token ceiling before every provider dispatch; the outer ledger bounds scheduling, not arbitrary custom provider internals. Overall deadlines cancel awaits; that cannot reverse a billed provider request.

Live execution requires `--live --config PATH`. Copy only budget/configuration fields into that JSON, never credentials: positive total caps (`max_model_calls`, `max_input_tokens`, `max_output_tokens`, `max_estimated_cost`), verified `input_per_million`/`output_per_million`, `rate_source`, `rate_date`, `currency`, future `deadline_utc`, `model`, `deployment`, `api_version`, `prompt_version`, `tool_version`, `renderer_version`, `schema_version`, optional `trials` and `order_seed`. This handoff provides no current price quote. Inspect `--live --config PATH --dry-run` first. Provider credentials remain in environment variables. The runner rejects unknown configuration fields. Config identifiers must match the actual provider; release QA verifies that match.

T2 runs once per case; S2/M2 receive the configured trial count and equal per-workflow reservations. Scheduling is deterministically interleaved, serial to avoid quota contention. Track cold/warm behavior separately during timing exercises. All arms receive deep copies of the same allowed input. Human raters receive randomized package packets with common trace/usage labels removed; inspect packets for remaining arm hints before distribution and hold the original results mapping privately. Human reference answers remain separate from runtime. The current report lists all terminal counts and does not infer accepted stories, factual precision or superiority without independent grading.

The final comparison and continuous-play/user study are **pending**. See `docs/next-iteration/evaluation-plan.md` for denominators, timing protocol and decision thresholds, and `docs/user-study.md` for the ready-to-pilot instrument.

Current conservative reservation: six calls, 32,000 input tokens and 6,600 output tokens, while the Runner caps combined tokens at 32,000 and each output at at most 1,100. The separate reservations intentionally overestimate possible combined usage to bound scheduling cost using separate rates. Unknown usage keeps both reservations. S2/M2 share the same 15-second Runner deadline.
