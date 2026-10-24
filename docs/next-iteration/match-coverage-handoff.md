# Match coverage engineering handoff — 24 October 2026

Baseline: `2d515515f0dcaeac7ad48f62a63900bebaefc858`; initial backend gate 325 passed.
Changes are reviewable in the working tree; no new commit, push, deployment or
external publication was performed. Pre-existing planning/reviewer changes were
preserved. This implements the primary MC plan, not the earlier pass-only deferral.

## Delivery by dependency

| Ticket | Engineering status | Implementation and acceptance evidence | Open limit |
|---|---|---|---|
| MC01 | Implemented / locally checked | `docs/match-events.md`: examples, cutoff/clock/state policy, time accounting, TTL, archive and rollback contracts | Football definitions and Spanish review pending |
| MC02 | Implemented / locally verified | Additive observation variants; strict v5 event/evidence/claim reader and schema; existing immutable SQLite/Cosmos adapters validate v5 writes; both-adapter roundtrip/hash tests | Cosmos is tested through the existing fake service, not a live deployment; old binaries require isolated sessions/compatible reader |
| MC03 | Implemented / locally verified | Two reproducible four-minute observation-only replays; separate opt-in catalogue; 21 separately hand-authored reference cases; physical/feed validation and gzip/schema evidence | Engineering-authored references are independent of metric functions, not independent human football validation |
| MC04 | Implemented / locally verified | `match_state.py`, `event_metrics.py`: cutoff-scoped shots/goals, unknown actor, unlinked/own goals, duplicate/reorder/cancel/team/scorer revisions; score independent of approval | Synthetic observations only; no inferred save/scorer/assist |
| MC05 | Implemented / locally verified | Elapsed-time possession, explicit assigned/unknown/dead/loose durations, clipped boundaries and minimums; explicit recovery/change/restart facts, dedup and 3 s witness | Completeness is limited to delivered observations; no tactical cause inference |
| MC06 | Implemented; zero-call mode verified | v5 bilingual simple/detail/focus realization, bounded predicates/roles/denominators; same Director/Reviewer roles, rejection/abstention/fallback and fake-provider checks | One composite family fact per v5 story; live new-family model behavior unverified |
| MC07 | Implemented / locally verified | Shared exact hash/revision approval/storage/audit; stale job rejection, immutable correction/retraction, queue priority, producer override, archive-only approval, protected projections and restart smoke | Paid scheduling is opt-in and not performance-certified; no new persistence infrastructure |
| MC08 | Implemented / browser verified | Family labels/filters, prominent source score/period, shot point/outcome, goal score transition, possession table, recovery roles, approved history, linked incident source details and mixed recap | Source IDs remain technical in expanded evidence; external accessibility/Spanish review remains pending |
| MC09 | Verified in local template mode | Backend/original reference gates, independent new-family evaluation, type/format/build, desktop/phone Playwright, two-stream continuous measurement and actual SQLite/API restart | Browser/mobile Chromium, not all browsers; no live Cosmos, real feed, paid model or production-scale claims |
| MC10 | Engineering materials complete; human validation pending | README, demo/friend/presenter addenda, incoming/metric contracts, pilot consent/assignment/tasks/keys/raw-count gates and this handoff | James recruitment; facilitator assignment; 5–8 viewers and 1–2 football-aware reviewers, ratings/findings/retests pending |

## What the candidate does

- **Clock/period/score and goals:** source cutoff and initial state determine score.
  Pending/shot-goal alone never score. Confirmation adds once, cancellation removes
  once; source state remains correct through suppress/retract. Goal evidence shows
  score transition at confirmation. New explanatory revisions require approval.
- **Shots:** explicit starts plus resolutions support saved, blocked, off-target,
  unknown or confirmed-goal wording. Unknown shooter/location stays unknown; a
  location point does not fabricate a trajectory. Linked shot/goal packages share
  one viewer incident with approved source details accessible.
- **Possession:** fixed snapshots on 15 s boundaries, trailing up to 60 s clipped
  to segment/period, elapsed time rather than frame counts. Show assigned base,
  coverage and excluded durations. Below 30 s assigned or 95% coverage, withhold
  percentages. Approved snapshots never silently roll forward.
- **Control:** explicit recovery may verify player/cause; team transition alone
  does not. Restart remains distinct. Matching incident/pass identities deduplicate.
  Immediate loss prevents the optional next-three-second retention clause.
- **Publication/viewing:** all supported families share source hashes, exact
  approvals, expiry/history/retraction, EN/ES/detail/verified focus and evidence.
  Recap uses exact approvals, goals then varied incidents, max five, with complete
  timeline count. Source score header is separate. Public snapshots/SSE never show
  unapproved candidates. Viewer navigation does not change shared overlay.

## Reproduce

Install dependencies using the README. From the repository root:

```sh
make coverage-dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000), select **Mixed-event discovery**,
use the prefilled local producer key and open the companion link. `.run/match-coverage.db`
is disposable isolated SQLite. Existing `why_now.db` was not migrated or rewritten.
Ordinary `make dev` keeps the new catalogue off. Enabling the flag affects creation;
new mixed sessions retain their capability so disabling it does not reinterpret
stored v5 approvals. Existing 173 entries and v1–v4 packages remain unchanged.

The verification instance uses web 3100/API 8100 so the owner's pre-existing
3000/8000 processes remain untouched. For the same separate-process setup:

```sh
WHY_NOW_MATCH_COVERAGE=1 WHY_NOW_DB=.run/match-coverage-verification.db \
  .venv313/bin/python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8100
