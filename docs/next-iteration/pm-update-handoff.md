# WHY/NOW — Contextual intelligence update: PM handoff

**Prepared:** 21 October 2026, America/Lima  
**Audience:** Product manager responsible for the [90+ improvement plan](grand-prize-90-plus-plan.md)  
**Implementation baseline:** `170e1c49ecedfb1bb8dce5604cd1d2c2c13e061d`  
**Implementation delivery:** three ordered commits on local `main`, listed below; documentation delivered separately  
**Release status:** implemented and verified locally; this update has not been deployed to Azure or pushed as part of this handoff

## 1. Outcome and scope

This update addresses the assessment's central product weakness: the application could describe a passage accurately but offered little previous-play context and often presented interchangeable stories. The candidate can now distinguish a supported historical contrast from an ordinary passage, expose the exact comparison evidence, and present more useful titles, player emphasis and recaps.

The implementation also improves mobile evidence access, producer editing, public agent decision summaries and delivery accounting. Existing approval authority and immutable approved revisions remain intact.

**This is a substantial implementation increment, not completion of every P0 release gate in the plan.** Human usefulness research, independent final evaluation, the paid architecture experiment and several operational requirements remain open. The supplied 76/100 assessment has not been replaced by a new score, and the 90+ target is not yet substantiated.

## 2. Changes delivered

| Area | Previous behavior | Behavior in this update |
|---|---|---|
| Historical context | The limited comparison tool always reported insufficient history | A bounded aggregate selects the previous three completed team passes and permits a precisely supported comparison |
| Agent choices | Angle was mostly metadata; titles were generic | Angle changes the lead, organization and factual title; historical contrast requires valid comparison evidence |
| Story identity | Similar moments looked interchangeable | Bilingual titles identify actors and measurements or reception location; duplicate names are disambiguated |
| Producer editing | Free-text editing could imply unrestricted copy control | Supported movement/reception/context emphasis produces a new exact proposal requiring approval; unsupported comparison requests are rejected |
| Player focus | General explanation with an appended role sentence | Passer views lead with verified release; receiver views lead with reception/location; later possession stays attributed to the team |
| Recap | Repeated approved moments could repeat paragraphs | A deterministic projection presents up to three distinct developments and groups similar approved moments with member links |
| Mobile evidence | Expanded history and detail could separate text from the pitch | Compact selected evidence sits with the explanation; history and fact details start collapsed |
| Explainability | Technical roles/actions were easier to inspect than editorial decisions | Producers see the selected angle/fact, context scope, reviewer repair and fallback before expandable technical details |
| Delivery accounting | Workflow completion and later acceptance were not fully distinguished | Append-only delivery events distinguish acceptance, stale discard, expiry, persistence failure and supersession |

### Historical comparison and correction safety

The comparison uses successful received passes from the same team and period, resolved strictly before the current release and within the preceding 120 seconds. The lower boundary is inclusive. Selection uses latest resolution time and stable pass ID for ties. Measurements are raw signed forward displacement in metres under the period's attack direction.

Only a current distance strictly greater than **each of all three** selected values supports comparative wording. Fewer than three passes, incomplete relevant history, equality or mixed results do not produce that claim. Incomplete history can still support a current-play explanation when the current evidence qualifies.

Context records contain comparator identities, release/reception times and coordinates, raw distances, source hashes, population dependencies and limitations. Tracking continuity is a conservative completeness witness; an upstream feed silently omitting both endpoints of a pass cannot be detected automatically. The comparison is explicitly limited to this replay and assumes an event-complete feed.

New package v3 binds current and historical evidence together. Corrections and late insertions can invalidate an affected approval, overlay and recap projection. Original packages remain immutable. Tests demonstrate withdrawal of a contextual story while preserving an unrelated approval. Stored v1/v2 packages retain their original text and hashes.

### Presentation and editorial workflow

The renderer creates English and Spanish variants from the same supported facts. Movement, reception and historical emphasis change the visible lead and title. Producers can select supported emphasis, inspect the resulting exact revision and approve it; an edit does not inherit the previous approval. Unsupported custom sentences are not copied into published text.

