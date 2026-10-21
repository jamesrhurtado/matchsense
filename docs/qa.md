# WHY/NOW engineering QA

Application: https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io

This is the hosted Azure MVP for engineering testing. It supports 171 fictional replay segments, including 90 s and 180 s sequences, with an independent investigation, approval and recap entry per delivered pass. It does not claim full-match analysis, real broadcast synchronization, or validated professional-football accuracy.

## Access and first run

The owner retrieves the producer access key from the local, private `.azure/qa-access.json` file and shares it with authorized testers through their chosen secure channel. Do not paste it into issues, screenshots or this guide. The homepage accepts the key; producer actions require it. Viewer URLs are read-only and need no key. This shared prototype key is not enterprise user identity or a per-user audit trail.

1. Open the application, enter the producer key, choose segment 01, and open the producer console.
2. Use 1× replay. The pass starts at 18 s; supporting retention evidence completes at 22.2 s.
3. For deliberate inspection, pause near 25 s and wait for the AI-reviewed candidate. This preserves the replay clock while model calls finish. Accelerated replay can legitimately finish before the model; its expired overlay must not be revived.
4. Inspect **Show why**, the independent evidence replay, definitions and source references.
5. Inspect **Processing & review trace**. A successful model run must show actual agent decisions, tool requests where chosen, model call counts and provider-reported tokens. `template fallback` is a degraded result, not successful model execution.
6. Approve the reviewed revision. Open the viewer companion, switch simple/detail, select Spanish and Theo Vega, then open the recap.
7. Retract in the producer console. The viewer explanation and open recap must disappear. An expired approved story remains available in recap, but its timed overlay disappears.

The model has a 25-second workflow deadline, two concurrent executions, at most eight model calls and twelve tool calls, and a token reservation budget. Overload/provider/validation failure yields an explicit supported template fallback or abstention. Nothing publishes automatically.

## Acceptance checks

| Area | Expected behavior |
|---|---|
| Authorization | Missing or wrong producer key cannot create/control/edit/approve, inspect diagnostics, or see an unapproved package |
| Positive segment | Eligible evidence produces a reviewed candidate; producer approval controls viewer visibility |
| Negative segments 02/03 | Ordinary unpressured and intercepted passes produce no candidate and no model calls |
| Evidence | Source cutoffs exclude future observations; source corrections invalidate old approval immediately |
| Editorial edit | Unsupported intent, match dominance or guaranteed outcomes are revised/rejected; accepted paraphrases need not match templates |
| Revision conflicts | Stale hash/revision returns 409; identical operation retries do not duplicate audit/publication |
| Audience controls | Language/detail/focus switch approved variants; shared overlay remains common |
| Streaming | SSE reconnect begins with an authoritative resync; snapshot recovery removes retracted content |
| Persistence | Paused session, package and approval survive an API restart; event redelivery does not duplicate observations |
| Timing | No story before evidence confirmation; expiry remains 52.2 s for the positive fixture, including late delivery |
| Mobile | Viewer at 390 px has no horizontal overflow and usable controls |
| Failures | Provider timeout/invalid output is explicitly labeled; persistence failure never advances a checkpoint past unwritten data |

## Automated checks

Local backend: `.venv313/bin/python -m pytest -q`. Expanded regression: `make synthetic-evaluate`; strict mode: `.venv313/bin/python -m evals.synthetic --strict --check-baseline`.

Local frontend production build: `npm --prefix apps/web run build`.

Local browser tests require local servers: `npm --prefix apps/web run test:e2e`. The hosted browser test is skipped unless explicitly enabled.

Hosted API workflow: `.venv313/bin/python scripts/cloud_smoke.py`. It starts a real billable model workflow, validates publication/variants/recap/SSE, leaves a paused approved QA session, and writes nonsecret diagnostics to `.azure/smoke-session.json`.

Restart the current API revision with Azure CLI, wait until `/api/ready` returns 200, then run `.venv313/bin/python scripts/cloud_smoke.py --retract`. This checks that the approved state survived and then retracts it.

Hosted browser: `WHY_NOW_CLOUD_TEST=1 npm --prefix apps/web run test:e2e -- cloud.spec.ts`. It reads the private QA access file server-side and stores screenshots plus a nonsecret verification report in `.run/`.

