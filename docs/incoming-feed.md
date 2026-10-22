# Incoming observation boundary

The current runtime accepts allowlisted observation-only replays (or their existing Event Hubs transport), not an arbitrary vendor feed. Metadata is immutable for a session: stable match/team/player IDs, 105 × 68 m coordinates, explicit period attack directions and a 10 Hz source in the shipped fixtures. Display names are not identities.

An adapter must validate `MatchMetadata` and each `OBSERVATION` before storage. Coordinates are metres, clocks milliseconds; converting another provider's normalized coordinates requires an explicit conversion before validation. Passing normalized numbers such as 0.5 directly is structurally valid metres and cannot be diagnosed from range validation alone. A declared units/scale adapter contract and independently authored vendor-format test remain T03 work; this document does not claim vendor integration.

Each pass requires stable `pass_id`, release and resolution events, explicit outcome, valid release/reception positions and verified controlling team/player. Tracking supplies possession intervals, nearby-opponent measurements and a continuity witness. Successful historical passes remain comparators even when they do not qualify as stories. Incomplete tracking or one-sided pass events disable comparative wording. The feed must be event-complete within its declared replay coverage: omission of both endpoints cannot be detected automatically.

Deliveries may reorder and retransmit exact IDs. Corrections use a new message ID, revision > 1, `supersedes_message_id`, occurrence clock and availability clock. They become visible only after availability and may change eligibility/population; no correction modifies an already approved package in place. At equal resolution times stable pass ID breaks ties. Different periods never share a comparison population.

Invalid envelopes are rejected with the contract's validation error. Unknown match IDs are not loaded. Generator plans, expected results and seeds stay outside runtime images and model tools. A production multi-vendor adapter requires a separately reviewed completeness and correction contract.
