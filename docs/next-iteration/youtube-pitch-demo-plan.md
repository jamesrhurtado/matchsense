# WHY/NOW — YouTube pitch demo implementation plan

Status: app-side pitch demonstration surfaces are implemented; OBS/YouTube setup and a real delivery rehearsal remain to be completed on the broadcast host.

## Implementation progress

- **Done in the app:** session-linked broadcast stage, transparent lower-third overlay, freshness guard, and producer-console links to stage, overlay, and companion.
- **Documented:** one-session setup and the OBS/YouTube pitch workflow in [`docs/youtube-pitch-demo.md`](../youtube-pitch-demo.md).
- **Still requires the broadcast host:** configure the two OBS browser sources, set the YouTube test broadcast destination/key in OBS, and verify the actual YouTube player. The stream key is entered locally and is never handled by the app.
- **Still requires OBS:** install and configure OBS Studio on the broadcast computer. It is not currently present in the computer's app inventory.
- **Phone companion:** the current local app address is only reachable on its host. A public HTTPS deployment is required before a phone can open the companion from another network.
- **Not implemented:** automatic or manual companion video-position synchronization. During the pitch, use linked exploration after the approved graphic appears and do not claim synchronized playback.

## Product outcome

Demonstrate one complete journey: a synthetic football event becomes an evidence-backed AI suggestion, a producer approves an exact revision, and the approved explanation appears over a real YouTube livestream. A companion lets fans explore the same approved facts in Spanish/casual and English/analyst modes.

YouTube is a delivery destination for one rehearsed pitch demonstration. The product remains the live explanation desk and companion. A reusable streaming-platform management product is outside this iteration.

## Architecture and AI decision

Synthetic feed → existing metrics and evidence → existing Story Director and Claim Reviewer → producer approval → viewer-safe publication → OBS browser source → YouTube Live.

The companion consumes approved publication data separately. Its language, detail and player/team preferences do not change the common video overlay.

Do not add an AI agent for OBS, YouTube, synchronization or publication. These actions must preserve the exact approved text, revision, timing and withdrawal state. Existing AI supplies editorial suggestions; the producer authorizes publication; deterministic code delivers it. No model calls should be triggered by opening OBS, reconnecting, changing preferences or changing broadcast presentation settings.

An optional future agent could rank supported stories for editorial attention. Consider it only after measuring a selection problem that existing logic cannot address. It is not a dependency or pitch requirement.

## Current implementation to reuse

- Existing studio, viewer and overlay routes, shared publication state and streaming updates.
- Exact-revision approval, source correction handling, retraction and approved recaps.
- Existing casual/analyst and English/Spanish variants.
- Existing synthetic live simulation and pressure/pass evidence.

The current overlay is a full dark page containing a card and operational messages. It needs adaptation for video composition. The current overlay text selects the English casual general variant; bilingual broadcast selection needs explicit implementation if included.

## Phase 1 — Lock the pitch passage

Choose one existing synthetic passage with a clear forward pass and supported before/after nearby-opponent comparison. Verify the precise numbers, timestamps, comparison intervals, coverage and eligibility window before scripting the narration. Do not assume that the historical 30 m example and the current live passage are interchangeable.

Use the same session for the producer, broadcast stage, overlay and companion. Add a small pitch-demo setup surface or documented launcher that provides their links and clearly identifies the selected fixture and AI mode. Keep the ordinary simulation available.

Preserve human approval and genuine continuous playback. If the candidate window is too short, adjust the pitch-specific scene timing or choose a longer suitable passage; do not silently revive expired content or preapprove it. Keep synthetic-data labeling visible.

Deliverable: one reproducible fixture/session configuration and a verified timing sheet.

## Phase 2 — Build the broadcast surfaces

Provide a clean broadcast-stage page with the synthetic pitch, score, clock and a small demo label, without producer controls or a duplicate explanation graphic.

Adapt the overlay page into a transparent video layer. Render only the approved, currently eligible explanation. Hide the graphic when empty, expired, withdrawn or disconnected; never put waiting messages, errors or reconnect banners into the broadcast output. Keep connection and eligibility diagnostics in the operator view. Add a documented freshness timeout so a frozen connection cannot leave stale copy on air indefinitely.

Use the existing editorial selection policy and exact approved wording. Start with one fixed broadcast language and detail level; bilingual personalization belongs in the companion for this demo. Use a short approved variant rather than generating a new summary at publication time.

Deliverable: separate stage and transparent overlay URLs suitable for a 1920 × 1080 OBS scene.

## Phase 3 — Compose OBS and deliver to YouTube