Multi-pass Azure QA: `.venv313/bin/python scripts/cloud_multi_smoke.py` starts three actual model investigations in one longer replay and verifies independent publication plus the deployed distance boundary. Then run `WHY_NOW_CLOUD_TEST=1 npm --prefix apps/web run test:e2e -- cloud-multiple.spec.ts` to inspect that same session through the hosted UI without additional model workflows. For restart verification, restart the current API revision, wait for a replacement replica to be ready, then run `.venv313/bin/python scripts/cloud_multi_smoke.py --restart-check`; this verifies stored approvals and retracts the last live QA moment.

## Report an issue

Include session ID, UTC time, replay clock/speed, browser/device, story revision, displayed execution mode, expected/actual behavior and the relevant trace action. Include token counts and `ingestion_lag_ms` when timing is involved. Exclude the producer key and authorization headers.

## Initial Azure verification (historical)

Verified 20 October 2026 (Lima), 21 October UTC, against API `cloud-v10` and web `cloud-v5`.

| Check | Result |
|---|---|
| Backend regression suite | 88 passed, including contracts, approval races, batch durability, numeric hashing, cutoffs, provider failures and telemetry sanitization |
| Production builds | API and web Linux amd64 images built successfully in ACR; web production build also passed locally |
| Public API positive flow | Passed real AI execution, package-hash reproduction after Cosmos/HTTP, approval, overlay, Spanish player variant, recap and SSE resync |
| Actual AI measurement | API test: 11,019 ms, 5 calls, 6,014 tokens; browser test: 4 calls, 5,060 tokens, complete usage, three agent roles, no fallback |
| Negative segments | Segments 02 and 03 fully ingested through paused cutoff, no candidate and zero model calls |
| Hosted browser | Passed evidence inspection, approval, Spanish detailed Theo Vega focus, recap, 390 px layout and retraction; zero JavaScript errors |
| Restart durability | Azure confirmed revision restart; stored approval survived, then retraction removed viewer story and recap |
| Monitoring | Queried real workspace data: application requests/dependencies plus sampled `story.workflow` and `story.agent` spans are present |
| Credential handling | QA access file is mode 600, Git-ignored and excluded from image context; no producer key is embedded in web code |

Positive API session: `03f77fe4-4135-4022-8519-a8cb7b7edc65`. Browser session: `479f67a4-8454-4e17-ab7f-233e2ab108f5`. Both were retracted after verification. Local nonsecret browser evidence is `.run/cloud-browser-verification.json`, `.run/cloud-producer.png` and `.run/cloud-viewer-mobile.png`. The owner can provide these artifacts to testers.

Earlier deployment checks exposed and fixed missing WebSocket dependency, per-frame persistence latency, rollout cache/ownership handling and Cosmos integral-number serialization. Generated-text metric omissions correctly caused fallback; the final editor now appends authoritative facts rather than having the model retype numbers. These checks establish the engineering path, not a measured general AI success rate.

The historical offline synthetic evaluation remains in `evals/REPORT.md`; its small constructed dataset and deterministic timings are not cloud model accuracy or latency results. The expanded local regression is recorded separately below.

## Expanded synthetic regression

After the initial Azure handoff, the v2 data suite added 168 cases across 28 families and six whole parent configurations. The first-pass restriction was then removed and the observation-only corpus added to the runtime catalogue. Reproduction and scope are in [the data guide](synthetic-data.md); individual results and clocks are in [the expanded report](../evals/synthetic-v2/REPORT.md).

| Local check | Result |
|---|---|
| Backend regression suite | 196 passed, including generated-feed API cases, independent multi-story tests against SQLite/Cosmos test adapters, scoped agent tools, and ten distance-boundary cases across both attack directions |
| Data validation | All 168 clean and observed feeds passed schema, roster, event/position, movement, clock, retransmission and correction checks |
| Export integrity | All 168 runtime streams, metadata files, clean trajectories and reference annotations matched their recorded hashes; 109,932 observed source frames, 110,730 delivery rows |
| Authored candidate/expiry checks | 168/168 cases passed all checks; 594/594 checkpoint decisions matched; 72/72 distinct moments detected and no false alerts in this constructed suite |
| Historical scope defect resolved | The earlier twelve failing cases now pass; all eighteen previously missed later moments are investigated. Observation/reference hashes are unchanged from commit b9bc99f |
| Package integrity | 72 local template packages and 7,200 variants passed schema, numeric, source-cutoff and content-hash checks |
| Defect found and fixed | The five metre progression gate now compares the original distance; 4.96 m cannot qualify through display rounding |
| Evaluation cost | Zero model calls for the complete offline regression; bounded live integration checks are recorded separately |

