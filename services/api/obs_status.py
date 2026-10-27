"""Read-only OBS status for an explicitly configured local broadcast host.

The endpoint never accepts an address or password from a request. OBS connects to
loopback only, with the password kept in the API process environment. This module
does not start, stop, or otherwise control streaming.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import uuid

from fastapi import APIRouter, Header
import websocket

TIMEOUT_SECONDS = 1.5
MAX_FRAME_BYTES = 65536


class ObsProtocolError(Exception):
    pass


class ObsAuthenticationRequired(Exception):
    pass


class ObsAuthenticationFailed(Exception):
    pass


def _authentication(password: str, salt: str, challenge: str) -> str:
    def sha64(value: str) -> str:
        return base64.b64encode(hashlib.sha256(value.encode("utf-8")).digest()).decode("ascii")
    return sha64(sha64(password + salt) + challenge)


def _receive(ws):
    raw = ws.recv()
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_FRAME_BYTES:
        raise ObsProtocolError()
    try:
        data = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ObsProtocolError() from exc
    if not isinstance(data, dict) or not isinstance(data.get("d"), dict):
        raise ObsProtocolError()
    return data


def _request(ws, kind: str) -> dict:
    request_id = uuid.uuid4().hex
    ws.send(json.dumps({"op": 6, "d": {"requestType": kind, "requestId": request_id}}))
    # Events and unrelated messages are never treated as a request response.
    for _ in range(30):
        message = _receive(ws)
        data = message["d"]
        if message.get("op") == 7 and data.get("requestId") == request_id:
            if data.get("requestStatus", {}).get("result") is not True:
                raise ObsProtocolError()
            result = data.get("responseData", {})
            if not isinstance(result, dict):
                raise ObsProtocolError()
            return result
    raise ObsProtocolError()


def read_obs_status(*, enabled: bool, port: int, password: str = "", connect=None) -> dict:
    """Fetch a bounded status snapshot; all returned fields are non-secret.

    The connection and responses are ephemeral and no credentials are logged.
    """
    if not enabled:
        return {"status": "disabled"}
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return {"status": "configuration_error"}
    ws = None
    identifying_with_auth = False
    try:
        connector = connect or websocket.create_connection
        ws = connector(f"ws://127.0.0.1:{port}", timeout=TIMEOUT_SECONDS,
                       http_no_proxy=["127.0.0.1"], suppress_origin=True)
        hello = _receive(ws)
        if hello.get("op") != 0 or hello["d"].get("rpcVersion") != 1:
            raise ObsProtocolError()
        identity = {"rpcVersion": 1, "eventSubscriptions": 0}
        auth = hello["d"].get("authentication")
        if auth is not None:
            if not password:
                raise ObsAuthenticationRequired()
            if not isinstance(auth, dict) or not isinstance(auth.get("salt"), str) or not isinstance(auth.get("challenge"), str):
                raise ObsProtocolError()
            identity["authentication"] = _authentication(password, auth["salt"], auth["challenge"])
            identifying_with_auth = True
        ws.send(json.dumps({"op": 1, "d": identity}))
        identified = _receive(ws)
        if identified.get("op") != 2:
            raise ObsAuthenticationFailed() if identifying_with_auth else ObsProtocolError()
        identifying_with_auth = False
        scene = _request(ws, "GetCurrentProgramScene")
        stream = _request(ws, "GetStreamStatus")
        stats = _request(ws, "GetStats")
        return {
            "status": "connected",
            "scene": scene.get("currentProgramSceneName") or scene.get("sceneName"),
            "stream_active": stream.get("outputActive"),
            "reconnecting": stream.get("outputReconnecting"),
            "stream_duration_ms": stream.get("outputDuration"),
            "output_congestion": stream.get("outputCongestion"),
            "skipped_frames": stream.get("outputSkippedFrames"),
            "total_frames": stream.get("outputTotalFrames"),
            "render_fps": stats.get("activeFps"),
            "cpu_percent": stats.get("cpuUsage"),
        }
    except ObsAuthenticationRequired:
        return {"status": "authentication_required"}
    except ObsAuthenticationFailed:
        return {"status": "authentication_failed_or_unavailable"}
    except (websocket.WebSocketConnectionClosedException, websocket.WebSocketTimeoutException,
            websocket.WebSocketException, TimeoutError, ConnectionError, OSError, socket.timeout):
        return {"status": "authentication_failed_or_unavailable" if identifying_with_auth else "unavailable"}
    except (ObsProtocolError, KeyError, TypeError, ValueError):
        return {"status": "authentication_failed_or_unavailable" if identifying_with_auth else "protocol_error"}
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def create_obs_router(require_producer):
    router = APIRouter()

    @router.get("/api/broadcast/obs-status")
    def obs_status(x_producer_token: str | None = Header(None)):
        require_producer(x_producer_token)
        # A cloud-hosted API's loopback is not the producer's broadcast host.
        if os.getenv("WHY_NOW_ENVIRONMENT") == "azure":
            return {"status": "unavailable_on_cloud"}
        try:
            port = int(os.getenv("MATCHSENSE_OBS_PORT", "4455"))
        except ValueError:
            return {"status": "configuration_error"}
        return read_obs_status(enabled=os.getenv("MATCHSENSE_OBS_ENABLED") == "1",
                               port=port, password=os.getenv("MATCHSENSE_OBS_PASSWORD", ""))

    return router