Create one OBS scene: broadcast stage underneath the transparent overlay. Ensure both sources use the same session and measure their alignment. Load a visible synthetic-demo label and an optional QR/link to the companion. Keep all producer tokens and stream credentials out of public URLs, logs and captured screens.

Configure one YouTube test broadcast manually. Use an unlisted stream where available and choose an appropriate latency setting. Verify account streaming readiness early. An unlisted link is shareable and must not be treated as access control.

No YouTube OAuth application, automatic stream creation, chat bot or stream-management dashboard is required. YouTube API integration is not necessary to send a composed video from OBS.

Deliverable: a verified livestream viewed through the actual YouTube player on a second device or browser. OBS preview alone does not complete this phase.

## Phase 4 — Bound companion synchronization

Video delivery and the companion have different delays. Do not claim automatic synchronization merely because they share a session clock.

For this pitch, implement or validate a manual alignment step using the match clock visible in the YouTube video. Bind the companion's presented timeline to that selected video moment, including the explanation and recap cutoff. A fixed offset is an initial approximation; rebuffering, pause or seeking requires realignment. Label this as manual synchronization.

Never expose future events simply because the backend has advanced. Apply current retraction/correction validity even when presenting an earlier approved moment; delayed presentation must not resurrect invalidated text. The existing live snapshot is not proof that historical presentation is supported: inspect the available history contract and add a bounded approved-history projection if necessary.

If safe delayed presentation cannot be completed within scope, demonstrate the companion's approved historical story explicitly after it appears on YouTube. Present it as linked exploration, without claiming a synchronized companion. This is the reduced-scope fallback, not an equivalent synchronization implementation.

Deliverable: a tested manually aligned companion, or a clearly disclosed linked-history experience.

## Phase 5 — Verify the complete journey

Add focused checks for new publication behavior and run relevant existing approval, retraction, correction, viewer and recap checks.

Acceptance criteria:

- Unapproved suggestions never enter the overlay or companion publication.
- The overlay shows the exact eligible revision and removes it after expiry, retraction, correction or freshness timeout.
- Reconnection restores authoritative state without resurrecting removed copy.
- Stage and graphic refer to the same synthetic passage/session and remain aligned in OBS.
- Both audience profiles preserve the approved numbers, scope and limitations; preferences do not change the common broadcast.
- If alignment is included, the companion does not reveal events beyond the selected video cutoff.
- The complete journey is observed in YouTube, not just local previews.

Record source availability, AI completion, approval, local graphic appearance and YouTube appearance as separate timings. Report measurements from rehearsals; do not invent accuracy, engagement or latency results. A withdrawal can disappear locally before its older video frames finish playing on YouTube. Document that delay rather than promising remote erasure of already transmitted frames.

Deliverable: a short verification record with observed timings, screenshots or recordings, AI/fallback identification and remaining limitations.

## Phase 6 — Record the pitch

Start the broadcast and establish healthy playback before recording the pitch. The submitted pitch is an edited screen recording of a real functioning stream, not a promise of a live connection during judging.

| Pitch time | Demonstration |
| --- | --- |
| 0:00–0:12 | YouTube player: synthetic football is already streaming. Introduce the need to understand the moment. |
| 0:12–0:38 | Producer console: the existing AI proposes an explanation; inspect its evidence while play continues. |
| 0:38–0:58 | Approve the exact revision and show its arrival in the YouTube player, allowing for measured delivery delay. |
| 0:58–1:25 | Companion: explore that approved story in Spanish/casual and English/analyst modes. |
| 1:25–1:43 | Catch-up: show an interval with actual approved history. |
| 1:43–1:55 | Close on the functioning product: producer control, real video delivery and individual exploration. |

Treat these as editing targets, not guaranteed event times. Rehearse against measured review and delivery delays. Disclose cuts or time jumps; never present edited timing as measured AI latency. If real AI fails or falls back, identify that state honestly and re-record a successful real-AI run when possible.

Keep retraction and network recovery as verified backup demonstrations rather than crowding the main pitch.

## Scope boundaries and completion

This iteration excludes native integration inside commercial OTT players, per-viewer customization burned into one shared stream, real Premier League footage/data, automatic video recognition, new predictive football models and broad production-scale certification.

The MVP is complete when a producer-reviewed AI explanation from a reproducible synthetic passage visibly reaches YouTube through OBS, the companion demonstrates two approved audience variants, relevant publication checks pass, and a truthful pitch recording under two minutes is ready.

Recommended implementation order: verify the passage and YouTube readiness → broadcast surfaces → OBS/YouTube smoke test → companion alignment or disclosed history fallback → publication checks → rehearsal and recording.
