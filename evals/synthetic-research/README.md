# Synthetic-data research audit

25 October 2026. Research only; no new product scenes or model evaluation.

Run from the repository root:

```sh
.venv313/bin/python evals/synthetic-research/audit.py
```

`current-fixtures.json` records the existing flagship/live streams 005–008, their
hashes, current feed-validator results and sampled movement diagnostics. All four
pass the existing validator. Maximum sampled player speed is approximately
8.16 m/s; maximum finite-difference vector acceleration is 103.54 m/s² in three
streams and 86.10 m/s² in the missing-frame variant. The audit documents its
calculation. These values identify abrupt path joins, not calibrated human
acceleration or a new realism score. All four share flagship trajectory ancestry.

Checks performed: script execution and byte-compilation; a second execution
reproduced the JSON exactly; all four stream hashes matched the recorded values;
new research/plan local links resolve; scoped whitespace checks passed. Existing
product fixtures were not regenerated. No backend, frontend, browser or model
quality improvement is claimed from this audit. Previous verification remains
separate. No real-data import, paid model call, deployment or publication occurred.

See [research](../../docs/synthetic-data-research.md) and
[proposed implementation](../../docs/next-iteration/synthetic-data-plan.md).
