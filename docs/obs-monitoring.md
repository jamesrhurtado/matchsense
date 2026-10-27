# OBS monitoring on the broadcast computer

MatchSense can display a read-only OBS status beside its broadcast setup. This is
separate from both the MatchSense feed and YouTube delivery. OBS connection or
an active output does not prove that a viewer has received a particular frame.

1. Run OBS on the same computer as the MatchSense API. Enable the OBS WebSocket
   server in OBS and set its password there. The default OBS port is 4455.
2. Start the API with `MATCHSENSE_OBS_ENABLED=1`. If the port differs, set
   `MATCHSENSE_OBS_PORT` to the local port. Set `MATCHSENSE_OBS_PASSWORD` in the
   API process environment to the WebSocket password without putting it in the
   browser, a URL, a screenshot, a committed file, or command history. The app
   does not read `.env` files automatically.
3. Open **Prepare broadcast** in the producer console. The OBS panel refreshes
   periodically and offers a manual check. It shows the current OBS program
   scene, output status, skipped output frames and rendering FPS when reported.
4. Confirm the composed match and explanation in OBS and then in the actual
   YouTube player. An unlisted test stream is useful for a rehearsal.

The API accepts only `127.0.0.1`, never a hostname supplied by a caller; the
endpoint requires the producer token. A cloud-hosted API cannot reach OBS on
the producer's laptop and reports that monitoring is unavailable. No OBS
credentials or stream key are returned to the browser. When OBS is disabled,
offline, has an incompatible WebSocket protocol or needs authentication, the
panel says so. Authentication and connection failure can be indistinguishable
during the handshake, so the message reports both possibilities.

The WebSocket integration only requests status. It does not modify OBS scenes,
sources, or streaming output. A working OBS installation and WebSocket connection
on the broadcast host are required to verify this portion of the demonstration.
