# Research record and decisions

Reviewed 21 October 2026. Source claims below are deliberately narrow. The proposed architecture, thresholds and effort estimates are MatchSense design judgments, not conclusions validated by those sources.

## Primary-source findings

| Source | What it establishes | Decision for this iteration |
|---|---|---|
| [Microsoft official hackathon rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) | Grand Prize emphasizes complete, compelling, explainable football intelligence and personalized experiences. The rubric has five equally weighted criteria; technology is the first tie-break. | Prioritize useful explanation, audience distinction and measured end-to-end behavior. Use specialist-category fit as supporting evidence, not the product objective. |
| [Microsoft agent orchestration patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns/) | Sequential and concurrent coordination have different dependency, latency and resource tradeoffs. | Test the smallest role arrangement that performs the task; parallelize only independent work. A reviewer depends on the final proposed content. |
| [Microsoft Foundry agent evaluators](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators) | Agent assessment can cover outcomes and process, including tool selection/input/result use and task adherence. | Record both final usefulness and tool/decision behavior. Evaluate SDK/version support before using optional managed evaluators; do not claim they are already configured. |
| [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | More agentic complexity can trade latency and cost for task performance. | Require an ablation against a well-configured single agent and account for all attempts. |
| [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | Tasks, repeated trials, traces and actual outcomes are distinct evaluation objects; graders can be combined. | Keep repeated trials separate from independent examples, preserve failed traces, and combine deterministic checks with evidence-based human review. |
| [FIFA: pressure on the ball](https://www.fifatrainingcentre.com/en/fwc2022/efi-metrics/efi-metric--pressure-on-the-ball.php) | Pressure concerns an opponent closing space toward the ball carrier. | A radius count is only a proximity proxy. Use nearby-opponent wording; do not claim a proven press escape. |
| [FIFA: line breaks](https://www.fifatrainingcentre.com/en/fwc2022/efi-metrics/efi-metric--line-breaks.php) | Line-break meaning depends on opposition units. | Longitudinal opponent counts cannot establish a defensive line break. Defer unit detection and its independent validation. |
| [NN/g: usability testing](https://www.nngroup.com/articles/usability-testing-101/) | Relevant participants, neutral tasks and observed behavior reveal usability problems. | Run a small formative study for design decisions and comprehension, not market-size or revenue claims. |
| [NN/g: metrics in qualitative studies](https://www.nngroup.com/articles/metrics-qualitative/) | Small qualitative studies support concrete participant observations; aggregate rates can imply unwarranted population precision. | Report counts, individual paired observations, confusion and corrections. Do not advertise generalized time savings from a handful of participants. |

The official requirements include public GitHub source, a working video shorter than two minutes, suitable judging access and English materials or translations. Submission closes 27 October 2026 at 23:59 Pacific; judging access must last through 10 November at 23:59 Pacific. The repository/video are still pending at baseline. See the [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md) and [delivery schedule](README.md). Registration status must be confirmed by James.

## Research conclusions applied to the product

**The strongest differentiator to test is an inspectable explanation of observed change.** A viewer should see the pass, identify its actors and spatial change, understand what the evidence does and does not establish, and choose an appropriate level of detail. Existing publication controls support this, but do not by themselves prove usefulness.

**Add geometry before tactical interpretation.** Forward pass displacement and reception zone are available from existing fields. They offer more concrete information without introducing a trained model, real match data or unverifiable causal claims. The calculations and language require their own tests; they are not official FIFA implementations.

**Add context only when the history supports it.** A three-minute replay with repeated passes does not automatically provide useful contrast. New structural parents must include preceding events with varied geometry and outcomes. The model must not see parent labels or future events.

**Structured narrative selection can be meaningful agent work.** Choosing which supported facts answer “what changed?” and which ones suit a casual viewer is a decision. It becomes credible innovation when experiments show that the choice improves understanding and editorial acceptance. A larger role count is not evidence.

## Required research spikes before implementation decisions

| ID | Timebox | Question / method | Deliverable and stop rule | Owner |
|---|---:|---|---|---|
| R01a | 2 h | Audit every current claim's subject, time, unit and meaning; inspect English/Spanish receiver wording | Approved glossary, corrections and adversarial examples. Defer any tactical label lacking operational evidence. | Backend + football reviewer |
| R01b | 2 h | Count valid previous completed passes available at candidate cutoffs; examine same-team and period coverage | Context feasibility report. C03 stays conditional if no honest comparator can be supplied. | Data/evaluation engineer |
| R01c | 2–3 h | Compare current narration with supported claim-block prototypes on 8–12 discovery examples | Select an explanatory structure users can paraphrase; remove generic introductions. New drafts are prototypes, not results. | AI + product |
| R01d | 1–2 h | Pilot neutral producer/viewer tasks and check task wording | Frozen study instrument after pilot. Pilot participant is excluded from final comparison. | Product researcher |
| R01e | 1–2 h, conditional | Compare simple chronological vs transparent priority ordering on ten candidate pairs | N01 proceeds only if independently assessed usefulness improves; no ranking agent by default. | Product + QA |

Timeboxes are not additional to every backlog estimate: R01 includes a subset of these activities; user-study preparation and optional ranking investigation are included under U02/N01. Scheduling must avoid counting the same work twice.

## Claim vocabulary and candidate metrics

| Information | Permitted meaning | Prohibited extrapolation |
|---|---|---|
| Nearby opponents | Maximum count within a stated radius/window, with coverage | Sustained pressure, decision time, pressure probability |
| Longitudinal opponents passed | Release-time positions between start and reception in attacking direction | Players eliminated, defensive unit broken, tactical intent |
| Team retention | Passing team retains possession across the observed interval | Receiver individually holds the ball throughout |
| Forward pass displacement | Signed attacking-direction x displacement from release to successful reception | Pass difficulty, causal attacking value, post-reception distance |
| Reception zone | Observed endpoint in a defined normalized pitch third | Chance creation, a formal final-third-entry metric without a separate definition |
| Previous-pass contrast | Explicit comparison with the last three valid previous completed passes in the bounded same-team/period history | Best pass in the match, percentile, sustained control, confidence percentage |
| Player focus | Recorded passer/receiver role, observed trail, approved relevant history | Off-ball causality, credit inferred from proximity, future performance |

## Open decisions and defaults

- **Agent topology:** test Director + Reviewer first. Add separate composition only if evaluation supports it. Maintain the existing implementation as a historical comparison and rollback option.
- **Comparison sample:** last three same-team completed passes before the current release, within 120 s and the same period; otherwise insufficient history. This is an initial specification to freeze after R01b, not a scientifically calibrated football threshold.
- **Editorial selection:** transparent deterministic ordering with human override before any model ranking experiment.
- **Real-time mode:** optimize current candidate production first. A factual-first path is a conditional design with separate immutable versions and explicit producer choice.
- **Language:** English/Spanish only; names and units resolve from source claims, and semantic roles/polarity must match. Broader localization is deferred.
- **Model:** keep the existing deployment for the fair baseline. A model upgrade is a separate paired experiment if evidence warrants it; no capacity, price or compatibility is assumed.
- **Human evidence:** start recruitment immediately. Lack of participants reduces what may be claimed; it cannot be replaced with synthetic testimonials or an LLM pretending to be users.

## Sources intentionally not used as validation

The original concept brief's near-perfect concept scores, vendor engagement statistics, unrelated hackathon winners, and original synthetic labels do not establish MatchSense's impact or winning probability. Real football data is unnecessary for this iteration and would introduce licensing and data-semantic work. The research above informs bounded design decisions; product evaluation supplies the evidence for claims about this product.
