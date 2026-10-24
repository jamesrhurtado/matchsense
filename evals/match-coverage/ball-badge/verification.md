# Ball-carrier badge verification

24 October 2026. Live stage presentation only; no source/package/backend changes.

Build, typecheck, formatting and whitespace checks passed. Full browser suite:
**27 passed, 2 paid Azure checks skipped** (1.8 minutes). Two new cases at 390 and
1440 px check two-digit number/badge separation in a crowded frame, explicit
source carrier identity/coordinates, no leader/dot over the carrier, correct
free-ball release, no indicator for missing ball data and no page overflow.
The existing free-ball exact-coordinate and keeper-kit regression remains passing.

Desktop/mobile captures were visually inspected: [desktop](desktop.png),
[mobile](mobile.png). Logs alongside this file. No backend numerical/continuous
run repeated for this presentation-only change; no model or deployment claim.
