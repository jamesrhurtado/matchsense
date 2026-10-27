import json
import base64
import hashlib
import socket
import struct
import threading

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from services.api.obs_status import _authentication, create_obs_router, read_obs_status


class FakeOBS:
    def __init__(self, authenticated=True, bad_auth=False):
        self.sent = []
        self.closed = False
        self.bad_auth = bad_auth
        self.messages = [{"op": 0, "d": {"rpcVersion": 1, **({"authentication": {"salt": "salt", "challenge": "challenge"}} if authenticated else {})}}]

    def send(self, value):
        message = json.loads(value)
        self.sent.append(message)
        if message["op"] == 1:
            self.messages.append({"op": 2 if not self.bad_auth else 0, "d": {}})
        elif message["op"] == 6:
            data = message["d"]
            values = {
                "GetCurrentProgramScene": {"currentProgramSceneName": "Match"},
                "GetStreamStatus": {"outputActive": True, "outputReconnecting": False, "outputSkippedFrames": 3, "outputTotalFrames": 1000, "outputDuration": 1234},
                "GetStats": {"activeFps": 59.9, "cpuUsage": 4},
            }
            self.messages.append({"op": 7, "d": {"requestId": data["requestId"], "requestStatus": {"result": True}, "responseData": values[data["requestType"]]}})

    def recv(self):
        return json.dumps(self.messages.pop(0))

    def close(self):
        self.closed = True


def test_local_obs_authentication_and_read_only_metrics():
    ws = FakeOBS()
    connections = []

    def connect(url, **kwargs):
        connections.append((url, kwargs))
        return ws

    status = read_obs_status(enabled=True, port=4455, password="private-password", connect=connect)
    assert connections[0][0] == "ws://127.0.0.1:4455"
    assert status == {"status": "connected", "scene": "Match", "stream_active": True,
                      "reconnecting": False, "stream_duration_ms": 1234,
                      "output_congestion": None, "skipped_frames": 3,
                      "total_frames": 1000, "render_fps": 59.9, "cpu_percent": 4}
    assert ws.sent[0]["d"]["authentication"] == _authentication("private-password", "salt", "challenge")
    assert [entry["d"]["requestType"] for entry in ws.sent[1:]] == [
        "GetCurrentProgramScene", "GetStreamStatus", "GetStats"]
    assert "private-password" not in json.dumps(status)
    assert ws.closed


def test_connection_states_and_no_password_leak():
    ws = FakeOBS()
    assert read_obs_status(enabled=True, port=4455, connect=lambda *a, **k: ws) == {"status": "authentication_required"}
    assert ws.closed
    ws = FakeOBS(bad_auth=True)
    assert read_obs_status(enabled=True, port=4455, password="bad", connect=lambda *a, **k: ws) == {"status": "authentication_failed_or_unavailable"}
    assert read_obs_status(enabled=False, port=4455) == {"status": "disabled"}
    assert read_obs_status(enabled=True, port=0) == {"status": "configuration_error"}


def test_producer_auth_and_cloud_loopback_are_enforced(monkeypatch):
    def require(token):
        if token != "producer":
            raise HTTPException(401)
    app = FastAPI()
    app.include_router(create_obs_router(require))
    client = TestClient(app)
    assert client.get("/api/broadcast/obs-status").status_code == 401
    monkeypatch.setenv("WHY_NOW_ENVIRONMENT", "azure")
    response = client.get("/api/broadcast/obs-status", headers={"X-Producer-Token": "producer"})
    assert response.json() == {"status": "unavailable_on_cloud"}


def test_status_over_real_loopback_websocket():
    """Exercise the wire protocol, including an authenticated OBS v5 handshake."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(10)
    port = listener.getsockname()[1]
    server_errors = []

    def obs_server():
        try:
            connection, _ = listener.accept()
            connection.settimeout(3)
            with connection:
                headers = b""
                while b"\r\n\r\n" not in headers:
                    headers += connection.recv(4096)
                key = next(line.split(b":", 1)[1].strip() for line in headers.split(b"\r\n")
                           if line.lower().startswith(b"sec-websocket-key:"))
                accept = base64.b64encode(hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
                connection.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + accept + b"\r\n\r\n")

                def receive(size):
                    data = b""
                    while len(data) < size:
                        chunk = connection.recv(size - len(data))
                        if not chunk:
                            raise ConnectionError()
                        data += chunk
                    return data

                def read_frame():
                    first, second = receive(2)
                    assert first == 0x81 and second & 0x80
                    size = second & 0x7f
                    if size == 126:
                        size = struct.unpack("!H", receive(2))[0]
                    mask = receive(4)
                    payload = receive(size)
                    return json.loads(bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

                def write_frame(message):
                    payload = json.dumps(message).encode()
                    header = bytes([0x81, len(payload)]) if len(payload) < 126 else bytes([0x81, 126]) + struct.pack("!H", len(payload))
                    connection.sendall(header + payload)

                write_frame({"op": 0, "d": {"rpcVersion": 1, "authentication": {"salt": "salt", "challenge": "challenge"}}})
                identify = read_frame()
                assert identify["d"]["authentication"] == _authentication("test-secret", "salt", "challenge")
                write_frame({"op": 2, "d": {"negotiatedRpcVersion": 1}})
                values = {"GetCurrentProgramScene": {"sceneName": "Match"},
                          "GetStreamStatus": {"outputActive": False, "outputSkippedFrames": 0, "outputTotalFrames": 0},
                          "GetStats": {"activeFps": 30.0}}
                for _ in range(3):
                    request = read_frame()
                    write_frame({"op": 7, "d": {"requestId": request["d"]["requestId"],
                                                 "requestStatus": {"result": True},
                                                 "responseData": values[request["d"]["requestType"]]}})
        except Exception as exc:
            server_errors.append(exc)

    thread = threading.Thread(target=obs_server, daemon=True)
    thread.start()
    try:
        status = read_obs_status(enabled=True, port=port, password="test-secret")
        assert status["status"] == "connected"
        assert status["scene"] == "Match"
        assert status["stream_active"] is False
        assert not server_errors
    finally:
        thread.join(timeout=5)
        listener.close()
