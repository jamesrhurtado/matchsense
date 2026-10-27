# Stronger synthetic football data for MatchSense

> SD01–SD04 follow-on: the [development dataset card](synthetic-dataset-v1.md)
> records the implemented first slice. The audit below retains historical findings;
> the hackathon recommendations at the end reflect the current submission scope.

25 October 2026, America/Lima. Research and read-only source audit; no new product
dataset or generator behavior is delivered by this document. Implementation is
specified in [the prioritized plan](next-iteration/synthetic-data-plan.md).

## Recommendation

For this hackathon, use a small, reproducible set of coherent football passages,
with explicit observation limits and separately stored expected answers. Keep the
judge-facing presentation fixture distinct from development/regression material.
A complete game engine, video generation and trained trajectory model are larger
projects than this submission needs.

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

For MatchSense the potential demonstration is concrete: a quiet period stays quiet;
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
| Evaluation separation | Runtime exports exclude reference answers; developer cases identify shared ancestry. Automated checks do not establish broad real-match representativeness. |

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

These sources support design choices, not a claim that MatchSense is validated.
Technical conclusions rely on governing bodies, maintainers or original research.

| Source, date and scope | What it supports | Decision for MatchSense; limit |
| --- | --- | --- |
| [IFAB Law 3, current 2026/27 page](https://www.theifab.com/laws/latest/the-players/) | The ordinary game has at most eleven players per side, including a goalkeeper. | Validate our declared 11v11 scenario roster and keeper roles. This slice excludes substitutions/dismissals; 22 is a scenario assumption, not an invariant for every real match. |
| [IFAB Law 10](https://www.theifab.com/laws/latest/determining-the-outcome-of-a-match/) | A goal requires the whole ball to cross the line in the goal opening, subject to offences. | Script physically consistent outcomes, but retain explicit source goal confirmation. A point at the goal-line centre does not independently prove a goal. Full refereeing is outside scope. |
| [FIFA: goalkeeper positioning, Tim Dittmer, January 2022](https://www.fifatrainingcentre.com/en/practice/elite-sessions/goalkeeper/in_and_out_of_possession.php) | Keeper position depends on possession, support angles, attacker location and shot angle. | Give keepers contextual support/shot-response paths. Do not pin them permanently to the goal line or treat leaving the penalty area as inherently invalid. Coaching guidance is not a universal positioning formula. |
| [FIFA: EPTS standard, June 2019](https://inside.fifa.com/en/innovation/news/new-global-standard-for-epts) | Tracking quality includes distance/velocity accuracy, test conditions, format and delivery delay. | Report separate structural, kinematic and delivery checks, with units and versions. These principles do not give our generator FIFA certification or authorize copying certification thresholds. |
| [FIFA: broadcast tracking validation, January 2021](https://ipt.fifa.com/innovation/news/assessing-the-quality-of-player-tracking-data-generated-using-broadcast-footage) | Visibility, video conditions and missing players affect validity; comparative validation differs from a gold standard. | Add explicit missing-player/ball intervals and distinct observed versus unknown possession. Do not convert an inferred hidden position into an observed position. We are not building a video tracker. |
| [FIFA Football Language: in possession, November 2021](https://www.fifatrainingcentre.com/en/resources-tools/football-language/in-possession/index.php) | Controlled possession can follow a reception, loose-ball collection, interception or restart. | Represent these distinct transitions in authored scenes. Preserve our existing family definitions and denominator rules; spatial closeness alone is insufficient evidence of recovery. |
| [Opta event definitions, current page](https://www.statsperform.com/opta-event-definitions/) | Shot, blocked attempt, recovery, possession and correction definitions have important distinctions. | Add saved/blocked/off-target/unresolved outcomes and recovery/control-change consistency checks within our contract. Provider conventions differ; do not silently redefine MatchSense to match Opta, or copy every field as authoritative. The page is not a substitute for current laws. |
| [Metrica Sports sample-data README](https://raw.githubusercontent.com/metrica-sports/sample-data/master/README.md) | Published examples synchronize tracking/events and document normalized coordinates and pitch dimensions. The samples are anonymized match data. | Adopt synchronization and explicit-unit discipline. Anonymized real data is not synthetic. No samples or trajectories were imported; redistribution/calibration would need separate terms review and declared provenance. |
| [Kloppy coordinate transformations, documentation v3.19.1](https://kloppy.pysport.org/user-guide/transformations/coordinates/) | Origin, axis orientation, dimensions and attack orientation must be explicit. | Keep metric coordinates and period direction separate. Mirror/direction tests are invariance checks and remain in the same dataset ancestry group. No new dependency is needed just to apply this principle. |
| [Google Research Football, June 2019](https://research.google/blog/introducing-google-research-football-a-novel-reinforcement-learning-environment/) | A physics-based environment and small scenario curriculum support reproducible football experiments. | Borrow scenario composition, state transitions and repeatable difficulty controls. RL playing agents solve a different problem from our explanation agents. This research does not validate our trajectories. |
| [Google Research Football repository](https://github.com/google-research/football) and [installation notes](https://raw.githubusercontent.com/google-research/football/master/README.md), inspected 25 October 2026 | The original repository is archived; local use involves native game-engine dependencies. | Do not switch the application to this simulator before the deadline. It can be a later adapter investigation. No claim that the linked successor or all other engines are archived. |
| [SoccerSynth-Detection, January 2025; revised October 2025](https://arxiv.org/abs/2501.09281) | Original research explores controlled variation and transfer testing for synthetic player-detection images. | Vary relevant conditions systematically and test outside development conditions. This is detection research, not evidence that generated event narratives or our multi-agent workflow transfer to real football. |
| [CheckList, ACL 2020](https://aclanthology.org/2020.acl-main.442/) | Behavioral capability matrices and controlled transformations find failures aggregate accuracy can hide. | Test invariance, evidence sensitivity and minimum supported behavior separately. This is a testing method, not a football realism score. |
| [Scikit-learn: grouped and time-aware evaluation](https://scikit-learn.org/stable/modules/cross_validation.html) | Correlated groups and ordered observations need appropriate separation to avoid misleading generalization estimates. | Split by authored trajectory ancestry before generating mirrors/noise/fault variants. Never count frames or transformed siblings as independent matches. This applies the principle; we are not training a classifier here. |
| [Datasheets for Datasets, Microsoft Research / CACM, December 2021](https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets/) | Document purpose, composition, creation and recommended uses. | Publish a concise dataset card, hashes, profile settings, ancestry, limitations and split membership. Public release remains a separate action. |
| [Anthropic: agent evaluations, January 2026](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Agent evaluations need outcomes and traces, repeated trials and complementary grading methods. | Useful context for later agent comparisons; beyond the synthetic-data claim for this hackathon submission. This vendor guidance supplies no score or numerical target for MatchSense. |

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

## Synthesis: hackathon scope

The repo already implements the high-value data practices for this submission:
authored movement and event state, shared ball/control logic, declared coordinate
and sampling conventions, paired evidence/correction examples, deterministic
generation, runtime/reference separation and hashed provenance. The one-minute
presentation fixture is separate from the larger opt-in development slice.

The remaining practical improvements are to make the demo's realism limits easy to
understand, surface a compact quality report by layer, and showcase a couple of
existing controlled pairs. These actions are documented in
[`synthetic-submission.md`](synthetic-submission.md). Do not add another test-data
catalogue or claim full-match realism for the hackathon. Keep the existing broader
regression infrastructure for later engineering use.

Defer full-match physics, RL training, diffusion training, synthetic video,
provider integration, xG and tactical-causation labels. None is needed to show how
evidence-supported stories, uncertainty and corrections work in this product.

## Evidence still missing

No real trajectories were imported, no new model calls were made, no full simulator
was installed and no product fixtures were regenerated during this research review.
The audit is local and read-only with respect to product data. Synthetic scene
checks establish correspondence to authored construction rules; they do not
establish real-match representativeness, producer workload or viewer benefit. The
linked plan defines broader later engineering work and is not the hackathon data
deliverable.

## 27 October 2026 — standards crosswalk and submission review

This addendum reconciles the earlier source audit with the current repository and
the hackathon's published requirements. The official rules require synthetic,
football-realistic data, identify synthetic-data creation as a technology-judging
question, and describe a five-stage path from event ingestion through personalized
presentation. They do not require ISO certification, a statistical population
simulator, differential privacy, or real match data. The Microsoft Reactor
challenge description independently emphasizes explainable match intelligence
from synthetic events. The Innovation Studio About/rubric page redirected to
Microsoft sign-in in this review; the locally recorded page review and exact
20%-each rubric are in [problem evidence](problem-evidence.md#contest-fit-and-delivery-constraints).

### Standards and research mapped to this project

| Guidance | Useful practice | MatchSense application and boundary |
| --- | --- | --- |
| [ISO/IEC 5259-1:2024](https://www.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/08/10/81088.html?browse=tc), [5259-2:2024](https://www.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/08/18/81860.html?browse=tc), and [5259-3:2024](https://www.iso.org/standard/81092.html) | Define fit-for-purpose data-quality objectives, measures and lifecycle ownership rather than treating a schema pass as overall quality. | Report separate, relevant layers: provenance, movement/geometry, source/event coherence and demonstrated behavior. This is a voluntary design crosswalk, not a claim of ISO conformance. |
| [NASA-STD-7009B](https://standards.nasa.gov/standard/NASA/NASA-STD-7009?trk=article-ssr-frontend-pulse_little-text-block) | Distinguishes model verification (matches specification) from validation for an intended real-world use, and asks that unverified aspects be recorded. | Our checks verify authored construction choices. State plainly that they do not establish real-match representativeness. NASA guidance is an analogy, not a required or claimed certification for a football hackathon demo. |
| [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10) and [AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) | Document data selection, suitability and representativeness in relation to intended use. | State that these original scripted scenes are for demonstrating evidence-sensitive storytelling, not learning or measuring general football behavior. |
| [NIST SP 800-226](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-226.pdf) | Synthetic records can retain utility problems and can leak source records unless privacy is evaluated; synthetic does not mean private by default. | Current coordinates and identities are authored fiction, so differential privacy is not the relevant improvement. If real tracking is later used to estimate or tune a generator, review rights and privacy before release and quantify privacy where needed. |
| [Datasheets for Datasets](https://doi.org/10.48550/ARXIV.1803.09010) | Document purpose, composition, creation, recommended uses, limitations and maintenance for each version. | The v1 dataset card and v2 guide already do much of this. Make the submission's demo/evaluation/legacy profiles explicit and state their counts, ancestry and non-claims together. |
| [W3C PROV overview](https://www.w3.org/TR/prov-overview/) | Represent source entities, generation activities, derivations, versions and responsibility so results can be traced and reproduced. | Existing generator IDs, manifests, ancestry hashes and stream hashes are a strong start. Add a compact machine-readable manifest that ties each runtime fixture to generator version/configuration, parent, transformation, profile and validator report. |
| [NIST SDNist](https://www.nist.gov/services-resources/software/sdnist-synthetic-data-report-tool) | Report utility and privacy separately; one aggregate “quality” score can conceal trade-offs. | Use task-specific football checks and scenario coverage, not tabular distribution scores as a stand-in for football realism. Its privacy measures do not directly fit fully authored fictional trajectories. |

### Current state: strengths and limits

The repository has substantial engineering work behind the hackathon demo: the
168-case suite has explicit families, deterministic generation, six ancestry
parents, grouped variants, observation-only runtime exports, separate expected
answers, hashes and per-checkpoint reports. Its fixed regression now reports
168/168 cases and 594/594 checkpoints. The separate vNext slice uses six authored
development scenes, twelve paired specifications and 24 source views; it adds
shared ball/control/event state, 10 Hz metric coordinates, smooth bounded paths,
missing/unknown evidence, corrections, shot/goal/recovery cases, source-only
validation and a dataset card. The new short presentation replay is versioned and
preserves the original fixtures.

These counts answer whether the implementation satisfies its authored checks,
not whether it represents real football. The 168 cases share six parent
configurations; adjacent frames, delivery variants, mirrors and repeated checkpoints
are not independent matches. The six-scene constrained slice is development
material. `simulator.validate` acceptance is not an endorsement of tactics. The
older four-minute exports pass legacy sampled-speed checks while the independent
audit finds path-join acceleration spikes up to about 103.54 m/s²; the newer
constrained profile has much smoother measured derivatives, but its bounds are
design choices rather than calibrated human or FIFA limits. Some legacy/grid
fixtures give keeper roles without plausible keeper paths; label those as
regression material and use the separate versioned replay for presentation.

### Hackathon recommendations

1. Keep the one-minute presentation fixture separate from development/regression
   data; label it synthetic and describe it as an authored excerpt.
2. Put the shared-state recipe, coordinates, sampling, movement profile, provenance
   and limitations in the submission. Do not imply a full-match simulator.
3. Show two existing paired examples: the missing-opponent support passage and the
   confirmed-then-cancelled goal. Explain the one meaningful change in each pair.
4. Report the small, relevant checks by layer: provenance, movement/geometry,
   source/event coherence and authored task behavior. Name profile thresholds as
   design choices; do not collapse them into a realism score.
5. Leave further test catalogs, large-scale evaluation programs and model comparison
   studies for later. The current submission's claim is that these authored scenes
   reproducibly demonstrate the product's evidence and correction workflow.

The copy-ready account and current measurements are in
[`synthetic-submission.md`](synthetic-submission.md).
