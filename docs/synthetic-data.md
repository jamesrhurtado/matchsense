# Synthetic data suite v2

This suite extends the original three demo fixtures with 168 reproducible cases: 28 scenario families, each applied to six whole geometry/roster/motion parents. Every case uses the existing observation and match contract `1.0.0`, fictional teams, 22 players, 10 Hz tracking and metres/milliseconds. It represents a scripted segment, never a full match or a recording of actual football.

## Generate and inspect

```sh
make synthetic-list
# One clear positive, with separate runtime observations and offline references:
.venv313/bin/python -m simulator.suite --case p01-01
# Several feed faults:
.venv313/bin/python -m simulator.suite --case p01-18 --case p01-21 --case p01-22
# Entire reproducible corpus (larger local export):
make synthetic-data
```

Default export: `.run/synthetic/` (Git ignored). Each case has:

- `runtime/<opaque-match-id>/match.json` and `stream.jsonl`: observations only, safe inputs to a bounded replay adapter.
- `evaluation-only/<match-id>.json`: intent, expected pass IDs at specific clocks, fault plan, parent split and review status.
- `evaluation-only/<match-id>.clean.jsonl`: complete clean trajectory, including future observations. Evaluation only.
- `provenance/<match-id>.json`: generator version, opaque IDs and SHA-256 hashes of metadata, clean data and delivered data.

Large exports are regenerated from source rather than committed. IDs, metadata, stream content and hashes are deterministic. Runtime metadata contains no seeds, scenario family, expected outcomes or fault descriptions. Pass-start events reveal neither outcome nor actual receiver.

The existing hosted application still offers its original three allowlisted demo fixtures and a 60 s replay clock. These exports are compatible with its data schemas and evidence functions. Longer segments and multiple-pass cases are evaluation inputs; they do not imply the current producer UI can replay or publish them. Use the evaluation runner and API tests for the new cases before changing the hosted fixture registry.

## Situation coverage

| Group | Families |
|---|---|
| Supported passing | Clear escape; different actual receiver; mirrored direction; both attacking teams; varied rosters, geometry and release times |
| Plausible negatives | No pressure, too few opponents bypassed, backward/lateral pass, insufficient continuation, interception, uncontrolled/out-of-play resolution |
| Boundaries and uncertainty | 4.96 m continuation; missing pressure/release coverage; retention gap; unknown possession; unknown confirmation ball; no explicit pass events |
| Delivery | Delayed and expired outcomes, reordered arrivals, exact retransmissions, corrections withdrawing/restoring support |
| Realism and scale probes | Smooth position noise, ordinary pass before a qualifying pass, three qualifying passes in a three-minute segment |

The noisy feed uses a small, smooth observational bias rather than independent frame jitter that would create impossible velocities. Interceptions and loose-ball transitions share the state used to emit events and positions. Players move continuously below 10 m/s, ball movement stays below 30 m/s, and every available controller stays close to the ball. Out-of-play samples stop at the touchline within the current coordinate contract; shots/goals and periods are deferred until implemented as coherent typed events.

## Independent validation and references

`simulator.validate.validate_feed` separates arrival order from occurrence order, accepts exact retransmissions, rejects conflicting identities and broken correction chains, and validates both the original and corrected physical source views. Explicit missingness is legal; it is never replaced with zero coordinates. This validates the feed independently of story detection.

Expected outcomes are authored from play intent and an explicit fault plan in offline generator code. Neither that code nor the catalogue imports the detector, metric thresholds or narrative renderer. Checks include the millisecond before confirmation, delayed availability, correction arrival, and the original overlay expiry. A correction cannot retrospectively authorize an earlier story.

These are engineering reference annotations. Football expert review is explicitly pending; they are not independently certified tactical judgments. Physical constraints do not establish professional football realism, opponent decision quality, or usefulness to an audience.

## Splits and interpretation

Two complete parents belong to development, two to validation and two to held-out regression. All faults and counterexamples from a parent stay together. Each parent varies geometry, attack direction, passing team, release time, roster assignment and seed. Adjacent frames, checkpoints and fault variants are correlated and must not be counted as independent football examples. There are six independent authored parent configurations, not 168 independently observed matches.

