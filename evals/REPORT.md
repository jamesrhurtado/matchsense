# Local evaluation results

Measured median processing: 3.361 ms; maximum: 5.926 ms. Scope: metric calculation plus local template workflow, one warm process, excludes replay/network/human time.

| Split | Parent configurations | Segments | TP / FP / FN | Precision | Recall | Alert coverage |
|---|---:|---:|---|---:|---:|---:|
| development | 2 | 6 | 2 / 0 / 0 | 100% | 100% | 33% |
| validation | 2 | 6 | 2 / 0 / 0 | 100% | 100% | 33% |
| held_out | 4 | 12 | 4 / 0 / 0 | 100% | 100% | 33% |

Each segment lasts one simulated minute. A detected moment must match the reference pass; its first confirmation time is 22,200 ms (100 ms tolerance). Negative families are ordinary unpressured passes and intercepted passes.

The simple baseline alerts on every completed forward pass. It produces 4 false alerts on the held-out segments. This baseline is disclosed as a narrow deterministic comparison, not a single-agent model baseline.

## Limitations

- Small, constructed synthetic test, not a measure of professional football accuracy.
- Thresholds are heuristic. Every parent still uses the same simulator mechanics.
- Model-backed workflow and fair single-agent comparison were not run.
- Variant generation is restricted to deterministic approved phrases; no free-form semantic quality claim is made.
- No human comprehension or editorial timing study was conducted.

Reproduce with `python -m evals.run`. Labels/configurations are offline-only; runtime code does not import this module. Thresholds/configurations were fixed before this report run; further tuning requires a new held-out split.
