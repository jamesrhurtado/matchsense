# WHY NOW reviewer session facilitator guide

## Purpose and distribution

### Live editorial iteration addendum — 25 October 2026

Use this instrument for the quieter live viewer, audience preview and interval
catch-up. Findings remain pending. Keep original R1 results separate; record the
build, execution mode and features enabled. Ask what participants think the product
does before explaining it.

Assign producers one task: choose a supported explanation worth sharing while
play continues, preview its audience versions, and approve or decline. Record
review time remaining, edits, expiry and reasons for declining. Declining a weak
story is not automatically failure. Ask whether their current tool does this better.

Ask viewers to watch normally, choose whether to open an explanation, and describe
what changed and what cannot be concluded. Record match action missed while
reading. After an absence, ask them to find approved explanations since their last
visit. Include a correction; check their understanding of current score and
withdrawn copy.

For paired comparisons, prepare equivalent synthetic intervals and a source-checked
factual timeline without suggested prose. Counterbalance baseline/candidate order;
avoid immediately repeating the same answer. An independent football reviewer must
check answer keys before grading. Those materials/key review and participant
assignments remain pending. The pitch alone is not a matched statistical baseline.

Add condition/order, assistance, paraphrase, unsupported interpretation, missed
match action and preference/reason to the existing task record. Report person-level
paired observations and counts. Repeated confusion in two sessions triggers a
revision; a critical score/publication misunderstanding blocks readiness claims.
Small samples do not establish market demand, retention or editorial savings.

Use this guide to run consistent individual sessions and turn observations into product changes. It contains expected behavior and study controls. Keep it with the facilitator; do not distribute it with participant handouts or anonymous output packets.

Instrument R1, 22 October 2026. These are blank instruments. No completed sessions, ratings or consent are implied. James coordinates recruitment and scheduling. This is a formative pilot, not a representative market study or a claim of multi-agent superiority.

## Recruit the right mix

- Football expert: one or two coaches, analysts, scouts or football journalists with practical evidence interpretation skills. Give manual 01.
- Producer: one or two sports producers, editors, commentators or content creators who decide what an audience should see. Give manual 02.
- Viewer: three or four casual and regular football viewers, including someone using a phone. Give manual 03.
- Spanish reviewer: at least one fluent Spanish speaker with football familiarity and sufficient English for comparison. Give manual 04. This role may overlap another, but do not count the person twice as an independent participant.

Prefer people who did not build the project. Record prior exposure and conflicts. An engineer can test mechanics, but that does not substitute for football judgment or viewer understanding. Record actual expertise rather than assuming a job title proves it.

## Plan the first round

Run one pilot to check task wording and logistics. Revise the instrument if needed, then freeze the product build, instructions, scenarios, rating definitions and answer keys for the remaining round. Retain pilot findings separately when the procedure changes. Do not give a product demonstration before tasks.

Use individual 30 to 45 minute sessions. People may attend on different days. If sessions run concurrently, each producer needs a separate disposable replay session and facilitator; do not let one participant change another's state. Group discussion is optional only after individual responses are saved.

## Before sending invitations

Fill these fields in a private session cover note for each participant:

Reviewer code and assigned role: _____________________________________

Date, start time, timezone and duration: ________________________________

Meeting or room and facilitator contact: _______________________________

Device, language and accessibility arrangements: _______________________

Manual to send and private return method: ______________________________

Send only the assigned manual. Keep private access credentials separate. Do not send the pitch, demo script, architecture comparison report, expected answers or other people's ratings. A participant may answer aloud while you transcribe if writing is difficult.

<!-- pagebreak -->

## Session preparation and opening

Verify the intended build and mode before the participant arrives. The last local candidate was v0.5 with schema 4; an older Azure build is not an equivalent test. Record commit or image identity, session ID, scene ID, language, device, viewport, replay clock and whether the replay is paused or continuous. Record the prompt and renderer version for model outputs. Never silently substitute a different build mid-round.

Create a disposable producer session and a matching viewer link. Prepare approved history and a supported unapproved candidate appropriate to the assigned tasks. Test access, sources, recap and retraction yourself in a separate rehearsal session. Do not require participants to supply an Azure account. Keep secrets out of recordings and forms.

For English usability testing, the contextual history A replay is a useful fixture. Follow docs/demo-script-v4.md for private setup, without using its persuasive narration. Have an independently checked answer key ready before testing. If a source cannot support a question, change the task before freezing it or mark that item unscorable.

