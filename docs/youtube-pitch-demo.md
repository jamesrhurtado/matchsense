# YouTube pitch demo setup

WHY/NOW can provide a synthetic match stage and a transparent, producer-approved lower third as separate browser pages. OBS composes those pages into a video that can be sent to YouTube Live. The app does not create or start a YouTube broadcast automatically.

## Start the pitch session

For an offline end-to-end UI rehearsal, start the coverage-enabled synthetic demo:

```sh
make coverage-dev
```

Open `http://127.0.0.1:3000`, choose **Pressure Swing flagship · guided mixed-event pitch**, **Guided walkthrough**, and **Template preview · no AI calls**. This mode validates the presentation and approval flow, not AI quality. For a real AI run, use the existing `make live-dev` workflow and select **AI · Director and Reviewer**; it uses the configured Azure identity and may make model calls.

Start a new session. From the producer console, open **Broadcast stage** and **OBS overlay** in separate tabs. Add the session's companion at `/watch/{sessionId}`. Use the same session ID for all three pages. With the local server, OBS and a companion browser on this Mac can open these local pages; a phone or remote viewer cannot access `127.0.0.1`.

## Configure OBS

1. Add the broadcast-stage URL as a **Browser Source** and set its canvas to 1920 × 1080.
2. Add the overlay URL as a second **Browser Source**, also 1920 × 1080, above the stage.
3. Confirm the OBS Browser Source background is transparent. The overlay is intentionally blank until there is a current approved story.
4. Preview the combined scene. Start the feed and approve a live story in the producer console. Confirm the lower third appears and disappears when its approved live window ends or the producer retracts it.
5. In the YouTube Live Control Room, create a dedicated test broadcast. Prefer **Unlisted** while rehearsing. Copy its stream destination and key into OBS locally; never put the key in a URL, screenshot, source file or app configuration.
6. Start streaming from OBS and verify the actual YouTube player on a second browser or device. OBS preview confirms composition only; it does not confirm YouTube delivery.

The visible match clock is the reference for the companion. YouTube buffering can put the player behind the app. For this pitch, open the companion after the approved moment appears in YouTube and describe it as linked exploration. Do not imply the companion is synchronized to the viewer's video position or supports pause/seek alignment. To let an audience member open the companion on a phone, deploy this app version to a public HTTPS address first and update the on-screen companion address; a local `127.0.0.1` link only works on the host computer.

## Pitch sequence

1. Show the synthetic match already playing in the YouTube player.
2. In WHY/NOW, let the existing Director and Reviewer produce a suggestion. Inspect the evidence in the producer console.
3. Approve the exact revision; return to the actual YouTube player and show the lower third arriving.
4. Open the same session's companion and compare Spanish/casual with English/analyst. Explain that facts are shared while presentation preferences differ.
5. Show catch-up for approved moments, then close on the complete producer-to-viewer flow.

Edit the recording to stay below two minutes. If scenes are cut or elapsed time is compressed, disclose the edit and do not describe the edit timing as measured AI or streaming latency. Keep `SYNTHETIC MATCH DEMO` visible. Do not use Premier League footage, marks or real match data in the submission.

## What is and is not integrated

- The app has stage and overlay URLs for a single session; OBS composes them.
- YouTube delivery uses OBS's normal streaming output. No YouTube API client, automatic broadcast creation or automated stream-key handling is included.
- The companion is available for the same session, but it follows the app clock. The player may be delayed by YouTube buffering. Treat it as linked exploration unless manually aligned and separately verified.
- Producer approval, current eligibility, correction and withdrawal behavior are controlled by WHY/NOW. Already transmitted video frames cannot be recalled from viewers' buffers.
- The template rehearsal has no model calls. Identify whether a recording used template fallback or the actual AI Director and Reviewer.

## Prepare broadcast panel and companion QR

In the main producer session, choose **Prepare broadcast**. The panel provides
full URLs and copy/open actions for the stage, overlay and companion, all tied
to that session. Add the two OBS sources at 1920 × 1080. Its connection indicator
confirms the app feed only; it does not inspect OBS or confirm delivery to YouTube.
The execution note distinguishes a template rehearsal from an AI session, whose
actual calls/fallback must still be checked in the review trace.

A companion QR appears in the panel and on the broadcast stage when the app is
opened at a public HTTPS origin. During a local rehearsal it remains hidden;
localhost, private IP literals, local hostnames and insecure addresses are not
encoded. QR images are generated in the browser, without a third-party QR API.
The full companion link is also readable/clickable as an alternative to scanning.

If OBS runs locally while the same app/backend is publicly reachable, set the
server environment variable `MATCHSENSE_PUBLIC_URL` to that public origin, for
example `https://your-current-deployment.example.com`, and restart the frontend.
Supply only the origin, without credentials, a path, query or fragment. This is
an address configuration, not a deployment or connectivity check. Do not point
it at the older Azure build or a different backend: the exact session must be
available at that address. Open the generated link on the iPhone before recording.

For the main pitch: prepare sources → start the synthetic match → inspect one
real AI attempt → review evidence → approve → verify in the YouTube player →
explore the same session in Spanish/casual and English/analyst views. A phone can
verify YouTube delivery even while the companion is still local; public hosting
is needed before the phone can open the companion. No automatic video-position
synchronization or completed YouTube delivery is implied by these controls.
