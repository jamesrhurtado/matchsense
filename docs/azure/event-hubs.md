# Event Hubs and replay checkpoint storage

**Status: specification only.** Local runtime observations are released from JSON Lines files by the replay clock. No namespace, hub, consumer or Azure checkpoint store exists for this project.

| Item | Proposed configuration |
|---|---|
| Namespace / hub | `whynow-events-<unique>` / `match-observations` |
| Tier / throughput | Smallest tier supporting the selected consumer and checkpoint requirements; confirm exact choice and pricing later |
| Partitions | Start with 2 for independent matches; verify tier limits and ordering needs |
| Partition key | Replay session or match session identity; all revisions of that session use the same key |
| Consumer group | `whynow-state` for the state engine; separate consumer groups only for actual independent consumers |
| Retention | Minimum supporting the demo/recovery window; verify the selected tier's supported retention |
| Checkpoint store | Small Storage account/Blob container for the chosen Event Hubs consumer SDK's checkpoint implementation |
| Authorization | Managed identity with Event Hubs Data Sender/Receiver as required; Blob permissions scoped to checkpoint storage |

The replay publisher controls release timing. Event Hubs provides transport; it does not interpret `available_at_ms` or implement the synthetic replay clock. Consumers still enforce schema, message IDs, exact deduplication, revision lineage, sequence tie-breaking and time-scoped queries.

Ordering is partition-scoped, not global. Persist processing checkpoint/state consistently enough to tolerate replayed messages. Publication is idempotent independently of transport delivery. Delayed outcomes cannot revive expired overlays. A reset has a new replay session/generation and does not mix with old checkpoint state.

Configuration to add with the adapter: namespace hostname, hub name, consumer group, checkpoint account/container, identity client ID and the runtime match/session partition key. No client-side secrets or connection strings are required in viewer code.

Verification: reconnect and duplicate delivery, late/corrected observations, replay generation isolation, crash between state write and checkpoint, safe restart, measured processing lag. [Official Event Hubs features and partition semantics](https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-features).