## Permission record

Explain how responses will be used to improve the product. Specify the actual private storage location, who can access it, retention period and contact for withdrawal before asking permission. Agree on a withdrawal deadline before anonymized aggregation or public quotation. Do not promise deletion of material already published elsewhere.

Store permissions and contact details separately from coded response sheets, outside Git. Use your organization's approved consent process if one exists. Do not make recording a condition of participation.

Participation agreed: Yes / No    Date and time: _________________________

Screen or audio recording agreed: Yes / No / Not requested

Anonymized quotation allowed: Yes / No / Ask again for each quote

Public screenshots allowed: Yes / No / Ask again for each image

Storage, access, deletion date and withdrawal contact explained: Yes / No

If participation is declined, stop. If recording is declined, take notes. Obtain any separate public-use permission before publication, even if participation was agreed.

## Read this opening

“We are testing the explanations and interface, not you. The football data is synthetic. Honest criticism and uncertainty help us improve. Please try each task independently. You can ask for help or stop at any time. During timed tasks, work quietly; we will discuss your reasoning afterward. There is no preferred answer.”

Give one task at a time. Define unfamiliar controls only after recording that help was needed. Do not explain the intended football conclusion. Use neutral prompts such as “What did you expect?” or “What on the screen led you to that answer?”

<!-- pagebreak -->

## Keep the content comparison anonymous

Use the existing discovery material under .run/agentic-v4-live-comparison: rating-packets.json and rating-instrument.csv. Keep rating-mapping-private.json, raw traces, run reports and architecture labels away from reviewers. The preserved outputs use prompt v4.0; the current app uses v4.1. Record this distinction rather than presenting the old packets as fresh current-build outputs.

Prepare a readable packet for each assigned output with only its neutral output ID, the exact explanation and the permitted evidence. Do not hand reviewers raw JSON, file paths, generation-mode badges, token counts or timing information. Keep the original output IDs so responses can be mapped back after ratings are locked.

Source claims generated inside an output are not an independent answer key. Give all outputs for the same scene the same canonical observations or independently checked evidence display. Preserve missing output as an explicit No explanation provided entry. Do not silently repair, rewrite, translate or omit unfavorable outputs. If paired Spanish variants are needed, preserve their exact package and variant identities.

Select a small fixed batch before seeing participant reactions. For a 45-minute football session, start with four outputs for one scene; rotate scenes across participants and add a quiet or difficult scene only if time allows. This supports discovery, not a definitive architecture ranking. Producers can review a smaller disclosed subset before UI tasks; report that coverage separately.

Vary output order between reviewers using a saved balanced rotation; keep the mapping private. Rate each output independently before asking for a preference. Ties are valid. A participant who later sees the architecture is no longer blind for subsequent content ratings. Complete blind sections first.

## Record ratings consistently

Manual 01 defines factual support, usefulness and clarity from 1 to 5, with Cannot judge. Manual 02 records publishability and exact edits. Preserve these as distinct judgments; do not invent numerical ratings from a producer's unscored prose.

For the existing CSV, enter factual support into factual_correctness_1_5, usefulness into editorial_usefulness_1_5 and clarity into clarity_1_5. Publish unchanged maps to would_publish_yes_no = yes. Any required edit or rejection maps to no; Cannot judge stays blank with a reason. Save detailed edit categories in a companion coded record. Do not convert Reject and Cannot judge into the same outcome.

Record whether the reviewer actually understood a comparison from their paraphrase, against the frozen key. Use blank plus a reason when not applicable. For an absent output, leave content ratings blank and separately record withholding_appropriate_yes_no. Absence caused by a system error remains a system error even if quiet would have been acceptable.

Save a separate instrument file per reviewer; never overwrite the master or another person's answers. R1 adds explicit anchors; do not silently pool ratings from a different instrument. Lock original responses before revealing methods or adjudicating disagreements.

<!-- pagebreak -->

## Expected behavior and scoring boundaries

For contextual history A, match-57c134ad6e6457a4, Moment 4 at replay second 95 compares 30 m of forward displacement with the previous three completed passes of 8, 12 and 16 m in chronological order. A reverse-ordered display is also valid. Match-ace422836df75ecc has the same 30 m fourth pass and prior distances of 32, 34 and 36 m; the greater-than-each claim is not supported. These are constructed paired scenes, not independent real-match validation.