Viewer fact selection connects to a measured movement arrow, reception region, observed possession interval or the three-pass comparison table. Selected evidence and live replay clocks are labeled separately. Core audience controls are localized; complete evidence-detail localization remains open.

Recap filters approved revisions and verified focus before selection. A versioned signature uses predicates, actor/team IDs, comparison relation and defined measurement buckets. It retains grouped member IDs/revisions/times, exposes links and recomputes after withdrawal. Similarity does not create a trend claim. Expired approved moments are archival and do not revive the live overlay.

### Engineering and evaluation foundations

Subscription state, audience preferences, selected variant requests and rendering acknowledgments now have focused hooks. Evidence replay, audience controls, producer review and editorial summaries are separate components. Existing stale-response protections remain, and changed UI modules have a formatting check.

SQLite and Cosmos adapters support append-only lifecycle records alongside immutable workflow outcomes. Detected opportunities retain capacity deferral and never-scheduled expiry. The first approved-render acknowledgment per story revision validates session/story/revision/evidence identity and records a browser monotonic interval plus server receipt time. It grants no approval authority and does not prove reading or comprehension.

The existing evaluation harness now supports matched **T3** deterministic, **S3** single-agent and **M3** Director/Reviewer paths using the same v3 facts and renderer. Live execution requires explicit budgets, verified rate metadata and matching implementation/provider identifiers. Source-file fingerprints include new and uncommitted implementation files. No paid model comparison was executed in this update.

## 3. Product demonstration available to the PM

Two new catalogue entries, **Previous-pass history A** and **Previous-pass history B**, each contain five moments over 2.5 minutes. The catalogue now contains 173 observation-only replays; the original 168-case regression inputs remain unchanged.

1. Open either new replay in the producer console.
2. Jump to second **95** and select **Moment 4**.
3. Inspect the explanation and evidence, then approve the exact revision.
4. Open the viewer companion. Expand **Inspect the facts** and select the comparison sentence when present.
5. Explore player focus, approved history, recap and the phone layout.

The fourth passage has identical present-play payloads in A and B and advances the ball **30 m**. A's previous three completed passes advance **16, 12 and 8 m**; B's advance **36, 34 and 32 m**. A supports historical contrast; B uses a current-play explanation. These are developer discovery fixtures sharing a trajectory backbone, not independent football validation.

## 4. Verification evidence

These are the completed checks from this update. They establish engineering behavior within the tested scope, not human usefulness or production readiness.

| Check | Recorded result | Boundary |
|---|---|---|
| Backend suite | **301 passed** | Includes context boundaries, correction isolation, package compatibility, approval races, recap, delivery dispositions and acknowledgment identity |
| Local browser suite | **15 passed** | Producer/viewer flows, Spanish controls, selection races, recap/retraction, comparison evidence and five-moment mobile history; hosted/cloud checks excluded |
| Production web build and TypeScript | Passed | Local candidate build |
| Scoped UI formatting | Passed | Changed component/hook/API modules |
| Original synthetic regression | **168/168 cases; 594/594 checkpoints passed** | Baseline unchanged; zero model calls; inspected regression data |
| Candidate v3 JSON Schema | Resolves and validates a real package | Archived v1/v2 schema files preserved |
| Offline T3 harness | **12 outcomes: 11 packages, one appropriate abstention, zero failures** | Zero model calls; human ratings remain unset |
| Two continuous 1× streams | Both produced candidates with **29.800 s / 29.759 s** remaining before expiry | Local templates, same scripted parent, no automatic approval; not the planned operating-envelope study |

The two-stream scheduling-observed evidence-to-completion measurements were **12.018 ms** and **7.442 ms**. They exclude durable ingestion, human approval and browser rendering and must not be presented as end-to-end or live-model latency. Historical cloud misses remain in the earlier evidence record.

The eight added offline context variants share one current-play recording. Neither those variants nor repeated trials count as independent final parents. Injected repair challenges are explicitly labeled tests, not measured spontaneous model errors.

## 5. Plan coverage and remaining work

