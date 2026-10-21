# WHY/NOW engineering QA

Application: https://whynow-web.graycoast-41e399d8.eastus.azurecontainerapps.io

This is the hosted Azure MVP for engineering testing. It supports three fictional 60-second football segments and one pass investigation per segment. It does not claim full-match analysis, real broadcast synchronization, or validated professional-football accuracy.

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

Local backend: `.venv313/bin/python -m pytest -q`.

Local frontend production build: `npm --prefix apps/web run build`.

Local browser tests require local servers: `npm --prefix apps/web run test:e2e`. The hosted browser test is skipped unless explicitly enabled.

Hosted API workflow: `.venv313/bin/python scripts/cloud_smoke.py`. It starts a real billable model workflow, validates publication/variants/recap/SSE, leaves a paused approved QA session, and writes nonsecret diagnostics to `.azure/smoke-session.json`.

Restart the current API revision with Azure CLI, wait until `/api/ready` returns 200, then run `.venv313/bin/python scripts/cloud_smoke.py --retract`. This checks that the approved state survived and then retracts it.

Hosted browser: `WHY_NOW_CLOUD_TEST=1 npm --prefix apps/web exec -- playwright test cloud.spec.ts`. It reads the private QA access file server-side and stores screenshots plus a nonsecret verification report in `.run/`.

## Report an issue

Include session ID, UTC time, replay clock/speed, browser/device, story revision, displayed execution mode, expected/actual behavior and the relevant trace action. Include token counts and `ingestion_lag_ms` when timing is involved. Exclude the producer key and authorization headers.

## Verification record

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

The offline synthetic evaluation remains in `evals/REPORT.md`; its small constructed dataset and deterministic timings are not cloud model accuracy or latency results.

## Known boundaries

One API replica/worker is enforced. Cosmos guards publication transactions, but this does not certify arbitrary horizontal scaling. Publisher scans historical sessions; high session counts need active-session scheduling before a broad rollout. SSE uses snapshot resync rather than a durable browser-event backlog. There is no human comprehension study, fair single-agent comparison, or production load certification yet. Model review is fallible even when numeric/schema checks pass. Generated introductions can be generic; richer football insight remains an improvement area. Spanish changes the explanation and recap, while interface labels currently remain English. Graceful API restart was tested; deliberate cloud outages at every checkpoint boundary and production load certification remain untested.
