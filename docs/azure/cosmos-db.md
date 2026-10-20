# Cosmos DB for NoSQL persistence

**Status: specification only.** The local adapter is SQLite and is verified with one API worker. A transactional Cosmos adapter is not implemented yet.

Propose one account and a `whynow` database. Choose serverless versus provisioned throughput from the actual region, expected request rate and budget rather than assuming free capacity. Start with a single write region for the demo unless verified requirements justify more.

| Container | Partition key | Documents and retention |
|---|---|---|
| `session-state` | `/session_id` | Replay state/checkpoints, current generation, observed score and bounded state snapshots |
| `story-state` | `/session_id` | Immutable evidence/package revisions, current approval/publication, idempotency operations, audit records |
| `observations` (if cloud persistence requires it) | `/session_id` | Delivered immutable messages and corrections; canonical fixture files can remain shared read-only |

Keep the decision, operation key and current package pointers in the same `story-state` logical partition when a transaction must update them together. Use ETag/optimistic concurrency for stale approval protection and a transactional batch for atomic decision/audit/idempotency writes. A cross-container update is not implicitly atomic.

Document IDs include type/story/revision and are unique within a session. Exact retransmissions preserve IDs; corrections append a new revision with lineage. Evidence references observation IDs rather than duplicating tracking windows into every variant. Recaps cite exact approved story revisions and must be invalidated or selected fresh on retraction/supersession.

Set TTL intentionally for temporary snapshots, not for audit/evidence that must remain inspectable during judging. Define indexing around session/story/revision/time access; exclude large unused fields from indexing after measuring. No vector index or similarity search is required.

Configuration to add with the adapter: account endpoint, database/container names and managed identity. Grant narrow data-plane permissions to the API identity. Validate actual throughput, hot partitions, document sizes and retention in the deployed environment.

Official reference: [Cosmos DB partitioning](https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview). The proposed partition choices are application design decisions, not a claim of verified cloud performance.
