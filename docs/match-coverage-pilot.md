# Mixed-event formative pilot — instrument MC10.1

Status: materials prepared; recruitment, facilitator, reviewer ratings, findings
and retests pending. This is engineering preparation, not participant evidence.
James owns recruitment of 5–8 first-time viewers and 1–2 football-aware reviewers.
Assign a facilitator before scheduling. Include people who need plain football
language and record English/Spanish fluency. Review the definitions in
[match-events](match-events.md) with the football reviewer before freezing keys.

## Consent and assignment

Use the consent/opening script in [user-study](user-study.md). Store identifying
information and recordings privately, outside this repository. Obtain separate
permissions for recording, quotations and public screenshots. Anonymous IDs V01–V08
and P01–P02; participants can stop freely. No participant records exist yet.

Counterbalance AB/BA (alternate assignments, freeze before sessions). A is current
pass-only 0.5 baseline: original segment 01, session clock 25 s. B is the new
four-minute mixed replay, disposable local session. Give the same explanation of
navigation, language/focus and evidence controls in each arm. Do not coach football
answers. Record baseline information as absent rather than manufacture an event.
The scenes differ in content/length: this is a formative information-availability
comparison, not a controlled estimate of UI impact or time savings. Before a
quantitative comparison, freeze matched scenes and have the independent reviewer
validate both keys. Do not recruit until that limitation is accepted/recorded.

## Facilitator setup (keep answers private from participants)

Start `make coverage-dev`. Select Mixed-event discovery. Pause at these replay
checkpoints, inspecting and approving exact revisions:

| Replay checkpoint | Approve | Key |
|---|---|---|
| 25 s | pass 1 | forward displacement and subsequent team retention are separate |
| 33 s | loose-1 recovery | explicit loose-ball recovery, blue-08; later 3 s retention |
| 47 s | attempt-1 shot | saved; not a goal; source location only |
| 60 s | possession-60000 | interval 00:00–01:00; denominator excludes dead/loose/unknown |
| 105 s | goal-1 | source score 1–0; scorer from source; no assist/causal claim |

Freeze the exact possession values from the evidence pane in the session packet;
reviewer must independently integrate the delivered frames before ratings. Do not
use engineering output alone as the football answer key. Fixed snapshots stay
00:00–01:00 when the replay moves. The display is not full-match possession.

Prepare a separate correction session. Approve shot attempt-2 and goal-1 at 105 s;
advance to 136 s. Score is 0–0, old explanations disappear. Review and approve the
cancelled-shot replacement; a score correction does not wait for approval.
Never call replay jumps live latency. Include 20 s of normal uninterrupted play
with no new alert and ask about overload only after task completion.

## Viewer tasks (silent attempt, then retrospective)

1. Find the current score and period. Is the explanation already approved?
2. Find an unsuccessful attempt and describe its outcome. Did it score?
3. Find a change of control. Who is verified, and what remains unknown?
4. Find the approved possession interval. What time does it cover? What time is
   excluded from the percentage? Is it a whole-match statistic?
5. Find the evidence for an explanation, including its observation time.
6. Focus on the shooter/scorer, then an uninvolved player and each team. Explain
   the empty state without assuming missing evidence proves no real involvement.
7. Catch up after correction. Explain why the score changed and why a replacement
   narrative requires approval. Revisit an old approved moment without changing
   another viewer's live selection.

Record start/end times, exact answers, help requests/rescue, success/partial/failure,
critical score/outcome/approval misconceptions and wording issues. An answer of
“not available” is correct for an absent baseline family, but separately record
whether the requested football-information task could be completed. Never count
unavailable baseline tasks as evidence of a misleading participant.

## Producer/reviewer tasks

Review at least one story from each family in both languages where fluent. Inspect
sources; accept as useful and supported, reject, or request substantive editing.
Check goal versus shot, unknown scorer, own goal, cancellation, team-only change,
restart versus recovery and insufficient possession evidence. Use the deliberately
unsupported assist claim as a labelled challenge, never a spontaneous model error.
Observe approval, expiry, archive-only approval and retraction while recap is open.

## Empty observation form

| Anonymous ID | Arm/order | Task/family | Correct/help/rescue | Time | Exact misconception | Useful & supported / edit / reject | Follow-up |
|---|---|---|---|---|---|---|---|
| Pending | | | | | | | |

Capture build fingerprint, mode, session ID, time/checkpoint, viewport, language,
participant expertise, facilitator and answer-key version. Keep contact details out.

## Provisional decision gates

- >=80% viewer task attempts complete without rescue; publish raw numerator and
  denominator and unavailable-baseline tasks separately.
- Zero unresolved critical score, outcome or approval misconceptions.
- >=70% reviewed candidate stories accepted as useful and supported without
  substantive editing; show family/language counts and individual failures.

An external second reviewer adjudicates critical errors and at least 25% of other
ratings. Fix/retest critical failures before a user-facing release. Small convenience
samples do not establish broad football accuracy, commercial value or time savings.
Current participants: 0. Ratings: none. Findings: pending. Deployment: not authorized.

## Separate flagship extension (prepared; no findings)

The additive Pressure Swing scene and comprehension/reviewer tasks are in
[the flagship pilot addendum](pressure-flagship.md#pilot-addendum--pending-real-participants).
Freeze it as a separately labeled scene; do not silently substitute its changed
pass timing or possession values into the original mixed-event answer key.