CI checks dataset/reference hashes and every expected/detected outcome against an explicit regression baseline. Strict mode and the unchanged-input guard both pass after the per-pass update. The first implementation correctly exposed multiple-pass failures before the fix; historical results are retained in Git. Offline success does not certify football realism or semantic AI accuracy on all 168 cases. The expanded observation-only catalogue contains 171 replays and is deployed without evaluation labels, references or seeds.

## Multiple-pass Azure release verification

Verified 21 October 2026 (Lima), API `cloud-v13` and web `cloud-v7`, version `0.3.0`.

| Deployed check | Result |
|---|---|
| Resource use | Same resource group and 14 listed resources; no additional Azure services provisioned |
| Runtime catalogue | All 171 observation-only replays available, with actual durations; expanded streams compressed and no reference labels in the runtime image |
| Three-minute replay | Independently investigated passes 1, 2 and 3 through real Event Hubs ingestion and durable Cosmos storage |
| Model execution | Final sample: 14 actual calls, 17,279 reported tokens, complete usage; two model-composed packages and one explicit factual-template fallback |
| Measured workflow time | Moment 1: 17,260 ms; moment 2 fallback: 11,013 ms; moment 3: 15,863 ms; excludes replay waiting, ingestion and human approval |
| Publication | Independent revision-1 approvals, source/hash checks after Cosmos/HTTP, current overlay, archived selection and Spanish actual-receiver variants passed |
| Recap and retraction | All three approved moments accumulated; retracting the middle moment removed only that moment and preserved the newer live overlay |
| Distance boundary | Fully ingested 4.96 m continuation produced no candidate and zero model calls on the deployed build |
| Browser regression | Nine local browser tests passed, including independent approvals, archived retraction, selected-history races and streaming |
| Final hosted browser | Passed three producer queue entries, archived evidence/retraction availability, two approved viewer entries, unchanged shared overlay while selecting history, Spanish Jori Luna focus, multi-moment recap and 390 px layout; zero JavaScript errors |
| Final API restart | Replacement replica confirmed; independent approvals and two-moment recap survived. Retracting the last live QA moment preserved the earlier approved archive |

Final browser evidence is `.run/cloud-multiple-browser.json`, `.run/cloud-multiple-producer.png` and `.run/cloud-multiple-mobile.png`.

Final API QA session: `56f53290-7e3f-4fe3-9152-d023ffb8957c`. Nonsecret results are `.run/cloud-multi-smoke.json`; guard diagnostics are `.run/cloud-multi-guard-diagnostics.json`. The initial all-AI wording check stopped at moment 2 because repeated “key pass” wording was rejected after the bounded repair. The same session was resumed without regenerating existing model outputs. The report retains each actual execution mode and fallback reason. This is a small integration sample, not an AI factual-accuracy rate or a fair agent comparison. Use `--require-all-ai` for a separate strict wording gate; default integration testing accepts explicitly labeled, verified factual fallbacks.

The first deployed browser inspection also exposed a broad Spanish opportunity claim and a misleading producer-edit label. The final guard rejects unsupported opportunity/chance wording in both languages, allows one repair, then uses the explicit factual fallback. The label now says “Proposed wording reviewed” without inventing who proposed it. Unit tests cover successful repair and repeated-claim fallback. Model review remains fallible; these checks do not establish complete free-text semantic verification.

## Version 0.4 Grand Prize iteration verification

Verified 21 October 2026, web `cloud-v8`; API `cloud-v15` for multi-moment/browser verification and `cloud-v16` for replacement-replica and initial continuous timing.

