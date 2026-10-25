# Expanded synthetic evaluation

Generator 2.0.0; mode `template`; metric `pressure-escape-v1`.

**168/168 cases passed every checkpoint; 0 cases have mismatches.** 594/594 checkpoint decisions matched their authored expectations.

A passing case means every availability, candidate and expiry checkpoint matched. All exported original and corrected feeds passed structural and physical validation.

| Split | Parents | Cases passed / total | Checkpoint TP / FP / FN | Expected moments detected / total |
|---|---:|---:|---:|---:|
| development | 2 | 56 / 56 | 26 / 0 / 0 | 24 / 24 |
| held_out | 2 | 56 / 56 | 26 / 0 / 0 | 24 / 24 |
| validation | 2 | 56 / 56 | 26 / 0 / 0 | 24 / 24 |

## Failures to prioritize

| Family | Cases with mismatch |
|---|---:|
| No checkpoint mismatches | 0 |

Raw clocks, expected/detected IDs and metric operands are in `results.json`. Failures are reported even when they reflect a documented MVP scope limit. The first run caught six false alerts from rounding distance before the gate; eligibility now uses the original measurement. No threshold or reference label was changed. The original first-pass restriction has been resolved: all authored later-pass checkpoints are now evaluated. Observation and reference hashes remain identical to commit b9bc99f, as checked against input-baseline.json. These inspected parents are regression data; final blind evaluation requires new parents.

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
| long_session | 6 / 6 |
| missing_ball_confirmation | 6 / 6 |
| missing_pressure | 6 / 6 |
| missing_release | 6 / 6 |
| multiple_passes | 6 / 6 |
| no_pass_events | 6 / 6 |
| noisy_tracking | 6 / 6 |
| out_of_play | 6 / 6 |
| possession_interruption | 6 / 6 |
| reordered_delivery | 6 / 6 |
| retention_gap | 6 / 6 |
| rounding_boundary | 6 / 6 |
| sparse_pressure | 6 / 6 |
| uncontrolled | 6 / 6 |
| unknown_possession | 6 / 6 |
| unpressured | 6 / 6 |

## Measurement scope

Distinct expected moments: 72/72 detected; distinct false alerts: 0 across 183.0 simulated minutes (0.0000/minute). These are correlated scripted examples.

Median metric computation: 1.823 ms; maximum 6.398 ms. Warm-process metric computation only; excludes generation, validation, workflows, replay, network and human approval.

Workflows attempted: 72; packages produced: 72; variants structurally/numerically checked: 7200. Actual model calls: 0; reported tokens: 0.

The default run uses deterministic templates. AI evaluation is a separately requested, budgeted run and must report actual model mode, fallbacks, abstentions and usage. Factual templates passing does not establish model semantic quality.

## Limitations

- Six scripted parent configurations, with correlated scenario/fault variants; not independent real matches.
- References are authored engineering expectations; football expert review and audience usefulness studies are pending.
- Checkpoint precision/recall counts predefined time decisions, not continuous full-match detection accuracy.
- Distinct false alerts are deduplicated by case/pass; simulated minutes include scripted quiet time.
- Candidate coverage includes false alerts; quiet cases combine deliberate negatives and missing-evidence abstentions.
- Variant checks cover schema, evidence references, numeric consistency and hash integrity; free-form semantic correctness is not established.
- Local execution does not exercise Azure transport, durable production load, web presentation or human approval latency.
- Held-out parents were fixed before the first run; after inspection they are regression data. Fresh final parents are required after tuning.

Reproduce with `make synthetic-evaluate`. Use `--strict` to return a failing exit code on any authored mismatch. `--check-baseline` fails on any changed case/check outcome, including changed detections when capabilities improve.
