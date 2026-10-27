# Audience Agent: read-only YouTube and rehearsal

The producer console can group recent live-chat questions and suggest an eligible
story. Questions are untrusted audience input, not match evidence. A producer
must explicitly associate the question with an exact current story revision and
review the existing evidence before any publication. Because the YouTube player
can lag behind the app clock, a family match is only a suggestion; it cannot
prove that chat refers to that moment. No chat message is posted by this feature.

For a real YouTube Live connection, enable YouTube Data API v3 and create a
Google OAuth Web application client. Set `YOUTUBE_CLIENT_ID` and
`YOUTUBE_CLIENT_SECRET` only in the API process environment. Register
`http://localhost:8000/api/youtube/oauth/callback` as an authorized redirect URI
for local use, or set `YOUTUBE_OAUTH_REDIRECT_URI` and register that exact URI
for another environment. Set `MATCHSENSE_WEB_ORIGIN` to the producer app origin
if it is not `http://127.0.0.1:3000`. The producer chooses **Authorize YouTube
Live**, grants the requested YouTube scope in Google, and then enters a live
video URL or ID. YouTube Live API methods require OAuth; an API key alone is not
sufficient for this chat integration. The app requests the `youtube.readonly`
scope, only reads chat, and never posts messages. Its OAuth access and refresh tokens remain in API-process memory and
are lost when that process restarts, so the producer reconnects after restart.
Use a single API process for this local flow. Google OAuth for a public app may
require consent-screen setup or verification depending on the client and users.

The integration uses YouTube `videos.list` and `liveChatMessages.list`; it
respects YouTube's returned polling interval and continuation token. A live
broadcast must have chat enabled, the authorizing account must have permission
to read it, and the stream must still be live. The API response reports
permission, ended-chat, missing-chat and rate-limit failures without exposing
provider credentials. `liveChatMessages.list` costs five quota units per call;
YouTube recommends `streamList` for lower-latency sustained polling to reduce
quota usage. Current console polling is bounded by YouTube's interval and only
runs while the producer panel is open and visible.

The explicit rehearsal input uses fictional local messages and makes no YouTube
calls. Session mode `template` groups exact normalized questions. Session mode
`ai` requests the Audience Agent using the configured Foundry provider; the
model can group semantically similar messages and suggest only an existing
candidate. Calls are bounded to 12 seconds and 50 recent messages. A failed or
unavailable model produces an explicitly labelled deterministic fallback.

Counts describe the sampled recent chat, not the entire audience. The intake
retains at most 150 messages from the most recent 90-second window at each
analysis; an AI analysis considers at most the last 50 of those. The response
includes `window_seconds`, `analyzed_at`, `available_message_count` and
`sample_limited`. Display names are not retained, channel identifiers are hashed
per session, and raw question text is stored in the protected session record.
Deployments should apply a retention policy appropriate to their intended use.

Groups and selected moments are producer-only. A suggested association is not
confirmed; the producer explicitly confirms an available exact revision and
hash. Corrections, expiration, a changed revision, and other eligibility changes
invalidate it. Group refresh uses a session revision check, avoiding silent
replacement of a concurrent producer action. Existing source correction and
publication checks remain authoritative. OBS preview and this API are not proof
that a question or explanation reached a YouTube player.
