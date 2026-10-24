# Moving demo verification — 24 October 2026

These results are separate from the original fixture/latency results and the
visual-only stage refresh. New fixture IDs end in 3 and 4. IDs ending in 1/2 and
the original 173 catalogue entries are unchanged; original mixed compressed-file
hashes are checked against their provenance manifest.

- Backend: **381 passed** in 88.13 s. Includes physical/feed validation of both
  new fixtures, deterministic exports, visible-motion thresholds throughout the
  segment, keeper lanes, pass eligibility, shot locations, missing ball data,
  goal availability/cancellation, all-family approval/recap and stored hashes.
- Independent match references: **21/21 passed** with the two original mixed
  physical/feed checks. No reference labels were changed.
- Browser: **25 passed, 2 paid Azure checks skipped**, 1.7 minutes. Existing
  pass/mixed flows remain covered. New real-backend case runs from zero at 1×,
  observes player movement, verifies guided pause at the first pass, checks
  evidence focus/viewport, approves the real package and checks public delivery,
  disables guided pauses and verifies continuous play across a later recovery.
- Build, typecheck, formatting and whitespace checks passed.
- Desktop and 390 px mobile inspected; no mobile page overflow. Screenshots:
  [start](start.png), [8 seconds](eight-seconds.png),
  [guided pause](guided-desktop.png), [mobile](guided-mobile.png),
  [evidence brought into view](evidence-in-view.png).

Logs are alongside this file. Reproduce the source checks with
`python -m pytest -q`; web checks with the commands in the parent UI verification
record. The guided browser case requires `WHY_NOW_MATCH_COVERAGE_E2E=1` and the
coverage-enabled API.

Presentation motion gates and automated rendering are not human usefulness or
football realism validation. The segment remains authored/synthetic. No new
model-specific, recruitment, reviewer-rating or deployment claim is made.

Original synthetic baseline: **168 cases / 594 checkpoints**, unchanged saved
signature (`baseline_changed: false`), with reports written separately under
`original-regression/`. Original numerical expectations were not revised.
The final fixture-only subset has **7 passing tests**, including an additional
compatibility regression proving legacy regeneration retains the new catalogue
entries; this targeted run followed the full 381-check backend run.

Continuous playback: **both new four-minute segments reached 240,000 ms at 1×**,
with no seeks and no errors (242.54 s and 241.56 s elapsed). Every required family
was observed in each producer queue; score remained unconfirmed until source
availability and cancellation removed it in the correction segment. See
[continuous samples](continuous.json) and [summary](continuous-summary.txt).
These are API continuity checks, distinct from the real-browser motion/guidance
case and the earlier latency measurements. No human approval-speed claim is made.
