# Incoming observation boundary

The current runtime accepts allowlisted observation-only replays (or their existing Event Hubs transport), not an arbitrary vendor feed. Metadata is immutable for a session: stable match/team/player IDs, 105 × 68 m coordinates, explicit period attack directions and a 10 Hz source in the shipped fixtures. Display names are not identities.

An adapter must validate `MatchMetadata` and each `OBSERVATION` before storage. Coordinates are metres, clocks milliseconds; converting another provider's normalized coordinates requires an explicit conversion before validation. Passing normalized numbers such as 0.5 directly is structurally valid metres and cannot be diagnosed from range validation alone. A declared units/scale adapter contract and independently authored vendor-format test remain T03 work; this document does not claim vendor integration.

Each pass requires stable `pass_id`, release and resolution events, explicit outcome, valid release/reception positions and verified controlling team/player. Tracking supplies possession intervals, nearby-opponent measurements and a continuity witness. Successful historical passes remain comparators even when they do not qualify as stories. Incomplete tracking or one-sided pass events disable comparative wording. The feed must be event-complete within its declared replay coverage: omission of both endpoints cannot be detected automatically.

Deliveries may reorder and retransmit exact IDs. Corrections use a new message ID, revision > 1, `supersedes_message_id`, occurrence clock and availability clock. They become visible only after availability and may change eligibility/population; no correction modifies an already approved package in place. At equal resolution times stable pass ID breaks ties. Different periods never share a comparison population.

Invalid envelopes are rejected with the contract's validation error. Unknown match IDs are not loaded. Generator plans, expected results and seeds stay outside runtime images and model tools. A production multi-vendor adapter requires a separately reviewed completeness and correction contract.

## Additive match-coverage event variants

The observation envelope remains 1.0.0; the additive schema export is
`observation-1.1.0.json`. New typed payloads: `shot_started` (shot_id, optional
location), `shot_resolved` (shot_id, typed outcome), `goal_status_changed`
(goal_id, status, nullable scorer, optional shot_id, explicit own_goal),
`ball_recovered` (incident_id, nullable previous team, typed explicit cause),
and `period_state_changed` (started/ended). See [definitions and examples](match-events.md).
New stable IDs are independent of message delivery IDs; correction lineages keep
logical event identity/occurrence, with a new message ID and availability cutoff.

Optional incident_id/pass_id on possession transitions links a recovery or pass
interception. Do not match by player proximity. Unknown outcomes/actors stay
unknown. A shot labelled goal is insufficient to score without confirmed goal
status. Source-confirmed state is public; explanatory packages need approval.

New sessions use immutable v5 packages. Saved v1–v4 text/hashes are never migrated
in place. Old binaries cannot read the additive event types/v5: isolate mixed
sessions or retain this compatible reader on rollback. Live Cosmos roundtrip and
real vendor adapters remain unverified; offline parity is not live Azure evidence.
