# Architecture and decisions

The producer and viewer share one replay session. Observation availability, deterministic calculations, publication and viewer selection are separate responsibilities. Local mode uses templates and SQLite; the hosted engineering build adds Foundry model roles, Event Hubs, Cosmos and managed identities. See [Azure resources](azure/README.md) and [QA results](qa.md).

```mermaid
flowchart LR
  F[Synthetic runtime fixtures] --> R[Replay clock publisher]
  R --> H[Event Hubs]
  H --> D[(Durable Cosmos observations)]
  D --> C[Available evidence cutoff]
  C --> M[Deterministic eligibility and metrics]
  M --> A[Agent Framework analyst]
  A --> V[Reviewer with bounded evidence tools]
  V --> E[Audience editor and validation]
  E --> S[(Immutable package and audit)]
  S --> P[Producer approves exact revision and hash]
  P --> O[Timed shared overlay]
  P --> W[Viewer variants and recap]
  C --> L[Live pitch and evidence replay]
```

## Decisions

- Next.js App Router, TypeScript and original SVG pitch; FastAPI/Pydantic for the API and contracts. Tested versions are pinned, with the npm lockfile and complete Python dependency pins.
- Replay is a wall-clock-to-synthetic-clock mapping stored in SQLite locally and Cosmos in Azure. It releases observations by `available_at_ms`; read tools cannot expand their bound cutoff. Reset creates a new session rather than rewinding approvals.
- A public observation-only catalogue allowlists 171 replays: the original three and 168 expanded cases. Additional streams use deterministic gzip compression. Replay duration follows the selected segment, including 90 s and 180 s sequences. Protected forward jumps pause the replay and release observations through the requested clock; backward navigation requires a new session.
- Source observations are immutable runtime files. Delivered correction messages replace earlier revisions in projections. Source IDs and the contents of all operands contribute to an evidence hash. Canonical hashing treats integral JSON floats and integers equally because Cosmos may serialize `1.0` as `1`; strings, nonintegral values, array order and fields remain significant; changed evidence supersedes current approval.
- Metrics check complete opponent coverage in the trailing window and continuity throughout retention. A receiving outcome alone is insufficient. Evidence coverage and limitations are visible.
- Story packages are immutable SQLite rows locally and Cosmos documents in Azure. Edits create a new package revision, run a single bounded wording review, and invalidate approval. Review requests use the revision/hash actually shown to the producer. Retries use a session-scoped operation ID and request hash.
- Each delivered pass has a separate investigation, `story-<pass-id>` identity, revision stream and editorial decision. Evidence tools bind the selected pass as well as the cutoff. A new pass never supersedes another pass's approval. Corrections invalidate only affected stories. New SQLite tables and Cosmos story pointers preserve legacy single-story records without destructive migration.
- The producer selects reviewed moments independently. Viewers select approved history while the shared overlay remains the latest eligible approved moment. `approved` and `status=expired` are separate: an archived approval is still inspectable/retractable, while its overlay has ended. Recaps combine all currently approved exact story revisions through the requested clock.
- Local mode has no model calls. Cloud mode uses distinct Agent Framework role contexts: analyst, reviewer, editor and a final reviewer pass. The model can request bounded tools and alter an interpretation. Numeric/schema checks and final semantic review constrain generated audience text. Model review is fallible; a comparative advantage over one agent has not been established.
- All 100 combinations of language, detail and focus are generated before approval: 4 base variants × (general + 22 players + 2 teams). Viewers select stored variants; they never cause model work or acquire editorial permission.
- A viewer-safe snapshot and SSE stream expose approved content only. The protected producer projection adds candidate status and package hashes. Unapproved evidence and diagnostics require the producer key.
- SSE sends an authoritative `resync` snapshot on connection, including reconnect with a last cursor. No durable stream backlog is claimed. Subsequent state updates include full current publication state, so removal/replacement is authoritative. Compression is disabled for stream delivery and the companion reconciles with a snapshot every two seconds as a recovery path.
- Producers poll every 350 ms. Streams coalesce position updates at 250 ms. Each connection holds one snapshot, rather than an unbounded queue. Snapshot cursors combine audit/control sequence and replay time; reset uses a new session ID.
- Recaps are assembled fresh from currently approved revisions through the requested available time. Retraction/edit removes eligibility; the UI invalidates an open recap on story state/revision changes.
- SQLite state survives API restart. In-process locking serializes package creation and decisions; use one API worker. Cloud publication uses ETag-protected transactional Cosmos batches. One API replica remains enforced; distributed scaling is not certified.

## Interfaces and authorization

FastAPI's `/docs` exposes the executable API contract. Producer writes require `X-Producer-Token`. The local default is intentionally public demo access; shared deployment requires a private key or an Entra-authenticated producer identity. Viewer preferences are validated enums/roster IDs, not free-form model instructions.

Use `/studio/{sessionId}`, `/watch/{sessionId}` and `/overlay/{sessionId}`. Next.js proxies `/api/*` to the API host, keeping browser requests on one origin. The web server never includes the producer key in its bundle; the operator enters it and stores it per tab.

## Evidence boundary

`load_match` accepts an allowlist of runtime match IDs and validates metadata/observations. Evidence tools receive server-bound metadata, delivered observations and cutoff; there are no file-reading or arbitrary-query tools. Tool ranges are capped at 15 seconds and 180 observations, with explicit future/range/player errors. Evaluation labels, seeds and configuration names are absent from runtime responses.

Cloud images copy only runtime files, schemas and application code; it must not include `evals` or `data/evaluation-only`. The current developer checkout retains offline evaluation files for reproducibility. The deployed runtime excludes evaluation labels and provenance files. Model tools cannot read arbitrary files or future observations.

## Cloud delivery and failure behavior

The publisher sends only replay-clock-available observations, partitioned by session. The consumer validates immutable session identity and uses batches of up to 100, persisting before Blob checkpoint updates. Exact retransmissions are verified and deduplicated. Periodic durable-cache reconciliation makes rows written by another process visible during rollout. Load balancing is five seconds and ownership expiry twenty seconds; a restart can briefly delay ingestion. These values are demo settings, not a throughput certification.

Model generation runs in two background workers with at most four pending jobs. Polling does not repeat a completed workflow for the same evidence revision. A restart may recompute unfinished work, but durable packages and approvals persist. Changed evidence invalidates old approval before replacement review completes. Models cannot publish.

Jobs are keyed by session, story ID and evidence revision. Out-of-order completion cannot attach a package to another pass, and current evidence is rechecked before storage. New cloud model work is skipped once the original live display interval has expired; already reviewed approved moments remain in history. Completed in-process jobs are bounded to 512 retained entries. This is a bounded demo scheduler, not a production priority/ranking service.

Workflow, role and tool spans carry match/session/revision context and measured usage, excluding prompts, generated prose and credential headers. Cosmos retains the complete bounded review trace. Application Insights sampling is 10 percent; logs also have a workspace ingestion quota. No automated hard spending cap is claimed.
