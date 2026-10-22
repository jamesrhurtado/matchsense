# Runtime performance and accounting

21 October 2026 (America/Lima). Local candidate source is the working tree based on `170e1c49ecedfb1bb8dce5604cd1d2c2c13e061d`; this iteration has not deployed a new Azure build. Candidate source-file hashes are recorded in `evals/agentic/context-smoke/manifest.json`.

## Observed continuous replay sample

Command: `.venv313/bin/python scripts/measure_replay.py --url http://127.0.0.1:8000 --sessions 2 --output .run/iteration-continuous-two.json`.

Two simultaneous template-mode streams ran continuously at 1×. No pause/seek helped readiness; no stories were automatically approved. Both produced a candidate; no misses in this two-opportunity sample. Both reuse the original scripted parent. This does not establish independent opportunity coverage, model speed, P95, capacity or the I03 operating envelope.

| Stream | First observed candidate, replay ms | Time remaining before expiry | Scheduling-observed evidence → candidate completion | Model calls |
|---|---:|---:|---:|---:|
| 1 | 22400 | 29800 ms | 12.018 ms | 0 |
| 2 | 22441 | 29759 ms | 7.442 ms | 0 |

These durations exclude observation durability, human approval and browser rendering. Server `release_commit` was unset (`unknown`); the code base and working-tree status above disclose that limit. Raw session rows remain in the ignored `.run/iteration-continuous-two.json`. Older cloud timings and the 8.753 s review-time miss remain in the historical QA/decision log; no older failure was replaced by this sample.

## Delivered accounting

- Immutable workflow attempts retain produced/fallback/rejected/abstained/failed/interrupted states and known/unknown usage.
- Append-only delivery records link run ID and package revision/hash to acceptance, stale discard, persistence failure, expiry before acceptance and supersession. A stale result cannot commit its package.
- Eligible detected opportunities retain first detection, capacity deferral and never-scheduled expiry. Duplicate lifecycle writes are idempotent in SQLite/Cosmos.
- Approval request receipt is recorded separately. Browser acknowledgment validates session/story/revision/evidence identity against an approved package, retains only the first acknowledgment per revision, rejects stale/unapproved identities, and shares the existing cloud request limits.
- Browser paint interval uses its monotonic clock around two animation frames after committed text. Server receipt has a UTC timestamp. There is no server/browser clock-offset estimate or cross-clock subtraction. Missing acknowledgment is missing telemetry, not zero latency or proof of reading.

Mocked operational tests exercise stale completion and expiry while preserving original model usage and terminal state, duplicate acknowledgments, cross-story/old revision rejection, capacity deferral and never-scheduled expiry. Cloud adapter tests are in-memory contract tests, not a new deployed Cosmos load test.

## Remaining release gates

Exact durable-observation/evidence-readiness UTC stages; scheduling delay and process-monotonic stage durations; expected-but-never-detected opportunity reconciliation from independent references; crash-safe package/disposition append reconciliation; comprehensive restart/persistence failure exercises; API lock-hold profiling; 20 varied eligible opportunities at 1× with one stream and then two; budgeted model cost/latency and browser end-to-end measurements. No complete timing distribution or live-model operating limit is claimed.
