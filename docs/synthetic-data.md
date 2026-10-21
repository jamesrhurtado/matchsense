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
