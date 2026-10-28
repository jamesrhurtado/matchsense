# Match events v1 (MC01)

Engineering owner: Codex in this delivery. Product/recruitment owner: James.
Football and Spanish reviewers/facilitator: unassigned; independent review pending.
These are product definitions, not football significance standards.

Time: timeline_ms is replay navigation; period_elapsed_ms is the source clock.
Availability gates every projection. Processing wall time is separate. Period
starts/ends explicitly stop the match clock; otherwise advance the latest source
clock only while the observed period is running. Initial metadata supplies score.

Public clock/period/confirmed score is source state, never editorial approval.
Pending goals do not score; cancelled goals remove their contribution. Latest
available revision per stable goal ID wins deterministically, even if deliveries
repeat or reorder. Own goal scorer can belong to the other team. No inferred
scorer, assist, save, recovery, cause or goal from coordinates. Shots use goal,
saved, blocked, off_target, unknown. A shot outcome requires its resolution;
goal wording and score additionally require a confirmed goal observation.

Match observation schema 1.1.0 adds optional `body_part` and `play_type` fields
to shot-start details. The flagship synthetic fixture supplies authored values
for its first two located shots; these are synthetic source details, not facts
inferred from video or tracking. The live illustrative xG estimate abstains
when location, body part, play type or complete nearby tracking is missing.

Possession: fixed trailing 60 s windows ending at 15 s replay boundaries. Clip to
segment/period, including an explicitly observed period end. Integrate left frame state over [frame, next frame), only if next
frame is at most 200 ms away in the same period. No extrapolation after last
frame. controlled/in_flight with declared known team assign time; loose and
out_of_play are separate. Everything else, including missing in-play state and
gaps, is unknown. Coverage = assigned/(assigned+unknown); team shares use assigned
only. Dead/loose excluded from both. Percentages require >=30 s assigned and
>=95% coverage. Always show interval, denominator, excluded durations, coverage.
Never silently advance an approved snapshot. Corrections invalidate its revision.

Control: possession_changed with distinct non-null old/new teams is a team change.
A null previous team is a restart/loose acquisition, labelled explicitly. Only
ball_recovered attributes recovery/cause (tackle/interception/loose_ball/unknown).
Source incident_id links transition and recovery; linked pass_id deduplicates
interception. No guessed matching by proximity. Three continuous seconds with
same team, >=95% time coverage and <=200 ms gaps supports later retention;
immediate loss removes only that optional clause. Ordinary restart never implies
recovery. Unknown players remain unknown.

Publication: v5 event-neutral packages alongside immutable v1–v4 passes. Shot,
goal, recovery/change stories live 30 s from evidence readiness. Possession lives
until its next boundary (or evidence readiness if late); archive approval adds
history only. Exact revision/hash approval required; corrections revoke affected
approvals. Linked shot/goal use one incident in viewer history/overlay/recap, with
source details retained. Confirmation never upgrades previously approved prose.
Queue priority: goal, shot, recovery, possession, pass; newest occurrence then
stable ID within each family. One overlay; inspectable reason and manual selection.
Only latest unreviewed possession stays active; older snapshots remain archived
with disposition. Recap: up to five incidents, goals first then family round robin;
latest possession snapshot; chronological display, count/link to complete history.

## Reference acceptance examples (engineering authored; reviewer pending)

| Family | Positive 1 | Positive 2 | Negative 1 | Negative 2 | Correction |
|---|---|---|---|---|---|
| State/goal | confirmed blue adds one | own goal unknown scorer adds scoring team | pending adds zero | shot goal alone adds zero | cancel removes one; team edit moves contribution |
| Shot | saved source says saved | off_target source says off target | start hides outcome | absent resolution gives no outcome card | saved -> blocked replaces approval |
| Possession | 40 s blue/20 amber = 66.7/33.3 | in-flight team time assigned | 29 s assigned withholds | 4 s gaps in 60 s withholds | corrected frame changes hash/share |
| Control/recovery | explicit loose recovery names player | team A -> B names teams only | restart is not recovery | nearby defender is not tackler | corrected player invalidates only incident |
| Pass | original segment 01 eligible | retained onward control names receiver separately | missing retention abstains | interception not reception | existing source revision invalidates |

## Compatibility and rollback

| Stored package | Reader | Mutation policy |
|---|---|---|
| v1–v4 | original reader/renderer | unchanged bytes/text/hash |
| v5 | event schema/renderer plus shared repositories | append revision, never rewrite |
| Unknown version | reject | no reinterpretation |

Observation envelopes and match metadata accept 1.0.0 and 1.1.0. Old binaries
cannot ingest the 1.1.0 shot details, new event variants or v5. Flag
WHY_NOW_MATCH_COVERAGE is off by default; enable disposable local pilot sessions
explicitly. Rollback must keep this compatible reader or isolate new sessions
from old builds. SQLite and Cosmos use their existing immutable package/atomic
decision adapters; no new infrastructure. Live Cosmos and model-specific
validation remain separate gates.

## Additive v6 Pressure Swing

[Definition, source gates and limits](pressure-flagship.md#exactly-what-the-measure-means).
Schema 6 uses the event-package reader/repositories and the `pressure-swing-v6`
renderer. Schema 1–5 readers and persisted bytes/hashes remain valid. Pressure
appears only in the new flagship fixtures, behind the existing coverage flag;
existing sessions retain their persisted coverage capability on flag rollback.
A source correction invalidates the exact approval; re-rendering is a new revision.
Pressure and ordinary pass stories share an incident in viewer history/recap.

## Additive v7 pressure wording

New pressure packages use schema 7 and the `pressure-swing-v7` renderer. The
analyst view reads as a short explanation of the pass, names players with their
shirt numbers, states the before/after windows and observed coverage, and gives
the measurement boundary. Older v6 pressure packages keep their original text,
hash and reader; the v7 reader accepts both versions without rewriting stored
approvals.
