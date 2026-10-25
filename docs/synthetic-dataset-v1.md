# Constrained synthetic episodes v1 — dataset card and preview

25 October 2026. SD01–SD04 engineering slice. Original fictional coordinates and
actors; development material, not held-out evaluation or expert-validated matches.

## What is delivered

**Six structurally distinct development parents, twelve paired case specifications,
twenty-four source views.** Each case has a 90-second base view and a view adding
delivery checks. Base views can intentionally contain unknown or missing source
observations. They do not all represent pristine tracking. The default four-minute
flagship and original catalogues remain unchanged.

| Passage | Parent / observed situation | Useful inspection point |
| --- | --- | --- |
| 01 | Support, circulation and a received forward pass | At 00:25: pass and nearby-opponent change; 24 m forward and observed team retention |
| 02 | Same physical passage, one opponent absent in the pre-pass window | At 00:25: no eligible pass/pressure story from incomplete evidence |
| 03 | Observed interception followed by retained control | At 00:20: explicit recovering player and previous team |
| 04 | Acquisition after unknown/loose control; source does not attribute the player | At 00:20: no inferred previous team or recovering player |
| 05 | Shot saved by the observed keeper; subsequent distribution | At 00:24: saved outcome and keeper control; ball reaches the keeper |
| 06 | Outfield block and subsequent loose-ball collection | At 00:29: blocked outcome and explicit collection |
| 07 | Goal following a pass; initial score 1:1 | At 00:36: confirmation changes score to 2:1 |
| 08 | Same incident with later source cancellation | Approve the goal at 00:36, advance to 00:52: score returns to 1:1 and old copy withdraws |
| 09 | Quiet circulation, including a keeper pass | At 01:00: explicit 60-second possession denominator; no qualifying pass highlight |
| 10 | Same possession passage with a sample gap and unknown ball interval | At 01:00: 55.9 s assigned / 4.1 s unknown; no percentage from insufficient coverage |
| 11 | Nearby-opponent change, teammate handover, later off-target shot | At 00:19: team retention despite a different controller; 00:34.2: off-target outcome |
| 12 | Delayed pass resolution and unknown shot outcome/shooter | Pass unavailable before 00:26; unknown shot available at 00:40 |

Each **delivery checks** entry adds an exact event retransmission, two missing
tracking samples at 00:10/00:10.1, and 800 ms extra availability delay on pass/shot
resolutions. This tests delivery behavior, not a new independent football scene.

## Try the data locally

For offline testing, run the normal coverage development server with the new
catalogue explicitly enabled:

```sh
WHY_NOW_SYNTHETIC_DEVELOPMENT=1 make coverage-dev
```

Open **http://127.0.0.1:3000**. Choose **Guided walkthrough** and **Template preview**,
open **More demo scenarios**, and select **Development passage 01** (or another
passage from the table). Start it, then use **Replay navigation → Skip to time**
to reach a stated inspection point. Review evidence, approve one story, open the
viewer companion and try Spanish/catch-up. The new passages do not inherit the
flagship's scripted guided pauses. For uninterrupted delivery, choose **Live
simulation** with **Template preview**; it runs at 1× and ends at 01:30.

The preview uses web **3200** / API **8200** and a separate SQLite store. It now
connects to the existing Azure deployment through the Director/Reviewer workflow;
the original engineering checks ran in template mode. Refresh the entrance,
choose **AI · Director and Reviewer**, and create a new session for AI testing.
Existing template sessions retain their recorded execution mode.

To start the AI API with the development catalogue (uses existing Azure resources;
requires Azure CLI sign-in), run:

```sh
WHY_NOW_SYNTHETIC_DEVELOPMENT=1 WHY_NOW_DB=.run/synthetic-slice-final.db .venv313/bin/python scripts/live_dev.py --api-only --api-port 8200
```

Point the web server at `API_URL=http://127.0.0.1:8200` and start it on port 3200.
The launcher verifies deployment identity, authentication and rates before startup.
Starting AI sessions makes model calls. Template preview remains available for
zero-call checks. No new model-quality claim is made: comparative AI evaluation
on these passages is SD05, still pending.

Rebuild/verify only the new exports:

```sh
make episodes-data
make episodes-evaluate
```