| Check | Actual result |
|---|---|
| Backend | 272 tests passed after the transport fix |
| Existing synthetic regression | 168 cases, 594 checkpoints and 72 moments pass with unchanged inputs/references; zero model calls |
| Frontend | Production build/TypeScript passed; 14 local browser tests passed |
| Hosted browser | Multi-moment producer/viewer, history selection, role focus, Spanish, recap, shared overlay and 390 px layout passed; no JavaScript errors |
| Three actual model attempts | Two AI packages and one explicit factual fallback; six calls, 12,909 tokens, complete reported usage |
| Server workflow durations | 7,826.233 ms; 7,005.049 ms; fallback 7,203.831 ms; excludes replay waiting and human review |
| Persistence/publication | Version 2 validation, exact hashes after Cosmos/HTTP, independent approvals, scoped retraction and replacement-replica survival passed |
| Guard | Fully ingested 4.96 m case produced no candidate and no model calls |
| Repository/CI | Private MIT repository pushed; backend and web GitHub Actions passed at `5949be4` |

The third model attempt rejected true spatial claims as editorially irrelevant. The factual guard correctly selected the template fallback. Prompt v2.1 separates factual support from editorial relevance; later two-stream execution produced two AI packages. These few examples do not establish an accuracy rate or superiority over the single-agent comparator.

Multi-moment artifact: `.run/cloud-multi-iteration-v2.json`, session `e25db3f8-31cf-4898-87bd-a4182ee91344`. Replacement verification retained approvals and recap; the last live QA moment was retracted afterward, preserving the earlier archive. Hosted browser evidence is `.run/cloud-multiple-browser.json` and the associated screenshots. The final state therefore differs from the earlier browser test's two-approved-moment setup.

### Continuous 1× timing: initial bounded measurement

The script `scripts/measure_replay.py` never pauses or seeks to help candidate readiness, automatically approves nothing, retains misses and checks that unapproved content stays private. The cloud report `.run/continuous-cloud-iteration-v2.json` used two concurrent replays of one known scripted parent on `5949be4` / API `cloud-v16`.

| Replay | AI calls / tokens | Scheduling observation → candidate | First API candidate clock | Display window remaining |
|---|---|---|---|---|
| 1 | 2 / 4,269 | 8,524.557 ms | 34,646 ms | 17,554 ms |
| 2 | 2 / 4,273 | 6,540.965 ms | 43,447 ms | 8,753 ms |

One missed the proposed 10 s review-window target. The candidate computation duration alone does not capture the delay. Active-first transport scheduling, skipping successfully flushed idle clocks, cached source ordering and releasing the transport lock during durable reads were subsequently implemented. Six regressions cover cutoff safety, concurrent arrivals, failure/retry, idle seeks and bounded caches. API-wide locking and sequential monitoring can also affect this measurement; do not attribute every delay to transport.

### Post-change bounded measurement

API `cloud-v17` / commit `c85f035`, same web `cloud-v8`, report `.run/continuous-cloud-iteration-v2-transport.json`:

| Replay | AI calls / tokens | Scheduling observation → candidate | First API candidate clock | Display window remaining |
|---|---|---|---|---|
| 1 | 2 / 4,371 | 6,225.911 ms | 32,414 ms | 19,786 ms |
| 2 | 2 / 4,266 | 6,665.221 ms | 34,710 ms | 17,490 ms |

Both produced AI candidates, complete usage and no publication; unapproved viewer isolation passed. Sessions `827cd17d-09b0-4442-9e59-038d8d476a89` and `6d3b045c-bcea-4249-aa30-de243ed808f9` were paused only after observation. Both left more than 10 s in this run. The earlier below-target result remains above; two pre/post samples with model and infrastructure variation are not a controlled causal experiment or evidence of a reliable target success rate. Current API and web revisions are healthy; no resources were added.

This is not the planned 20-opportunity timing study, a P95 estimate, independent real-football data, a browser-display acknowledgment, exact durable-ingestion timing or a production load certification. Human comprehension, football expert review and blinded T2/S2/M2 comparison remain pending. Four developer-visible harness cases share one generator backbone and are not sealed independent final parents.

## Known boundaries

One API replica/worker is enforced. Cosmos guards publication transactions, but this does not certify arbitrary horizontal scaling. Publisher prioritizes active sessions and skips unchanged idle clocks; high session counts still require load evaluation. SSE uses snapshot resync rather than a durable browser-event backlog. There is no human comprehension study, fair single-agent comparison, or production load certification yet. Model review is fallible even when numeric/schema checks pass. The version 2 constrained grammar covers a limited set of supported facts; richer football insight remains an improvement area. Spanish changes the explanation and recap, while interface labels currently remain English. Graceful API restart was tested; deliberate cloud outages at every checkpoint boundary and production load certification remain untested.
