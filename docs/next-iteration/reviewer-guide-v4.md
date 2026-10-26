# Reviewer guide: MatchSense v4 discovery

Prepared 22 October 2026 (America/Lima). James will arrange participants. No reviewer observations have been collected yet.

## Materials and roles

Use `.run/agentic-v4-live-comparison/rating-packets.json` with `rating-instrument.csv` once that run finishes. Keep `rating-mapping-private.json`, `results.jsonl`, run reports and arm summaries away from raters until ratings are frozen. Case identifiers describe the shared task, not which architecture generated an output. Do not reveal the architecture during the session.

At least one reviewer should understand football and one should review Spanish meaning. Producers/analysts assess whether they would publish each output; casual viewers assess understanding. If a developer serves as a reviewer, record that role and report their observations separately from independent user research. Obtain consent before recording or quoting; keep personal information outside Git.

## Pilot, then freeze

Pilot one session and correct confusing instructions. Freeze the final task wording, reference answers, scene assignments and ratings before the final sessions. Counterbalance baseline/candidate order and use matched different scenes to reduce memorization. Discovery packets are formative; their cases are not an independently sealed final benchmark.

## Blind content review

For each packet, show the same available evidence, historical values and time window to each rater. Do not coach the intended angle. Ask:

1. What happened, and which player/team did what?
2. What changed in this passage compared with the prior play, if anything?
3. What does the evidence establish, and what does it not establish?
4. Would this explanation be useful to show? What substantive edit would you require?
5. If there is no output, was staying quiet appropriate?

Complete factual correctness, editorial usefulness, clarity, comparison-scope understanding, publishability and notes in the CSV. Leave unknown answers blank with an explanation; never replace missing ratings with a model estimate. A second rater independently checks all severe/suspicious cases and at least 25% of the rest. Retain disagreement before adjudication.

## Product interaction tasks

On the local candidate build, without instructions naming the control:

1. Find a specific approved passage and explain its primary change.
2. Inspect the current distance versus the three prior passes. Explain why a longer pass does not automatically imply a better tactical decision.
3. Switch to a receiver and distinguish reception from later team possession.
4. Open an earlier moment; recognize the selected evidence time versus live time; return to live.
5. Use Catch me up to find distinct developments and open a grouped member.
6. As a producer, choose an emphasis, inspect the exact new revision and approve it. Retract an older moment while preserving another approval.
7. As a Spanish reviewer, check actor roles, polarity, units, comparison denominator and evidence labels.

Collect task success, moderator help, errors, misconceptions and requested edits. Record clean task timing before retrospective think-aloud discussion. Record continuous-replay review timing separately from paused evidence inspection.

## Critical checks and reporting

A viewer must not infer a line break, chance creation, tactical superiority, receiver possession throughout the interval, or match-wide ranking from these measurements. Any interface-induced critical mistaken belief requires a fix and retest.

Report participant counts, expertise, actual task outcomes and examples. Separate successful output quality from all-opportunity coverage so abstentions/failures cannot inflate quality. Do not infer population-wide comprehension gains or broadcaster adoption from a small formative study.

Human findings are required before the architecture benefit and impact claims are reassessed. Use the implementation's measurements and the research protocol, not the desired 90+ score, to decide what to ship.
