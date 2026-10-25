# Stronger synthetic football data for WHY/NOW

> SD01–SD04 follow-on: the [development dataset card](synthetic-dataset-v1.md)
> records the implemented first slice. The research below retains its original
> pre-implementation audit and recommendations.

25 October 2026, America/Lima. Research and read-only source audit; no new product
dataset or generator behavior is delivered by this document. Implementation is
specified in [the prioritized plan](next-iteration/synthetic-data-plan.md).

## Recommendation

Build a small, reproducible library of coherent football passages, with explicit
observation limits and a separate evaluation key. Improve the existing generator
and observation contract. Keep the current producer/viewer pipeline and two AI
roles. A complete game engine, video generation and trained trajectory model are
larger projects than this iteration needs.

The useful distinction is between **a plausible simulated world**, **what the
source has observed by a given time**, and **what an explanation may claim**.
An authored intention, true future outcome or hidden controller must not become
runtime evidence. Generated labels make a controlled test possible; they do not
establish real-match tactical truth or user usefulness.

## Why this matters to the contest

The challenge calls for football-realistic synthetic events across the five-stage
pipeline. Technical judging explicitly includes creative, optimized synthetic
data creation. The multi-agent category also asks for effective specialization,
handoffs and failure recovery, with a benefit over a single agent. Better scenes
can supply a fair test of that benefit; they cannot guarantee it. These are
direct requirements and opportunities in the
[official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md).

For WHY/NOW the potential demonstration is concrete: a quiet period stays quiet;
an observed change supports a concise explanation; incomplete evidence produces
a qualified result or abstention; a correction withdraws old text. The viewer
continues watching while the producer decides what deserves attention.

## What the repository actually contains

Inspected `simulator/match_coverage.py`, `matchday_demo.py`, `flagship.py`,
`live_match.py`, `validate.py`, the provenance manifests, the agent discovery
dataset and retained actual-model comparison.

| Existing capability | Evidence and remaining gap |
| --- | --- |
| Varied incident families | Authored passes, nearby-opponent changes, shots, goals, recoveries/control changes and possession intervals already exist. Adding those families again is not the next task. |
| Moving presentation fixture | `matchday_demo.py` uses authored paths, sinusoidal ambient movement, explicit controller intervals and scripted ball routes. Keeper positions are already near their own goals. They are not ball-responsive keeper behavior. |
| Pressure flagship | `flagship.py` patches player paths and event times to create comparison opportunities. The same protagonists and repeated pass structure limit diversity. |
| Delivery stress | `live_match.py` reflects the flagship and adds delayed shots, missing frames and retransmission. Useful robustness variants share the original trajectory ancestry. |
| Validation | Existing checks cover schema, clock, identities, control proximity, sampled speed, pass endpoints and correction lineage. They do not certify smooth acceleration, collision avoidance, keeper response, every shot/recovery alignment or a realistic event distribution. |
| Evaluation separation | Runtime exports exclude reference answers; developer cases identify shared ancestry. The final independent scenario/football review work remains open. |

The reproducible [audit](../evals/synthetic-research/current-fixtures.json) checks
the existing four exports ending `005`–`008`. All pass the existing validator.
Each represents 240 seconds; three have 2,401 tracking frames, and the deliberate
missing-frame variant has 2,399. Maximum sampled player speed is about 8.16 m/s.
Maximum vector finite-difference acceleration is about 103.54 m/s² in three
exports and 86.10 m/s² in the missing-frame variant. Those diagnostics expose
abrupt path joins; they are not calibrated physiological measurements. A mirror
repeats the same motion issue. Missing observations and rounding affect derivatives.

Reproduce without model calls or fixture mutation:

```sh
.venv313/bin/python evals/synthetic-research/audit.py
```

Passing the existing speed limit can therefore coexist with visibly abrupt
movement. Preserve that passing regression result and add a stricter validation
profile for new scenes. Do not rewrite old exports to improve this audit.

The earlier [actual-model discovery comparison](../evals/agentic/discovery-v4/README.md)
used 15 correlated cases and four approaches. Broad story choices matched and
the Reviewer requested no repairs. The current data may insufficiently exercise
the separation of responsibilities; the architecture may also add limited value
on those cases. Both remain possible. New data must not deliberately weaken the
single-agent baseline or encode the desired winner.

## Primary research and its practical implications