The statement establishes the comparison for those passes in that replay. It does not establish match-wide ranking, tactical superiority, chance creation or player intent. Verify actor names, actual receiver, team retention, event times and qualifications from the exact assigned evidence. Do not apply this numeric key to other scenes. Have a football reviewer check scene keys independently before using them to grade other participants; exclude that key author's judgments from a claimed blind comparison of the same scenes.

A successful viewer task means an accurate explanation or the intended action without step-by-step help. Earlier-moment selection changes personal inspection; Return to live restores the current selection. Viewing preferences select approved variants. A recap uses current approved stories, and can group similar moments. Merely locating a button does not demonstrate understanding.

A successful producer task means the intended exact revision is approved or withheld for a supported reason. Editing requires a new approval. Retracting one story removes that approval from history and recap while other approved stories remain. An expired overlay can still have approved history. Never force a participant to approve a story they reasonably reject; provide a fresh prepared session for later mechanics tasks and record the substitution.

## Observer record for each task

Reviewer code: ______  Task ID: ______  Scene and session: ________________

Build and language: ______________  Replay paused or continuous: _________

Outcome: Completed independently / Completed with help / Partial / Failed / Skipped

Skip or failure reason: Participant choice / System issue / Time limit / Other

Start and end on the same observer clock: __________  Duration: __________

Help given and when: ________________________________________________

Exact response or observation, with screen or claim reference:

____________________________________________________________________

Understanding: Correct / Partly correct / Incorrect / Cannot score

Serious mistaken belief or unintended publication: Yes / No / Needs review

Evidence and proposed issue: _________________________________________

Start timing when task instructions and the assigned screen are available; stop at the completed decision. Record help and interruptions. Use a predeclared four-minute limit per UI task after the pilot; record unfinished tasks, and continue discussion separately. Do not subtract server and browser clocks or label these observations end-to-end system latency.

<!-- pagebreak -->

## Close each session

Ask what should change first, what should be preserved and whether the participant would use the product in their actual context. Ask for a concrete reason. Offer one final chance to add uncertainty or correct a response; preserve the original and the revision separately. Confirm the private return method and any follow-up permission. Thank them without suggesting their answers should be positive.

## Turn observations into engineering work

Review responses after each session for urgent issues, but keep the remaining round consistent. If you must fix a serious issue, create a new build/instrument round and report the split. Do not hide earlier failures by replacing their results with retest results.

- Critical: unsupported central fact believed because of the interface, wrong actor/meaning, unintended publication, or stale/unapproved content shown as approved. Preserve evidence, investigate and retest before claiming that flow is ready.
- Major: a core task cannot be completed, requires intervention, or needs substantive content changes. Prioritize according to recurrence and impact.
- Minor: wording, layout or navigation friction without a material factual or control error.
- Preference: useful subjective feedback without a demonstrated failure. Preserve it without treating it as a correctness defect.

Have a second qualified reviewer independently assess all critical or suspicious cases and at least 25 percent of the remainder. Preserve disagreement before adjudication. Do not let an average score erase a serious error. Spanish issues changing actor, polarity, value or qualification require explicit resolution even if the prose sounds natural.

## Issue record

Issue ID and affected build: ___________________________________________

Observed problem and reproduction steps: ______________________________

____________________________________________________________________

Reviewer codes and evidence IDs: _____________________________________

Severity and reason: __________________________________________________

Expected behavior and source: _________________________________________

Owner and proposed change: __________________________________________

Retest task, reviewer and pass condition: _______________________________

## Report honestly

Report participant count, expertise, prior exposure, role overlap, scenario coverage and missing data. Give completed-without-help counts with denominators, substantive edits, withholding decisions, serious errors and individual task times. State paused versus continuous replay. Do not claim statistically established gains, market adoption or broadcaster time savings from this small sample.

Only unblind architecture after ratings are locked. Compare usefulness, acceptance, editing effort, failures and measured usage together. Current discovery has not demonstrated a two-agent advantage. Human findings may support keeping, simplifying or changing the workflow; none is a predetermined answer.

Store completed forms, mappings, consent and recordings outside the repository, in access-controlled research storage. Keep only blank templates and suitably anonymized approved summaries in Git. The manuals are ready; participant recruitment, scheduling, answer-key validation and completed ratings remain real work to perform.