The split was fixed before the first v2 evaluation. Once results are inspected, these cases become a regression set. Create new parent configurations and combinations for any final blind evaluation after tuning metrics or prompts. The v1 report remains a separate historical result, not evidence of accuracy on this expanded suite.

## Evaluate

```sh
make synthetic-evaluate
# Small development sample, written under .run/:
.venv313/bin/python -m evals.synthetic --case p01-01 --case p01-22
# Fail on every mismatch, including documented unsupported multi-pass cases:
.venv313/bin/python -m evals.synthetic --strict
```

The report separates scenario-level pass/fail, authored checkpoint precision/recall, distinct moments, missing-evidence cases, expiry/corrections, package/variant validation and model usage. Full reports are committed under `evals/synthetic-v2/`. The baseline contains dataset hashes plus every expected/detected checkpoint result, including known failures. CI fails on any changed outcome or dataset hash. An improvement also requires an explicit review/update; this avoids silently treating known failures as full acceptance.

The first frozen run of the expanded suite passed 150/168 cases and 570/594 checkpoints. Six false-positive cases exposed distance rounding before the five metre gate. Twelve further failing cases (six multi-pass, six three-minute sessions) exposed the documented first-pass-only engine limitation, missing eighteen expected later moments. The report contains the individual clocks and operands. These results are a baseline for fixes, not a release acceptance threshold.

Twelve API integration cases inject the generated feeds into isolated local sessions and exercise real HTTP approval, Spanish actual-receiver variants, overlay expiry, correction-driven withdrawal and recap invalidation. They intentionally register the test sessions directly: the public fixture allowlist is not expanded by a test. Separate generator/evaluator tests reject conflicting retransmissions, invalid lineage, implausible movement, incorrect event/frame control and future-label exposure.

### Optional actual-model sample

The full suite is offline, with no model requests or Azure charges from evaluation. To evaluate a small sample through the existing Agent Framework workflow, set the existing deployment endpoint/name and ensure local Azure authentication, then explicitly request:

```sh
# Uses the deployment identified by existing exported environment variables:
.venv313/bin/python -m evals.synthetic --mode foundry --case p01-01 --case p02-25 --max-investigations 2
```

Foundry mode requires one to six explicit case IDs and limits workflow investigations to one to six (default four). Each workflow retains the application's existing eight-call, token and deadline limits. Skipped cases, reviewer abstentions and template fallbacks stay visible. Detection scores remain pre-model; they do not treat a fallback as successful AI generation. Actual available tokens/calls are reported, with incomplete usage explicitly marked when a workflow abstains without returning usage. Monetary model cost is not fabricated. This is an evaluation helper, not a fair template/single-agent/multi-agent study, a cloud end-to-end test or a load test.

## Current findings and next product work

The local distance-gate fix raises the result to **156/168 cases and 576/594 checkpoints**, with no false alerts in this constructed suite. All twelve remaining failing cases are multiple-pass/long-session probes: the current engine misses eighteen later expected moments because it selects the first pass only. These known gaps remain in both the report and CI regression baseline. The original five metre threshold and scenario expectations were preserved; display rounding remains one decimal place.

Priorities from this run:

1. Add independent per-pass investigation, stable story IDs and multiple stored publication packages before increasing the hosted replay scope.
2. Add editorial ranking/cooldown for nearby candidates and ensure recap/retraction tracks each exact story revision.
3. Run a small explicit actual-model evaluation, then fresh parent combinations and football-informed review. The optional model runner is implemented; this offline run does not certify new scenarios against the live AI service.
4. After those changes, register selected new runtime fixtures in the hosted environment and exercise Event Hubs/Cosmos, browser delivery and bounded load. Local API tests do not establish that cloud path for the new corpus.

The corpus is generated locally under `.run/synthetic/`; these files are Git ignored. Generator source, tests, reference definitions, dataset/reference hashes, reports and the CI baseline are version controlled. The expanded corpus and distance fix are local; the hosted environment still uses the original fixtures and deployed code.