These sources support design choices, not a claim that WHY/NOW is validated.
Technical conclusions rely on governing bodies, maintainers or original research.

| Source, date and scope | What it supports | Decision for WHY/NOW; limit |
| --- | --- | --- |
| [IFAB Law 3, current 2026/27 page](https://www.theifab.com/laws/latest/the-players/) | The ordinary game has at most eleven players per side, including a goalkeeper. | Validate our declared 11v11 scenario roster and keeper roles. This slice excludes substitutions/dismissals; 22 is a scenario assumption, not an invariant for every real match. |
| [IFAB Law 10](https://www.theifab.com/laws/latest/determining-the-outcome-of-a-match/) | A goal requires the whole ball to cross the line in the goal opening, subject to offences. | Script physically consistent outcomes, but retain explicit source goal confirmation. A point at the goal-line centre does not independently prove a goal. Full refereeing is outside scope. |
| [FIFA: goalkeeper positioning, Tim Dittmer, January 2022](https://www.fifatrainingcentre.com/en/practice/elite-sessions/goalkeeper/in_and_out_of_possession.php) | Keeper position depends on possession, support angles, attacker location and shot angle. | Give keepers contextual support/shot-response paths. Do not pin them permanently to the goal line or treat leaving the penalty area as inherently invalid. Coaching guidance is not a universal positioning formula. |
| [FIFA: EPTS standard, June 2019](https://inside.fifa.com/en/innovation/news/new-global-standard-for-epts) | Tracking quality includes distance/velocity accuracy, test conditions, format and delivery delay. | Report separate structural, kinematic and delivery checks, with units and versions. These principles do not give our generator FIFA certification or authorize copying certification thresholds. |
| [FIFA: broadcast tracking validation, January 2021](https://ipt.fifa.com/innovation/news/assessing-the-quality-of-player-tracking-data-generated-using-broadcast-footage) | Visibility, video conditions and missing players affect validity; comparative validation differs from a gold standard. | Add explicit missing-player/ball intervals and distinct observed versus unknown possession. Do not convert an inferred hidden position into an observed position. We are not building a video tracker. |
| [FIFA Football Language: in possession, November 2021](https://www.fifatrainingcentre.com/en/resources-tools/football-language/in-possession/index.php) | Controlled possession can follow a reception, loose-ball collection, interception or restart. | Represent these distinct transitions in authored scenes. Preserve our existing family definitions and denominator rules; spatial closeness alone is insufficient evidence of recovery. |
| [Opta event definitions, current page](https://www.statsperform.com/opta-event-definitions/) | Shot, blocked attempt, recovery, possession and correction definitions have important distinctions. | Add saved/blocked/off-target/unresolved outcomes and recovery/control-change consistency checks within our contract. Provider conventions differ; do not silently redefine WHY/NOW to match Opta, or copy every field as authoritative. The page is not a substitute for current laws. |
| [Metrica Sports sample-data README](https://raw.githubusercontent.com/metrica-sports/sample-data/master/README.md) | Published examples synchronize tracking/events and document normalized coordinates and pitch dimensions. The samples are anonymized match data. | Adopt synchronization and explicit-unit discipline. Anonymized real data is not synthetic. No samples or trajectories were imported; redistribution/calibration would need separate terms review and declared provenance. |
| [Kloppy coordinate transformations, documentation v3.19.1](https://kloppy.pysport.org/user-guide/transformations/coordinates/) | Origin, axis orientation, dimensions and attack orientation must be explicit. | Keep metric coordinates and period direction separate. Mirror/direction tests are invariance checks and remain in the same dataset ancestry group. No new dependency is needed just to apply this principle. |
| [Google Research Football, June 2019](https://research.google/blog/introducing-google-research-football-a-novel-reinforcement-learning-environment/) | A physics-based environment and small scenario curriculum support reproducible football experiments. | Borrow scenario composition, state transitions and repeatable difficulty controls. RL playing agents solve a different problem from our explanation agents. This research does not validate our trajectories. |
| [Google Research Football repository](https://github.com/google-research/football) and [installation notes](https://raw.githubusercontent.com/google-research/football/master/README.md), inspected 25 October 2026 | The original repository is archived; local use involves native game-engine dependencies. | Do not switch the application to this simulator before the deadline. It can be a later adapter investigation. No claim that the linked successor or all other engines are archived. |
| [SoccerSynth-Detection, January 2025; revised October 2025](https://arxiv.org/abs/2501.09281) | Original research explores controlled variation and transfer testing for synthetic player-detection images. | Vary relevant conditions systematically and test outside development conditions. This is detection research, not evidence that generated event narratives or our multi-agent workflow transfer to real football. |
| [CheckList, ACL 2020](https://aclanthology.org/2020.acl-main.442/) | Behavioral capability matrices and controlled transformations find failures aggregate accuracy can hide. | Test invariance, evidence sensitivity and minimum supported behavior separately. This is a testing method, not a football realism score. |
| [Scikit-learn: grouped and time-aware evaluation](https://scikit-learn.org/stable/modules/cross_validation.html) | Correlated groups and ordered observations need appropriate separation to avoid misleading generalization estimates. | Split by authored trajectory ancestry before generating mirrors/noise/fault variants. Never count frames or transformed siblings as independent matches. This applies the principle; we are not training a classifier here. |
| [Datasheets for Datasets, Microsoft Research / CACM, December 2021](https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets/) | Document purpose, composition, creation and recommended uses. | Publish a concise dataset card, hashes, profile settings, ancestry, limitations and split membership. Public release remains a separate action. |
| [Anthropic: agent evaluations, January 2026](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Agent evaluations need outcomes and traces, repeated trials and complementary grading methods. | Reuse existing outcome accounting; measure useful output, reviewer interventions, false rejections, time and cost. Human judgment remains necessary for editorial usefulness. This vendor guidance supplies no score or numerical target for WHY/NOW. |

## What the other hackathon projects add

Firefox Developer Edition was accessible. The two existing project descriptions
below were reread on 25 October after resuming their site sessions. The web reader
could not fetch the Ninety Labs page; its description was read in Firefox.
No comments, ratings or messages were posted. These are advertised approaches,
not independently verified implementations.

- [The Ninety Labs](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126492)
  describes a seeded synthetic broadcast, a private event/position answer key,
  repeatable scoring and generation targeted at detector weaknesses. The useful
  lesson is explicit measurement and controlled hard cases. Its vision/footage
  pipeline is outside our current product. Its repository field showed no link;
  no working engine or accuracy claims were reproduced.
- [Pulse: Football Insights You Can Verify](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/126354)
  describes three authored fictional scenarios, synchronized statistics and
  inspectable evidence. Its page distinguishes the template browser prototype
  from model integration goals. That reinforces that fictional scenes and an
  interactive pitch are shared ground. Its runtime and realism were not tested.

Our proposed distinction is a **correction-aware editorial test library**:
the same observed situation can justify explaining, qualifying, remaining quiet
or withdrawing, with the result visible through producer and viewer workflows.
That is a proposed product emphasis, not an exclusive market claim.

## Synthesis: what to build, retain and defer

1. **Build:** smooth, role-aware movement and a shared episode state driving ball,
   actors and event outcomes. Allow support play, failed attacks and uneventful time.
2. **Build:** independently structured scene parents and paired context/availability
   cases. Every supported family must remain testable end to end.
3. **Build:** explicit world/observation/reference boundaries and stronger independent
   validation, including source-event/trajectory consistency.
4. **Retain:** delivery fault injection, immutable original exports, evidence and
   approval infrastructure, exact revisions and correction handling.
5. **Measure:** all comparison arms under fair constraints. Separate data realism,
   deterministic guard effectiveness, agent contribution, live timing and human value.
6. **Defer:** full-match physics, RL training, diffusion training, synthetic video,
   provider integration, xG and tactical-causation labels. None is needed to fix
   the identified data weaknesses.

A stronger dataset may reveal that both agent approaches already perform well,
that the Reviewer catches useful issues, or that it rejects useful stories too
often. All are valid findings. Data alone cannot add a missing agent capability.
If the agents only make a trivial yes/no choice on a family, difficult scenes may
require a separately justified workflow improvement before the role adds value.

## Evidence still missing

No real trajectories were imported, no new model calls were made, no full simulator
was installed and no product fixtures were regenerated. The audit is local and
read-only with respect to product data. Football reviewer agreement, Spanish
semantics, real-match representativeness, producer workload and viewer benefit
remain unestablished. The research does not raise a product score automatically.
The linked plan defines the next engineering work and separates participant work.
