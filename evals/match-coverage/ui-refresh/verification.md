# Match stage UI verification — 24 October 2026

Scope: live match presentation in producer and viewer. No backend, model,
persistence, stored-package hash or numerical reference change in this UI refresh.

Final production build, typecheck and component formatting: **passed**.
Browser suite: **23 passed, 2 paid Azure tests skipped** (1.3 minutes).
This includes 17 original local browser regressions, four existing mixed-event
cases (three real API flows and one linked-role mock), and two new stage cases.
New cases check desktop/mobile score correction without approved prose, explicit
missing control, keyboard access to selection policy, progress semantics and
Spanish. Original expectations were retained.

Commands:

```sh
npm --prefix apps/web run build
npm --prefix apps/web run typecheck
npm --prefix apps/web run format:check
WHY_NOW_MATCH_COVERAGE_E2E=1 PLAYWRIGHT_BASE_URL=http://127.0.0.1:3100 npm --prefix apps/web run test:e2e
```

Visual inspection: 1440 px desktop, 360/390 px mobile, 768 px tablet; Spanish
mobile. No horizontal page overflow at the inspected sizes; no page errors in the
capture run. Snapshots use the real local mixed-event API session, paused at 105 s,
with engineering-approved fixture stories. The two new regression cases use mocks.

- [Desktop stage](stage-desktop.png)
- [390 px stage](stage-390.png)
- [Spanish stage](stage-spanish.png)
- [Final browser log](browser.txt)
- [Build log](whynow-ui-build.txt)
- [Typecheck log](whynow-ui-typecheck.txt)
- [Formatting log](whynow-ui-format.txt)

The initial browser run exposed a clock text-node regression, corrected by
preserving a separate clock value. A rebuild overlapped that run and invalidated
later loaded pages; it was interrupted and superseded by the full clean run after
restarting the production preview. Its partial log is retained as
`browser-initial.txt`. The final run has no failures.

Backend numerical evaluation, physical/feed checks, persistence restart and
continuous-playback measurement were not repeated for this presentation-only
change. Their earlier results remain in the parent directory and are distinct
from this UI gate. No model-specific, human-usefulness or deployed-result claim
is made. No publication or deployment occurred.

## Keeper/ball follow-up

Final gate: **24 local browser cases passed; 2 paid Azure cases skipped** (1.3 m).
Build, typecheck, formatting and whitespace checks passed. The extra browser case
checks role-based keeper shapes/colors, unchanged keeper coordinates, the ball
leader's exact source coordinate and the Spanish keeper legend. The full existing
pass/mixed-event regression suite remains included. Desktop (1440) and mobile
(390) screenshots inspected; no horizontal overflow at either width.

New results: [browser log](keeper-ball/browser.txt),
[desktop](keeper-ball/markers-1440.png), [mobile](keeper-ball/markers-390.png).
The keeper positions remain a documented synthetic-grid limitation; no fixture or
backend changes, physical-evaluation rerun, model call or deployment in this follow-up.