API_URL=http://127.0.0.1:8100 npm --prefix apps/web run start -- --port 3100
```

Run a production build first for `npm run start`. See [the short mixed demo](../match-coverage-demo.md)
for 25/33/47/60/105 s checkpoints and the 136 s cancellation replay. Replay jumps
are labelled navigation, never latency evidence.

## Verification artifacts

The original numerical evaluation inputs/expectations are unchanged. Generated
wall-time-only changes to its reports were restored; new-family outputs live in
`evals/match-coverage/`.

- Original checks: `make data-check`, `make evaluate`, `make synthetic-evaluate`.
  168/168 original constructed cases, 594/594 authored checkpoints, unchanged baseline.
- New references: `make coverage-evaluate`, 21/21 hand-authored cases and two
  independent physical/feed checks; `results.json`, `cases.json`.
- Reproducibility/schema: `schema-and-reproducibility.json`: both gzip exports
  reproduced byte-for-byte and real packages from all four new families validate
  against the exported v5 JSON Schema.
- Local backend, browser and build command outputs are summarized in
  `evals/match-coverage/verification.json` (written from actual completed checks).
- `continuous-play.json`: all authored and unexpectedly observed opportunities
  included; per-family readiness/queue wait/review time, deferrals, expiry and usage,
  two simultaneous full four-minute **1×** replays, zero paid calls. Source file
  fingerprints identify the measured implementation. This is a local poll-consumer
  upper-bound measurement; no production P95 claim.
- `continuous-play-initial.json` preserves the first run's incomplete schedule:
  77 authored checkpoints plus eight observed revisions without retained first-seen
  telemetry. It is not the complete acceptance denominator. The subsequent full
  schedule has 85 opportunities. Of these, 83 occur before segment end and all
  83 leave at least 10 s for review (minimum 12.65 s). The two end-boundary
  snapshots remain in accounting, with nominal windows excluded from live latency
  claims. Backend source fingerprints match delivery; the homepage default was
  refined afterward and is covered by the final browser suite. Further final-run results supersede that first run.
- `restart.json`: actual API process restart, same isolated SQLite, three exact
  packages/hash/approval identities retained, later source cancellation and public
  SSE reconnect verified. This is local persistence evidence, not live Cosmos.

Observed integration failures were fixed without changing original reference
expectations: catalogue count/isolation, legacy async ordering, legacy clock text
markup and a new test's mistaken assumption that an opposing team cannot have an
approved possession window. The restart harness also initially queried a protected
producer snapshot when asserting public visibility; it was corrected to use the
public projection. Retain actual run outcomes, not just successful packages.

## AI, pilot and release limits

Local mode performs no model requests. Existing pass model mode is unchanged.
The new-family v5 adapter uses the same bounded Director and Claim Reviewer roles;
source facts and bilingual text are recomputed by code. Models may select/reject
one supported composite family fact, never supply arbitrary prose, actor, score,
assist or denominator. `WHY_NOW_MODEL_MODE=foundry` plus `WHY_NOW_MATCH_MODEL=1`
explicitly selects its experimental integration. It is not verified against a
specific deployment and must not be pitched as a working measured new-family AI
release. Expired unscheduled paid candidates have no archive-generation guarantee;
use the verified template mode for historical pilot review.

No paid run or Azure resource change was made. Live Cosmos/Event Hubs, deployment,
new-family model behavior/cost/latency and broader concurrency remain separate
release checks. Keep a compatible v5 reader or isolate mixed sessions on rollback.

[The pilot packet](../match-coverage-pilot.md) is prepared, with no participant data.
James owns recruitment; a facilitator and independent football/Spanish answer-key
review are still required. Counterbalanced pass-only/candidate scenes currently
have different content: the instrument explicitly limits interpretation and
requires matched, reviewer-frozen keys before quantitative comparison. No user
benefit, football validity, reviewer score, productivity gain or 90+ rating is
inferred from automated tests. Public release/deployment stays separate.


Reproduce the timing sample against the isolated verification API:

```sh
.venv313/bin/python scripts/measure_match_coverage.py --base http://127.0.0.1:8100
.venv313/bin/python scripts/summarize_match_coverage.py
```

The capture takes about four real minutes, uses 1× playback and two fresh sessions,
and does not seek. Use port 8000 instead for the ordinary `coverage-dev` API.
The script's queue-wait value includes polling/HTTP observation delay; it is a
conservative consumer-readiness measure, not isolated scheduler service time.
The synthetic replay reuses the existing trajectory backbone with explicit source
event observations; it is not a shot-ballistics simulation or independent football
realism validation.

Final integration also preserves separately approved shooter/scorer roles inside
one linked incident, including team/family filtering. The browser regression for
the original pass now explicitly selects original segment 01: its expectations are
unchanged while the opt-in homepage intentionally defaults to the mixed segment.
Historical goal evidence retrieves its exact source cutoff even after another
goal's later correction; the current public score remains separately corrected.
