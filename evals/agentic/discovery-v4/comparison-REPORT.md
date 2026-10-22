# Agent evaluation run

Mode: explicit model discovery.

Scheduled outcomes: 60. Human grading pending.

| Arm | Scheduled | Packages | Missing expected | Rejection candidates | Repairs returning packages | Known calls | Median observed ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| D3 | 15 | 14 | 0 | 0 | 0 | 14 | 3193.547 |
| M3 | 15 | 14 | 0 | 0 | 0 | 28 | 7605.36 |
| S3 | 15 | 14 | 0 | 0 | 0 | 27 | 8337.16 |
| T3 | 15 | 14 | 0 | 0 | 0 | 0 | 29.722 |

All scheduled jobs, including failures, timeouts and budget skips, remain in opportunity denominators.
Known usage is a subtotal when any usage is unknown; manifest reservations remain the billing bound.
A repair returning a package is observed behavior, not proof that the repair was correct. Rejection candidates are not confirmed errors.
Contract validation and handwritten context references are mechanical checks, not independent football accuracy or usefulness grades.
T3 is run once per case; model trials are repeated observations, not additional independent cases.
D3 removes review only inside this evaluation; production approval and validation stay required.
These developer-visible challenge compositions share existing trajectory backbones and current-play recordings.
They are not a blind final set or independent evidence of real-match accuracy.
No agent superiority, usefulness, human acceptance, or Grand Prize score is established.
Unknown usage retains its full reservation. Provider cancellation does not guarantee zero billing.
Use rating-instrument.csv with rating-packets.json; preserve blank ratings until real reviewers complete them.
Results and rating-mapping-private.json identify arms and must not be supplied to blinded raters.
