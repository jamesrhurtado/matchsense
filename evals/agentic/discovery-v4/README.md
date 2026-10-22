# v4 discovery comparison — actual model evidence

22 October 2026, America/Lima. Developer-visible discovery, one trial per model arm. These are correlated cases sharing existing trajectory backbones; no independent final benchmark or human ratings are claimed.

## Frozen comparison, prompt v4.0

Fifteen cases × four arms = 60 outcomes. Fourteen eligible opportunities and one intentionally insufficient case per arm. All expected opportunities returned a package; the negative was withheld in every arm. All returned packages passed the runtime contract and the available handwritten context-reference checks. These checks do not establish football usefulness.

| Arm | AI / template / fallback | Correct quiet cases | Model calls | Median all-case elapsed | Estimated model cost |
|---|---|---:|---:|---:|---:|
| T3 deterministic | 0 / 14 / 0 | 1 | 0 | 29.7 ms | $0 |
| S3 single + self-check | 13 / 0 / 1 | 1 | 27 | 8,337.2 ms | $0.015684 |
| M3 Director + Reviewer | 14 / 0 / 0 | 1 | 28 | 7,605.4 ms | $0.015850 |
| D3 Director only, evaluator-only | 14 / 0 / 0 | 1 | 14 | 3,193.5 ms | $0.006455 |

Total: 69 model calls, 203,540 input tokens and 12,430 output tokens; complete reported usage; estimated $0.037989 at verified public GlobalStandard text-model rates of $0.15/M input and $0.60/M output. Timing includes runner overhead and the early-abstention case; it is not ingestion-to-display time or a live operating envelope. Provider variation and one trial prevent attributing latency differences to architecture.

**Finding:** the broad selected angle matched across all arms in all eligible cases. The model arms tended to select fewer detailed facts than T3, but no reviewer repair was requested. Neither a reviewer usefulness advantage nor superiority over the template/single-agent baseline is established. The single S3 fallback does not establish a statistically reliable M3 reliability advantage; it still delivered supported template content.

## Observed failure and applied fix

S3's `relay-attribution` Director omitted mandatory `c-pressure` from detailed claims. Runtime validation selected factual fallback before model review; no invalid text published. The original failure and its usage are retained in `comparison-outcomes.json`.

Prompt v4.1/code now gives every model strategy the same single bounded opportunity to repair a structurally invalid narrative plan. Required facts and validation are not relaxed. Regression tests reproduce the omitted fact and verify repair in both S3/M3. A subsequent targeted one-case/four-arm verification made five model calls and returned valid outputs, estimated $0.00228225. Its model responses were valid on the first proposal, so that run alone does not demonstrate the repair being invoked.

The targeted check is not a replacement for the frozen comparison. A fresh independent final comparison and blind human ratings remain required before selecting an architecture for a claimed quality benefit.

## Other runs and artifact policy

- Initial four-case smoke: 16 outcomes, 15 calls, estimated $0.00890865; complete usage.
- Frozen discovery comparison: 60 outcomes, 69 calls, estimated $0.037989; complete usage.
- Post-fix targeted check: 4 outcomes, five calls, estimated $0.00228225; complete usage.
- Combined estimated model usage: **$0.0491799**, excluding existing infrastructure. Public retail estimates are not invoice totals.

Exact manifests include source fingerprints, model/deployment/version, prompts, renderer, rate source, budget and cases. `*-outcomes.json` retain every output or failure in a concise form. Full packages/traces and rating packets remain in the corresponding ignored `.run/agentic-v4-*` folders. Blinded CSV rows stay blank until actual reviewers complete them. Do not send arm reports, outcome summaries or the private rating mapping to raters before ratings are frozen.

All comparison arms use the same deterministic renderer and evidence. D3 is an evaluator-only ablation guarded by `evaluation_only=True`; it is never selected by the production API. Factual checks and producer approval remain required.