| Plan tickets | Delivered in this update | Remaining gate |
|---|---|---|
| A01 / T02 | Bounded context, v3 dependency binding and correction/compatibility tests | Football review; persistent reverse dependency index and retention policy |
| A02 | Consequential angles, evidence-gated comparison and independently recomputed reviewer context | Live behavioral evidence, relevance/false-rejection assessment and fuller explicit plan metadata |
| U01–U04 | Titles, emphasis editing, role-first views, distinct recap, mobile evidence and decision summaries | Human usefulness/Spanish review, broader accessibility audit and complete evidence-detail localization |
| T01 | Opportunity/delivery records, immutable usage/outcomes and approved-render acknowledgments | Exact durability/readiness timestamps; expected-but-never-detected accounting; crash-safe reconciliation; clock uncertainty work |
| T03 | Frontend separation, formatting and documented incoming-feed boundary | Lock profiling, further backend decomposition, declared-unit adapter and independently authored adapter test |
| A03 | Matched v3 experiment paths, provenance checks and offline smoke | Verified paid-run configuration, context/reviewer ablations, blinded ratings and architecture decision |
| I01 | Authored context challenges and paired playable replays | Structurally independent discovery parents, sealed 24-parent final benchmark and realism review |
| I02 | Working study surfaces and documented tasks/thresholds | Recruitment, pilot, frozen participant sessions and actual findings |
| I03 | Retained bounded local two-stream timing sample | At least 20 varied continuous opportunities, one/two-stream model/cloud measurements, recovery and cost report |
| C01 | Backend/API scenario coverage and browser demonstration of context with five moments | All three acceptance scenarios through complete producer/viewer browser flows and independent release review |

No broadcaster adoption, comprehension improvement, editorial time saving, multi-agent superiority or new category score is claimed. No additional agent, Azure service, tactical inference model or unrelated story family was introduced.

## 6. Ordered implementation commits

The update was uncommitted when the handoff check began. Its existing changes were then organized into these concern-based commits; the earlier verification results apply to their combined implementation tree. This avoids implying the implementation had already been committed in the previous work session.

| Order | Commit | Concern |
|---|---|---|
| 1 | `9afd879` | Contextual narratives, compatible v3 contracts, correction-safe publication and lifecycle accounting, with backend tests |
| 2 | `56ff86e` | Paired context replays, unchanged original regression inputs, matched v3 evaluation paths and recorded offline evidence |
| 3 | `c2778b0` | Audience evidence, mobile layout, producer controls, focused UI modules and browser checks |
| 4 | Documentation commit containing this handoff | README, metric/architecture definitions, delivery status, validation limits and PM handoff |

The offline manifest records the original Git base plus hashes of the tested source files. It is preserved as run evidence rather than rewritten to pretend the evaluation ran after these commits. Publication/pushing and a new Azure rollout are separate from this local handoff.

## 7. Recommended PM follow-up

1. Review the A/B demonstration and confirm whether the supported comparison answers a useful producer/viewer question.
2. Arrange football and Spanish review plus producer/viewer participants. Use the prepared study instrument and freeze answer keys and thresholds before final sessions.
3. Complete the remaining accounting, dependency-index and operational requirements before a production-readiness claim.
4. Finalize independent scenarios and a concrete bounded paid evaluation configuration. Run blinded T3/S3/M3 comparison and ablations; retain the simplest passing architecture if collaboration provides no demonstrated benefit.
5. Reassess the product against the five categories only after those findings exist. Record actual scores and limitations rather than copying the plan's targets.

## 8. Supporting repository records

- [Original improvement plan](grand-prize-90-plus-plan.md)
- [Ticket-level implementation and verification record](decision-log.md)
- [Metric, context and recap contracts](../metrics.md)
- [Architecture and compatibility decisions](../architecture.md)
- [Incoming-feed boundary](../incoming-feed.md)
- [Runtime measurements and incomplete operational gates](../runtime-performance.md)
- [Product validation status](../product-validation.md) and [study instrument](../user-study.md)
- [Score reassessment limits](../product-score-reassessment.md)
- [Agent evaluation report](../../evals/agentic/REPORT.md), [candidate manifest](../../evals/agentic/context-smoke/manifest.json) and [output summaries](../../evals/agentic/context-smoke/summary.json)
