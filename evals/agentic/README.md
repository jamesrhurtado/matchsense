# Agent evaluation harness

This is separate from `evals/synthetic.py`: the 168-case corpus remains inspected regression data. Start from the repository root:

```
.venv313/bin/python -m evals.agentic.run --dry-run
.venv313/bin/python -m evals.agentic.run
```

Both commands make **zero model calls**. The second runs the actual T3 deterministic structured renderer and writes manifests/results/report under ignored `.run/agentic`. Every attempted or budget-skipped job has a terminal row. Human grades remain unset. Errors record only their class, avoiding accidental provider-token disclosure.

Four original developer-visible challenge compositions cover a receiving-player handover during team retention, duplicate cross-team names with mirrored direction, an instruction embedded in a name, and an outcome unavailable at cutoff. They share one existing trajectory-generator backbone; seed changes do not create independent football parents. This is an initial development set, below the planned 8–12 distinct discovery parents. A football reviewer still needs to assess realism; independent QA must author and seal the final set. Expectations are authored without invoking the production detector, but are not independent football ground truth.

Eight additional authored previous-pass variants share one current-play recording: greater/equal-or-mixed interpretations, signed backward history, insufficient history, missing endpoint, tracking gap and correction. The default now schedules 12 outcomes. These are not 12 independent parents.

`RuntimeInput` contains metadata, visible observations, cutoff and pass ID only. References, seed configuration, family labels and expected narrative never reach adapters. Source IDs are permitted because actual tools need them. No runtime module should import this evaluation package.

The injectable async adapter contract is `adapter(RuntimeInput, WorkflowBudget) -> {outcome, package, usage, ...}`. Outcomes include template/AI/fallback/abstention/rejection/timeout/failure/stale/budget exhaustion. Usage keys are `model_calls`, `input_tokens`, `output_tokens`; null means unknown and retains the full reservation. Adapter exceptions retain the reservation too. An adapter must enforce the shared per-workflow call/token ceiling before every provider dispatch; the outer ledger bounds scheduling, not arbitrary custom provider internals. Overall deadlines cancel awaits; that cannot reverse a billed provider request.

For a controlled review-role probe, run `scripts/run_agent_discovery.py --stage fault-probe --output <new-directory>`. It schedules three authored history compositions × two trials × S3/M3, with a 72-call ceiling and $0.50 estimated-cost cap. Both arms receive the exact same fixed initial `historical_contrast` plan, which is factually supported but conflicts with the current provisional policy's recommendation. The injected first Director response is evaluation-only and replaces one model call; the benchmark measures Reviewer versus self-review and any repair, not spontaneous Director selection. A deterministic check reports whether the seeded angle remains, is corrected by the model, or is contained by the template fallback. The policy is a product hypothesis, not football ground truth, so results must be labeled as controlled fault-injection evidence.

Live execution requires `--live --config PATH`. Copy only budget/configuration fields into that JSON, never credentials: positive total caps (`max_model_calls`, `max_input_tokens`, `max_output_tokens`, `max_estimated_cost`), verified `input_per_million`/`output_per_million`, `rate_source`, `rate_date`, `currency`, future `deadline_utc`, `model`, `model_version`, `deployment`, `api_version`, `prompt_version`, `tool_version`, `renderer_version`, `schema_version`, optional `trials` and `order_seed`. This handoff provides no current price quote. Inspect `--live --config PATH --dry-run` first. Provider credentials remain in environment variables. The runner rejects unknown configuration fields. The CLI checks schema/prompt/tool/renderer identifiers and deployment/API/model identifiers against the runtime environment. Set `FOUNDRY_MODEL_NAME` and `FOUNDRY_MODEL_VERSION` from verified deployment metadata before dispatch. Source-file hashes include uncommitted/new implementation files. Rate verification and football review remain explicit human work.

T3 runs once per case; S3/M3 receive the configured trial count and equal per-workflow reservations. Scheduling is deterministically interleaved, serial to avoid quota contention. Track cold/warm behavior separately during timing exercises. All arms receive deep copies of the same allowed input. Human reference answers remain separate from runtime. The current report lists all terminal counts and does not infer accepted stories, factual precision or superiority without independent grading.

The final comparison and continuous-play/user study are **pending**. See `docs/next-iteration/evaluation-plan.md` for denominators, timing protocol and decision thresholds, and `docs/user-study.md` for the ready-to-pilot instrument.

Current conservative reservation: six calls, 32,000 input tokens and 6,600 output tokens, while the Runner caps combined tokens at 32,000 and each output at at most 1,100. The separate reservations intentionally overestimate possible combined usage to bound scheduling cost using separate rates. Unknown usage keeps both reservations. S3/M3 share the same 15-second Runner deadline.
