# Expanded synthetic evaluation

Generator 2.0.0; mode `template`; metric `pressure-escape-v1`.

**150/168 cases passed every checkpoint; 18 cases have mismatches.** 570/594 checkpoint decisions matched their authored expectations.

A passing case means every availability, candidate and expiry checkpoint matched. All exported original and corrected feeds passed structural and physical validation.

| Split | Parents | Cases passed / total | Checkpoint TP / FP / FN | Expected moments detected / total |
|---|---:|---:|---:|---:|
| development | 2 | 50 / 56 | 20 / 2 / 6 | 18 / 24 |
| held_out | 2 | 50 / 56 | 20 / 2 / 6 | 18 / 24 |
| validation | 2 | 50 / 56 | 20 / 2 / 6 | 18 / 24 |

## Failures to prioritize

| Family | Cases with mismatch |
|---|---:|
| long_session | 6 / 6 |
| multiple_passes | 6 / 6 |
| rounding_boundary | 6 / 6 |

Raw clocks, expected/detected IDs and metric operands are in `results.json`. Failures are reported even when they reflect a documented MVP scope limit. No detector thresholds or reference labels were changed to improve these results.

## Family coverage

| Family | Passed / total |
|---|---:|
| backward_pass | 6 / 6 |
| correction_restores | 6 / 6 |
| correction_withdraws | 6 / 6 |
| delayed_outcome | 6 / 6 |
| different_receiver | 6 / 6 |
| duplicates | 6 / 6 |
| escape | 6 / 6 |
| expired_outcome | 6 / 6 |
| insufficient_bypass | 6 / 6 |
| insufficient_progression | 6 / 6 |
| intercepted | 6 / 6 |
| lateral_pass | 6 / 6 |
| long_session | 0 / 6 |
| missing_ball_confirmation | 6 / 6 |
| missing_pressure | 6 / 6 |
| missing_release | 6 / 6 |
| multiple_passes | 0 / 6 |
| no_pass_events | 6 / 6 |
| noisy_tracking | 6 / 6 |
| out_of_play | 6 / 6 |
| possession_interruption | 6 / 6 |
| reordered_delivery | 6 / 6 |
| retention_gap | 6 / 6 |
| rounding_boundary | 0 / 6 |
| sparse_pressure | 6 / 6 |
| uncontrolled | 6 / 6 |
| unknown_possession | 6 / 6 |
| unpressured | 6 / 6 |

## Measurement scope

Distinct expected moments: 54/72 detected; distinct false alerts: 6 across 183.0 simulated minutes (0.0328/minute). These are correlated scripted examples.

Median metric computation: 1.676 ms; maximum 4.575 ms. Warm-process metric computation only; excludes generation, validation, workflows, replay, network and human approval.

Workflows attempted: 60; packages produced: 60; variants structurally/numerically checked: 6000. Actual model calls: 0; reported tokens: 0.

The default run uses deterministic templates. AI evaluation is a separately requested, budgeted run and must report actual model mode, fallbacks, abstentions and usage. Factual templates passing does not establish model semantic quality.

## Limitations

- Six scripted parent configurations, with correlated scenario/fault variants; not independent real matches.
- References are authored engineering expectations; football expert review and audience usefulness studies are pending.
- Checkpoint precision/recall counts predefined time decisions, not continuous full-match detection accuracy.
- Distinct false alerts are deduplicated by case/pass; simulated minutes include scripted quiet time.
- Candidate coverage includes false alerts; quiet cases combine deliberate negatives and missing-evidence abstentions.
- Variant checks cover schema, evidence references, numeric consistency and hash integrity; free-form semantic correctness is not established.
- Local execution does not exercise Azure transport, durable production load, web presentation or human approval latency.
- The existing engine investigates only the first pass. Multi-pass and long-session expectations intentionally exceed that capability.
- Held-out parents were fixed before the first run; after inspection they are regression data. Fresh final parents are required after tuning.

Reproduce with `make synthetic-evaluate`. Use `--strict` to return a failing exit code on any authored mismatch. `--check-baseline` fails on any changed case/check outcome, while retaining the disclosed current failures in the report.
