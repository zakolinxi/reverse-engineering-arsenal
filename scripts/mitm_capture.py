#!/usr/bin/env python3
"""mitmproxy addon: write structured HTTP/WebSocket evidence to JSONL.

Run with mitmdump (this file is an addon, not a standalone proxy):

  RE_CAPTURE_OUT=flows.jsonl mitmdump -q -p 8888 -s scripts/mitm_capture.py
  RE_CAPTURE_OUT=flows.jsonl RE_CAPTURE_HOSTS=api.example.com,example.org \
    mitmdump -q -p 8888 -s scripts/mitm_capture.py

Environment:
  RE_CAPTURE_OUT        output JSONL path (default rea_capture.jsonl)
  RE_CAPTURE_HOSTS      comma-separated host substrings; empty = all hosts
  RE_CAPTURE_BODIES     1 to include request/response bodies (default 1)
  RE_CAPTURE_MAX_BODY   max bytes per body (default 262144)
  RE_CAPTURE_REDACT     1 to mask Authorization/Cookie/Set-Cookie values (default 0)

HTTPS requires trusting the mitmproxy CA on the client. Only intercept traffic you
are authorized to inspect, and store the output somewhere access-controlled.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
import time
from pathlib import Path

CONFIG = {
    "out": Path(os.environ.get("RE_CAPTURE_OUT", "rea_capture.jsonl")),
    "hosts": [h.strip().lower() for h in os.environ.get("RE_CAPTURE_HOSTS", "").split(",") if h.strip()],
    "bodies": os.environ.get("RE_CAPTURE_BODIES", "1") not in ("0", "false", "False"),
    "max_body": int(os.environ.get("RE_CAPTURE_MAX_BODY", "262144")),
    "redact": os.environ.get("RE_CAPTURE_REDACT", "0") in ("1", "true", "True"),
}

SENSITIVE_HEADERS = {"authorization", "proxy-authorization", "cookie", "set-cookie"}


def host_allowed(host: str) -> bool:
    if not CONFIG["hosts"]:
        return True
    host = (host or "").lower()
    return any(item in host for item in CONFIG["hosts"])


def headers_of(message) -> dict:
    result = {}
    for key, value in message.headers.items(multi=True):
        name = key.lower()
        if CONFIG["redact"] and name in SENSITIVE_HEADERS:
            result[key] = "<redacted>"
        else:
            result[key] = value
    return result


def encode_bytes(raw: bytes) -> dict | None:
    if not CONFIG["bodies"] or not raw:
        return None
    truncated = len(raw) > CONFIG["max_body"]
    raw = raw[: CONFIG["max_body"]]
    try:
        text = raw.decode("utf-8")
        return {"encoding": "utf-8", "truncated": truncated, "text": text}
    except UnicodeDecodeError:
        return {"encoding": "base64", "truncated": truncated,
                "base64": base64.b64encode(raw).decode("ascii")}


def body_of(message) -> dict | None:
    try:
        return encode_bytes(message.raw_content or b"")
    except (ValueError, AttributeError):
        return None


def ws_body_of(message) -> dict | None:
    return encode_bytes(getattr(message, "content", b"") or b"")


class CaptureAddon:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.handle = None
        self.count = 0

    def load(self, loader) -> None:
        from mitmproxy import ctx
        CONFIG["out"].parent.mkdir(parents=True, exist_ok=True)
        self.handle = CONFIG["out"].open("a", encoding="utf-8")
        ctx.log.info(f"[rea] capture -> {CONFIG['out'].resolve()}")
        ctx.log.info(f"[rea] hosts={CONFIG['hosts'] or 'ALL'} bodies={CONFIG['bodies']} redact={CONFIG['redact']}")

    def done(self) -> None:
        with self.lock:
            if self.handle:
                self.handle.flush()
                self.handle.close()
                self.handle = None

    def write(self, event: str, payload: dict) -> None:
        if not self.handle:
            return
        payload = {"ts": round(time.time(), 3), "event": event, **payload}
        line = json.dumps(payload, ensure_ascii=False, default=str)
        with self.lock:
            self.handle.write(line + "\n")
            self.handle.flush()
            self.count += 1

    def http_connect(self, flow) -> None:
        host = flow.request.pretty_host
        if not host_allowed(host):
            return
        flow.metadata["rea_t0"] = time.time()
        self.write("connect", {
            "flow_id": flow.id,
            "host": host,
            "port": flow.request.port,
            "client": flow.client_conn.peername,
        })

    def request(self, flow) -> None:
        host = flow.request.pretty_host
        if not host_allowed(host):
            return
        flow.metadata["rea_t0"] = time.time()
        self.write("request", {
            "flow_id": flow.id,
            "method": flow.request.method,
            "scheme": flow.request.scheme,
            "host": host,
            "port": flow.request.port,
            "url": flow.request.pretty_url,
            "http_version": flow.request.http_version,
            "headers": headers_of(flow.request),
            "body": body_of(flow.request),
        })

    def response(self, flow) -> None:
        host = flow.request.pretty_host
        if not host_allowed(host):
            return
        started = flow.metadata.get("rea_t0")
        self.write("response", {
            "flow_id": flow.id,
            "url": flow.request.pretty_url,
            "status": flow.response.status_code,
            "reason": flow.response.reason,
            "http_version": flow.response.http_version,
            "elapsed_ms": round((time.time() - started) * 1000, 1) if started else None,
            "headers": headers_of(flow.response),
            "body": body_of(flow.response),
        })

    def websocket_start(self, flow) -> None:
        host = flow.request.pretty_host
        if not host_allowed(host):
            return
        self.write("ws_open", {
            "flow_id": flow.id,
            "url": flow.request.pretty_url,
            "headers": headers_of(flow.request),
        })

    def websocket_message(self, flow) -> None:
        if not host_allowed(flow.request.pretty_host):
            return
        message = flow.websocket.messages[-1]
        self.write("ws_message", {
            "flow_id": flow.id,
            "url": flow.request.pretty_url,
            "from_client": bool(message.from_client),
            "type": "text" if getattr(message, "is_text", False) else "binary",
            "content": ws_body_of(message),
        })

    def error(self, flow) -> None:
        self.write("error", {
            "flow_id": getattr(flow, "id", None),
            "url": getattr(flow.request, "pretty_url", None),
            "error": str(getattr(flow, "error", "")),
        })


addons = [CaptureAddon()]


if __name__ == "__main__" and "mitmdump" not in os.path.basename(sys.argv[0]).lower():
    print(__doc__)