The exporter refuses to overwrite an existing new fixture with different bytes.
Once released, changes require new versioned identities; do not delete historical
exports or rewrite old approvals. During development only newly authored,
unpublished candidate outputs were regenerated to correct a support-lane overlap
and unify support targets with the actual episode ball. Original sources and
reference expectations were preserved throughout.

## Construction and measurement choices

- Observation sampling: **10 Hz**, 105 × 68 m pitch, x right / y down, declared
  period attack directions. Roles: eleven actors per side, including one keeper.
  No substitutions/dismissals are simulated.
- Authored episode state defines controller/team, flight, loose ball, stopped
  play and observation limits. Events and their contact coordinates are exported
  from that same state. Off-ball support and keeper target knots use the actual
  episode ball. Contact participants have explicit paths for saves, blocks,
  receptions and acquisitions.
- Player paths use C2 quintic rest-to-rest interpolation. The design profile
  bounds speed to 9 m/s, sampled acceleration to 6 m/s² and turning to 3 rad/s
  when both interval speeds exceed 1 m/s. Derivative tolerance is 0.05; contact and
  coordinate tolerances are explicit in the frozen profile. Ball speed is bounded
  to 30 m/s; kicks may change its velocity abruptly. These are generator choices,
  not human limits or FIFA certification.
- Players can pause at authored anchors. This is constrained scripted movement,
  not learned tactical behavior, collision physics or a full-game simulator.
  Close-contact frames are reported separately; near players do not automatically
  imply a tackle, recovery or cause. Keeper support can legally be outside the
  small goal area. A central support position need not move sideways continually.
- Ball points are restricted to the existing observation contract's pitch bounds.
  A reported goal's point at the line does not establish whole-ball crossing or
  absence of an offence; only explicit source confirmation changes the score.
  There are no generated assist, xG, difficulty or tactical-cause labels.

## Separation, ancestry and reproducibility

Authoring scripts and profile remain offline. Runtime folders contain only
`match.json` and `stream.jsonl.gz`. Runtime identifiers are opaque and the optional
catalogue has neutral passage numbers; it contains no seeds, parent labels or
expected answers. The application never imports the generator or reference key.
Existing delivered-clock source access still excludes future/unavailable rows.

The separate key at `data/evaluation-only/episodes-v1.json` states 32 checkpoints,
expected roles, outcomes, timing, denominators and prohibited implications. Its
expectations were authored without production metrics as their oracle. They are
engineering specifications, not independent football reviewer judgments.

All a/b specifications, clean/fault views and future mirrors of one parent belong
to the same development group. Six separately constructed episode/route scripts
share interpolation and serialization code. They are not six validated football
distributions. There are **zero held-out parents** in this slice. A later held-out
set must be authored and frozen before tuning against it; no claim of blindness
is made for these inspected development cases.

The manifest records profile and authoring-file SHA-256, parent-structure hashes,
case/view membership and export hashes. Generation has no RNG or model calls.
Gzip uses a fixed timestamp; byte reproducibility was checked with the repository's
Python environment. Do not assume all compression-library/platform versions
produce identical compressed bytes.

## Verification and remaining work

See [case-level results](../evals/synthetic-vnext/results.json) and the
[verification record](../evals/synthetic-vnext/verification.md). Independent
validation reads observations, not authoring paths or detector outcomes. It
checks current feed rules, movement derivatives, period direction, control and
shot/contact alignment, goal-link consistency, cutoff boundaries and the latest
corrected tracking projection. Negative tests distinguish intended semantic
failures from schema rejection.

A QA-only excerpt crosses 45:00, explicitly omits a 15-minute halftime, then starts
period two with reversed direction. It derives from the quiet parent, is not a
seventh scene, and is not in the playable catalogue or a continuous-play claim.

Original runtime/schema/reference files and stored packages were snapshotted
before implementation and compared afterward. New data checks, original numerical
regression, API/browser integration and human/AI evaluations are reported separately.

Held-out cases, current mixed-family agent comparisons, football/Spanish ratings,
user benefit and the two four-minute composed demos remain SD05–SD07 work. The
existing failed live-AI review-time target remains open. This slice adds no Azure
resources, deployment, public repository change or external publication.

Provenance/licensing: original fictional scene definitions and generated coordinates
under the repository's existing MIT license. External sources informed design
choices only; no third-party trajectories, event records, footage or logos were
imported. [Research and source limitations](synthetic-data-research.md).
